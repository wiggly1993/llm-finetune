import pandas as pd, numpy as np
from transformers import AutoTokenizer

MODEL = "/workspace/models/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/c03e6d358207e414f1eca0bb1891e29f1db0e242"
SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
tok = AutoTokenizer.from_pretrained(MODEL)

df = pd.read_parquet("/workspace/data/train.parquet")
col = "message" if "message" in df.columns else "subject"
texts = [
    tok.apply_chat_template(
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": m},
         {"role": "assistant", "content": d}],
        tokenize=False)
    for m, d in zip(df[col], df["diff"])
]
lens = np.array([len(x) for x in tok(texts)["input_ids"]])
print("rows:", len(lens))
print("mean:", lens.mean(), "max:", lens.max())
for p in (50, 90, 99, 99.9):
    print(f"p{p}:", np.percentile(lens, p))
for n in (1024, 2048, 4096):
    print(f">{n}: {(lens > n).mean() * 100:.2f}%")