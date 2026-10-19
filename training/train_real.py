from unsloth import FastLanguageModel
import glob, torch
from pathlib import Path
from datasets import load_dataset
from transformers import DataCollatorForSeq2Seq
from trl import SFTTrainer, SFTConfig

MODEL = "/workspace/models/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/c03e6d358207e414f1eca0bb1891e29f1db0e242"
OUT = "/workspace/checkpoints/run3"
MAX_LEN = 8192
DATA = Path(__file__).parent.parent / "data"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL, max_seq_length=MAX_LEN,
    dtype=torch.bfloat16, load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=16, lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth", random_state=42,
)

def tokenize_row(row):
    msgs = row["messages"]
    prompt_msgs, answer = msgs[:-1], msgs[-1]["content"]
    assert msgs[-1]["role"] == "assistant"
    prompt_text = tokenizer.apply_chat_template(
        prompt_msgs, tokenize=False, add_generation_prompt=True)
    prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
    answer_ids = tokenizer(answer + "<|im_end|>", add_special_tokens=False)["input_ids"]
    return {
        "input_ids": prompt_ids + answer_ids,
        "attention_mask": [1] * (len(prompt_ids) + len(answer_ids)),
        "labels": [-100] * len(prompt_ids) + answer_ids,
    }

def build(path):
    ds = load_dataset("json", data_files=str(path), split="train")
    ds = ds.map(tokenize_row, remove_columns=ds.column_names)
    return ds.filter(lambda r: len(r["input_ids"]) <= MAX_LEN)

train_ds = build(DATA / "train.jsonl")
val_ds = build(DATA / "val.jsonl")
print("train rows:", len(train_ds), "val rows:", len(val_ds))

# ---- masking check (milestone 6) ----
ex = train_ds[0]
trained = [t for t, l in zip(ex["input_ids"], ex["labels"]) if l != -100]
print("tokens total:", len(ex["input_ids"]), "| tokens with loss:", len(trained))
print("--- TRAINED TEXT START ---")
print(tokenizer.decode(trained[:60]))
print("--- TRAINED TEXT END ---")
print(tokenizer.decode(trained[-40:]))
print("--------------------------")

trainer = SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=train_ds, eval_dataset=val_ds,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True, label_pad_token_id=-100),
    args=SFTConfig(
        output_dir=OUT,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        per_device_eval_batch_size=1,
        num_train_epochs=3,
        learning_rate=2e-4,
        warmup_steps=20,
        lr_scheduler_type="cosine",
        fp16=False, bf16=True,
        optim="adamw_8bit",
        max_grad_norm=1.0,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch", save_total_limit=5,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        remove_unused_columns=False,
        dataset_kwargs={"skip_prepare_dataset": True},
        seed=42,
    ),
)

resume = len(glob.glob(f"{OUT}/checkpoint-*")) > 0
trainer.train(resume_from_checkpoint=resume)
model.save_pretrained(f"{OUT}/lora_final")
tokenizer.save_pretrained(f"{OUT}/lora_final")
print("DONE")