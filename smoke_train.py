import torch
import pandas as pd
from datasets import Dataset
from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from trl import SFTTrainer, SFTConfig

MODEL = "/workspace/models/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/c03e6d358207e414f1eca0bb1891e29f1db0e242"
SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL,
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

# 10 rows, batch 2 -> 5 steps/epoch
df = pd.read_parquet("/workspace/data/train.parquet").head(10)
col = "message" if "message" in df.columns else "subject"
texts = [
    tokenizer.apply_chat_template(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": r[col]},
            {"role": "assistant", "content": r["diff"]},
        ],
        tokenize=False,
    )
    for _, r in df.iterrows()
]
ds = Dataset.from_dict({"text": texts})
print(texts[0][:600])  # eyeball the template

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=ds,
    args=SFTConfig(
        output_dir="/workspace/checkpoints/smoke",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=1,
        num_train_epochs=2,
        learning_rate=2e-4,
        fp16=True,
        bf16=False,
        optim="adamw_8bit",
        max_grad_norm=1.0,
        logging_steps=1,
        save_strategy="epoch",
        report_to="none",
        dataset_text_field="text",
        dataset_num_proc=1,
        seed=42,
    ),
)

# loss only on assistant tokens
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)


ex = trainer.train_dataset[0]
print("UNMASKED:", tokenizer.decode([t for t in ex["labels"] if t != -100]))
raise SystemExit

trainer.train()
print("peak VRAM GB:", torch.cuda.max_memory_allocated() / 1e9)
model.save_pretrained("/workspace/checkpoints/smoke/lora_final")
print("DONE")