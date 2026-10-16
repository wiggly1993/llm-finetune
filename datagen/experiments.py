from validate import tests_validation, plan_validation 
from apply_check import diff_applies
from aider.coders.udiff_coder import find_diffs, normalize_hunk, do_replace
from pathlib import Path
from split_reply import split_reply

from task_filter import task_is_good
from validate import build_diff, split_reply



if __name__ == "__main__":
    # starting_point = Path(__file__).parent

    # full_path_ds_reponse = starting_point / "raw" / "javascript" /"javascript_31.txt"
    # with open(full_path_ds_reponse, encoding="utf-8") as f:
    #     raw_ds_output = f.read()
    #     d = split_reply(text=raw_ds_output)

    # print(d["solution"])

    # def washer(text_to_wash):
    #     lines = text_to_wash.splitlines()
    #     new_text = ""
    #     for line in lines:
    #         new_text += line.rstrip() + "\n"

    #     return new_text


    # d["stub"] = washer(d["stub"])
    # d["solution"] = washer(d["solution"])

    # #diff = build_diff(d["stub"], d["solution"], d["filename"])
    # value, info_text = task_is_good(d)

    #print(repr(diff))

    import json, re, sys

    path = sys.argv[1]
    total = 0
    bad = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            answer = rec["messages"][-1]["content"]
            plan = answer.split("```diff")[0]
            total += 1
            if re.search(r"\btest", plan.lower()):
                bad += 1
    print(path, "plans with 'test':", bad, "of", total)