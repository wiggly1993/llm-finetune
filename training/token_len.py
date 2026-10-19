from transformers import AutoTokenizer
from datasets import load_dataset
from pathlib import Path

tok = AutoTokenizer.from_pretrained("/workspace/models/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/c03e6d358207e414f1eca0bb1891e29f1db0e242")

if __name__ == "__main__":
    base = Path(__file__).parent.parent
    ds = load_dataset("json", data_files=str(base / "data" / "train.jsonl"), split="train")

    lengths = []
    for row in ds:
        text = tok.apply_chat_template(row["messages"], tokenize=False)
        lengths.append(len(tok(text)["input_ids"]))

    lengths.sort()
    n = len(lengths)
    print("rows:", n)
    print("min:", lengths[0])
    print("mean:", sum(lengths) // n)
    print("p50:", lengths[n // 2])
    print("p99:", lengths[int(n * 0.99)])
    print("max:", lengths[-1])
    print("over 2048:", sum(l > 2048 for l in lengths))
    print("over 3072:", sum(l > 3072 for l in lengths))
    print("over 4096:", sum(l > 4096 for l in lengths))