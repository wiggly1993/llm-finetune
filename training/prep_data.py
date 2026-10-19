from datasets import load_dataset
from pathlib import Path




if __name__ == "__main__":
    base = Path(__file__).parent.parent
    path_to_train_data = base / "datagen" / "out" / "combined.jsonl"
    # turn path into str text for load_dataset
    path_to_train_data = str(path_to_train_data)
    #print(path_to_train_data)

    ds = load_dataset("json", data_files=path_to_train_data, split="train")
    # print(ds)

    split_ds = ds.train_test_split(test_size=0.15, shuffle=True, seed=42)
    train_set, test_set = split_ds["train"], split_ds["test"]

    path_to_store_data = str(base / "data")
    print(path_to_store_data)
    Path(path_to_store_data).mkdir(parents=True, exist_ok=True)

    train_set.to_json(path_to_store_data + "/train.jsonl")
    test_set.to_json(path_to_store_data + "/val.jsonl")