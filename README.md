# llm-finetune

Fine-tuning Qwen2.5-Coder-7B-Instruct (QLoRA, Unsloth) for the Aider Polyglot benchmark.

## Scripts
- `train_real.py`: main QLoRA training run
- `smoke_train.py`: 10-row smoke test
- `merging_experimental.py`: merge LoRA adapter into base model
- `check_len.py`: token length check

## Status
- run1 (commit msg -> diff): 1.8%
- run2 (commit msg + file -> diff): 0.4%
- base model: 2.2% (whole), 2.7% (udiff)
- Commit data hurt. Next: synthetic stub -> solution data, validated by tests.

## Not in repo
Data, models, adapters. They live on HuggingFace (wiggly1993).
