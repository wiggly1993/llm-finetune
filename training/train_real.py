import glob, torch, pandas as pd
from datasets import Dataset
from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from trl import SFTTrainer, SFTConfig

MODEL = "/workspace/models/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/c03e6d358207e414f1eca0bb1891e29f1db0e242"
OUT = "/workspace/checkpoints/run2"
SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL, max_seq_length=2048,
    dtype=torch.float16, load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=16, lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth", random_state=42,
)

def build(path, n=None):
    df = pd.read_parquet(path)
    if n:
        df = df.head(n)
    #col = "message" if "message" in df.columns else "subject"
    col = "model_input"
    texts = [
        tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": m},
             {"role": "assistant", "content": d}],
            tokenize=False)
        for m, d in zip(df[col], df["diff"])
    ]
    return Dataset.from_dict({"text": texts})

train_ds = build("/workspace/data/train.parquet")
val_ds = build("/workspace/data/val.parquet", n=500)

trainer = SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=train_ds, eval_dataset=val_ds,
    args=SFTConfig(
        output_dir=OUT,
        per_device_train_batch_size=8,
        gradient_accumulation_steps=4,   # effective batch 32
        per_device_eval_batch_size=8,
        num_train_epochs=1,
        learning_rate=2e-4,
        warmup_steps=100,
        lr_scheduler_type="cosine",
        fp16=True, bf16=False,
        optim="adamw_8bit",
        max_grad_norm=1.0,
        logging_steps=10,
        eval_strategy="steps", eval_steps=500,
        save_strategy="steps", save_steps=500, save_total_limit=3,
        report_to="none",
        dataset_text_field="text",
        dataset_num_proc=1,
        seed=42,
    ),
)
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)

resume = len(glob.glob(f"{OUT}/checkpoint-*")) > 0
trainer.train(resume_from_checkpoint=resume)
model.save_pretrained(f"{OUT}/lora_final")
tokenizer.save_pretrained(f"{OUT}/lora_final")
print("DONE")