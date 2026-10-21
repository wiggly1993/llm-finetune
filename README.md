# llm-finetune

Fine-tuning **Qwen2.5-Coder-7B-Instruct** (QLoRA, Unsloth) to beat its own baseline on the **Aider Polyglot** benchmark (225 exercises: Python, JavaScript, C++, Rust, Go, Java), using the `udiff` edit format.

**Outcome: negative result.** Three training runs, none beat the base model. Format compliance improved a lot (49% to 75% well-formed diffs), but the pass rate did not move. The project was stopped at the budget limit. The pipeline, the harness fixes and the lessons are documented below.

Budget: $100 total. Hardware: rented Vast.ai GPUs (RTX 2080 Ti for runs 1-2, RTX 3090 for run 3, and again for the final benchmark).

---

## TL;DR results

All scores are `pass_rate_2` on the full 225-case benchmark, one run each (single runs are noisy, roughly +/- 0.5 points).

| Model | Edit format | Pass rate 2 | Passed | Well-formed |
|---|---|---|---|---|
| Base | udiff | 2.7% | 6/225 | n/a |
| Base (re-run, final harness) | udiff | **2.2%** | 5/225 | 48.9% |
| run1 (commit message to diff) | udiff | 1.8% | 4/225 | n/a |
| run2 (commit message + old file to diff) | udiff | 0.4% | 1/225 | n/a |
| run3 (synthetic, merged) | udiff | **1.8%** | 4/225 | **75.1%** |

Success rule set before training: average of several runs, at least 3 points over base. Not met.

---

## Repo layout

```
llm-finetune/
  datagen/     synthetic data generation + validation (DeepSeek V3)
  data/        final run3 data: train.jsonl (2360 rows), val.jsonl (417 rows)
  training/    QLoRA training, merging, data prep scripts
  results/     aider benchmark stats for base and run3 (merged)
  log.txt      working log
```

Not in the repo (too large): base model, adapters, merged weights. Adapters live on HuggingFace under `wiggly1993/qwen7b-lora-adapters` (`run1/`, `run3/`).

---

## 1. Data

### Run 1 and 2: commit data (failed)

Source: `bigcode/commitpackft`, cleaned and filtered to the six benchmark languages, ~112k training rows.

- Cleaning: removed whitespace-only and comment-only diffs, converted diffs to Aider's udiff format (`@@ ... @@` without line numbers, wrapped in a ```` ```diff ```` fence).
- run1 input: commit message. run2 input: commit message + file name + old file contents. Target: the diff.
- Why it failed: commit data teaches *small edits to existing files*. Aider Polyglot asks for *an empty stub turned into a full solution*. Wrong skill.

### Run 3: synthetic, benchmark-shaped data

Idea: have a strong model write new Exercism-style exercises, keep only the ones that provably work, and wrap them in Aider's exact turn-1 message layout.

**Pipeline**

#### 1) Generation

1. **Generate.** DeepSeek V3 is called once per task with a seed (language, topic, difficulty) so tasks do not all look alike. Each reply contains five delimited sections: `===INSTRUCTIONS===`, `===STUB===`, `===SOLUTION===`, `===TESTS===`, `===PLAN===`. DeepSeek never writes the diff. It is told not to copy existing Exercism exercises and to use the standard library only.
2. **Split** the reply by the delimiters.

#### 2) Testing

3. **Validate by execution.** Solution + tests are written to a temp folder and run. **Only passing samples are kept. The check was never loosened.**
4. **Stub must fail.** The same tests are run against the stub. If the stub passes, the task is trivial and is dropped.
5. **Plan check.** The short plan is rejected if it contains a code fence or is too long (max ~120 words, plain text).

#### 3) Final preparations

