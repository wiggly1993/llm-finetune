from aider.coders.udiff_coder import find_diffs, normalize_hunk, do_replace
from pathlib import Path
import sys
import subprocess

from validate import build_diff, split_reply

def diff_applies(d):
    diff = build_diff(stub=d["stub"], solution=d["solution"], filename=d["filename"])

    aider_list = find_diffs(diff)

    file_path = aider_list[0][0]
    hunk = aider_list[0][1]

    hunk = normalize_hunk(hunk)

    new_text = do_replace(Path(file_path), d["stub"] + "\n", hunk)

    if new_text == d["solution"] + "\n":
            return True
    else:
            return  False





if __name__ == "__main__":
    starting_point = Path(__file__).parent

    full_path_ds_reponse = starting_point / "raw" / "test_42.txt"
    with open(full_path_ds_reponse, encoding="utf-8") as f:
        raw_ds_output = f.read()
        d = split_reply(text=raw_ds_output)

    def washer(text_to_wash):
        lines = text_to_wash.splitlines()
        new_text = ""
        for line in lines:
            new_text += line.rstrip() + "\n"

        return new_text


    d["stub"] = washer(d["stub"])
    d["solution"] = washer(d["solution"])

    task_is_good(d)


    






        #print(new_text)

