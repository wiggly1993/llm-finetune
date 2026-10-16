from validate import tests_validation, plan_validation 
from apply_check import diff_applies
from aider.coders.udiff_coder import find_diffs, normalize_hunk, do_replace
from pathlib import Path
from split_reply import split_reply



def task_is_good(d):
    # first diff applies
    if not diff_applies(d=d):
        return False, "diff applies did not work"
     
    if not plan_validation(d=d):
        return False, "Plan is too long"

    value, info_text = tests_validation(d=d)
    if value:
        return True, ""
    else:
        return False, info_text




if __name__ == "__main__":
    starting_point = Path(__file__).parent

    full_path_ds_reponse = starting_point / "raw" / "test_1.txt"
    with open(full_path_ds_reponse, encoding="utf-8") as f:
        raw_ds_output = f.read()
        d = split_reply(text=raw_ds_output)


    print(task_is_good(d))