6. **Build the diff ourselves.** A local script produces the udiff from stub to solution (full block replacement, `@@ ... @@`, no context lines). No AI is involved here, which guarantees the format.
7. **Wrap in Aider's real turn-1 layout:** fixed system prompt with udiff rules, the fixed sympy example chat, the file stub in a code fence, the instructions, and the fixed "use the above instructions to modify the supplied files" tail. Tests are never shown to the model.
8. **Training target** (the only part with loss): `Ok, I will:` + a short numbered plan + the ```` ```diff ```` block.

**Output:** 2777 validated samples, split 2360 train / 417 val. Cost for the DeepSeek calls: roughly $20.

**Scripts in `datagen/`**

| Script | Role |
|---|---|
| `hi_deepseek.py` | DeepSeek API connectivity test [confirm] |
| `prompt_builder.py` | builds the generation prompt (seed + format example) [confirm] |
| `prompt_loop.py` | loops generation over seeds / languages [confirm] |
| `split_reply.py` | splits the model reply into the five sections |
| `section_stripping.py` | cleans section contents (fences, whitespace) [confirm] |
| `task_filter.py` | filters bad / duplicate tasks before validation [confirm] |
| `validate.py` | runs solution vs tests, stub vs tests, keeps passes only |
| `validity_loop.py` | runs validation over all generated tasks [confirm] |
| `parse_template.py` | parses Aider's message template for the wrapper [confirm] |
| `apply_check.py` | checks that the built diff applies cleanly to the stub (Aider's parser) [confirm] |
| `experiments.py` | scratch experiments |

`catch2_local/` and `junit_local/` hold local C++ / Java test dependencies (git-ignored). `raw/`, `work/`, `out/` are git-ignored intermediates (lost with the instance, not needed).

**Known limits of the data**

- Turn 1 only. Turn 2 (retry after test errors) is not trained.
- Contamination check against the Polyglot test set was skipped (deliberate decision).
- Whether short reasoning helps a 7B model is untested here (hypothesis taken from PewDiePie's video).

---

## 2. Training

All runs: Unsloth + TRL `SFTTrainer`, QLoRA (4-bit base, LoRA adapters), loss only on the assistant answer.

| | run1 | run2 | run3 |
|---|---|---|---|
| Data | commitpackft | commitpackft + old file | synthetic (2360 rows) |
| GPU | RTX 2080 Ti | RTX 2080 Ti | RTX 3090 |
| Precision | fp16 | fp16 | bf16 |
| Max seq length | 2048 | 2048 | 8192 |
| Epochs | 1 | 1 | 3 |
| Batch | 8 x 4 accum = 32 | 8 x 4 accum = 32 | 1 x 16 accum = 16 |
| Steps | 3512 | n/a | 444 |
| Time | ~14 h | n/a | 4 h 41 min |
| Train loss | 1.2 to ~0.8 | 0.34 | avg 0.2132 |
| Eval loss | 0.819 to 0.814 | n/a | 0.271 / 0.2631 / 0.2746 |

**run3 settings** (`training/`): LoRA r=16, alpha=16, dropout 0, all attention + MLP projections (`q,k,v,o,gate,up,down`), Unsloth gradient checkpointing, lr 2e-4, cosine schedule, 20 warmup steps, `adamw_8bit`, `max_grad_norm=1.0`, seed 42. Eval and checkpoint every epoch, `load_best_model_at_end=True` on `eval_loss`.

**Custom loss masking:** the prompt is tokenized with the Qwen chat template and the generation prompt; labels are `-100` for every prompt token, so only the final assistant answer (plan + diff + `<|im_end|>`) is trained on. A masking check at start-up prints the first and last trained tokens.

**Result of the epochs:** eval loss was best after epoch 2 (0.2631) and rose slightly in epoch 3 (mild overfit). The saved adapter is the epoch-2 checkpoint (`checkpoint-296`, identical hash to `lora_final`).

**Merge:** `peft` `merge_and_unload()` in bf16, saved as one ~15 GB safetensors file. (run1 was merged with Unsloth's `save_pretrained_merged`.)

---

## 3. Evaluation setup

- Aider benchmark harness from `Aider-AI/aider` with `Aider-AI/polyglot-benchmark` (not `clone-exercism.sh`), no Docker (`AIDER_DOCKER=1`).
- Model served with vLLM 0.26.0 (OpenAI-compatible API), `--max-model-len 16384`, `max_new_tokens 2048`.
- Command: `benchmark.py RUN --edit-format udiff --threads 1 --keywords python,javascript,cpp,rust,go,java`
- Every run checked before trusting it: 225 result files, **0 exceptions**, all six languages present.

**Harness traps that produce fake scores** (all hit and fixed):

- Missing `go`, `cargo`, `java` makes those languages fail silently as fake 0%.
- JS needs `/npm-install` (normally built by Aider's Docker image) and a `/aider` symlink, otherwise `npm-test.sh` is not found.
- `--keywords java` also matches `javascript`. Use `java/exercises` for single-language checks.
- Recursive glob `**` over the run directory loops through the `node_modules` symlink and hangs.
- Too small a context cap (6144) produced fake `exhausted_context_windows`.
- Hangs (litellm timeout) are resumed with `--cont` and the same run name.

---

## 4. Results in detail

Final comparison, same harness, same server settings, udiff, 225 cases, 0 exceptions:

| Metric | Base | run3 (merged) |
|---|---|---|
| pass_rate_1 | 1.8% (4) | 1.8% (4) |
| pass_rate_2 | 2.2% (5) | 1.8% (4) |
| well-formed cases | 48.9% | 75.1% |
| malformed responses | 449 | 292 |
| cases with malformed responses | 115 | 56 |
| exhausted context windows | 27 | 53 |

Base `whole` per language (earlier run): cpp 0/26, go 1/39, java 1/47, js 3/49, python 0/34, rust 0/30.

**Reading the result**

- Synthetic data fixed the *format*: well-formed diffs rose from 49% to 75%.
- It did not fix the *solving*: passed exercises stayed at 4-5 of 225. The difference between 5 and 4 is one case, i.e. noise.
- Exhausted context windows doubled, so run3 may loop or ramble more in retries (turn 2 was never trained).
- Same pattern as in PewDiePie's 32B project: a format fix alone gives no gain.

---

## 5. Lessons

1. **Data content is the lever, not format.** Commit data taught the wrong skill; synthetic benchmark-shaped data taught the format but not enough skill at 3k samples.
2. **Base capability matters.** The 7B base solves ~2% of the benchmark. A few thousand samples are unlikely to lift a model that starts that low. PewDiePie started from a 32B model near 16%.
3. **Validate the harness before trusting any score.** Several setups produced fake 0%.
4. **Never loosen validation** to get more samples through.
5. **Average several runs.** This project ran each configuration once because of budget, so differences below ~1 point are not meaningful.
6. **Synthetic data is not cheap at scale.** ~$20 for ~2.8k validated samples makes 15k samples roughly $80+, which exceeded the budget.

## 6. What would come next (not done)

- Scale the validated synthetic set (~15k) and add a final small round of top-quality samples.
- Train turn 2 (retry after test errors).
- Contamination check against Polyglot.
- Try a larger base (14B) if it fits the budget.
- Several benchmark runs per model, averaged.

---

## Reproduce (outline)

1. Rent a GPU with 100 GB+ disk. Install the language tools: `apt install golang-go cargo openjdk-17-jdk`.
2. Use separate virtual environments for Unsloth, vLLM and Aider. Installing vLLM or Aider into the Unsloth environment can break torch.
3. Download the whole base repo: `hf download Qwen/Qwen2.5-Coder-7B-Instruct --cache-dir /workspace/models`.
4. Train with the run3 script in `training/` on `data/train.jsonl` and `data/val.jsonl`.
5. Serve with vLLM (adapter via `--enable-lora`, or merged weights) and run the benchmark with the command above.
6. Check for 0 exceptions and 225 results before reading any score.
