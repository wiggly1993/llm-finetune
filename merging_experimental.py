from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only

import glob, torch, pandas as pd
from datasets import Dataset
from trl import SFTTrainer, SFTConfig

MODEL = "/workspace/models/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/c03e6d358207e414f1eca0bb1891e29f1db0e242"
LORA_MODEL_PATH = "/workspace/checkpoints/run2/lora_final"

OUT = "/workspace/merged/run2"
SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=LORA_MODEL_PATH, 
    max_seq_length=2048,
    dtype=torch.float16, 
    load_in_4bit=False,  # not sure: Set to False for a completely lossless 16-bit merge
)

# 3. Save the permanently fused model
# This dequantizes and merges weights seamlessly.
model.save_pretrained_merged(
    OUT, 
    tokenizer, 
    save_method="merged_16bit"
)