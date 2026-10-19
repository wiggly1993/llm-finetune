from validate import build_diff
from split_reply import split_reply
from parse_template import fill_messages, parse_template
from task_filter import task_is_good
import signal

from pathlib import Path
import json

def build_answer(plan, diff):
    text = ("Ok, I will:\n\n"+plan.strip()  
    +"\n\nHere are the diffs for those changes:\n\n"+diff.strip())  
    return text


def washer(text_to_wash):
    lines = text_to_wash.splitlines()
    new_text = ""
    for line in lines:
        new_text += line.rstrip() + "\n"

    return new_text


def build_record(base_dict_list, deepseek_parts):
    # 1) TARGET CREATION: create the diff based on ds parts for the desired target
    diff = build_diff(stub=deepseek_parts["stub"], solution=deepseek_parts["solution"], filename=deepseek_parts["filename"])

    # combine the diff with some str text and the "reasoning part" 
    full_target_text = build_answer(plan=deepseek_parts["plan"], diff=diff)
    #print(full_target_text)

    # 2) INPUT CREATION: fill_message() takes the base dict list AND the unique ds chopped parts
    # returns a LIST of dictionaries that now have the full fake convo AND the unique parts inserted
    filled_d = fill_messages(base_dict_list, deepseek_parts["filename"], 
                              deepseek_parts["stub"], deepseek_parts["instructions"])


    # Now lets combine them
    filled_d.append({"role": "assistant", "content": full_target_text})

    # bc we like to suffer we store now this list of dictionaries into yet another dictionary. 
    # probably because this is convention before training to have everything in one dict like that
    record = {"messages": filled_d}

    return record


class TaskTimeout(Exception):
    pass

def _on_timeout(signum, frame):
    raise TaskTimeout()

signal.signal(signal.SIGALRM, _on_timeout)
TIMEOUT_SEC = 120  # max seconds per task

if __name__ == "__main__":
    langs = ["cpp", "go", "java", "javascript", "python", "rust"]
    base_dict_list = parse_template()

    kept, skipped = 0, 0

    starting_point = Path(__file__).parent
    counter_path = starting_point / "score.json"
    counter_dict = {}

    def count(lang, reason):
        counter_dict.setdefault(lang, {})
        counter_dict[lang][reason] = counter_dict[lang].get(reason, 0) + 1
        json.dump(counter_dict, open(counter_path, "w"))

    for lang in langs:
        full_out_path = starting_point / "out" / f"{lang}_pilot.jsonl"
        with open(full_out_path, "w") as out:

            for p in sorted(Path(starting_point / "raw" / lang).glob("*.txt")):
                print(f"processing: {p}")
                with open(p) as f:
                    raw_ds_output = f.read()

                signal.alarm(TIMEOUT_SEC)  # start the clock
                try:
                    deepseek_parts = split_reply(text=raw_ds_output)

                    deepseek_parts["stub"] = washer(deepseek_parts["stub"])
                    deepseek_parts["solution"] = washer(deepseek_parts["solution"])

                    value, info_text = task_is_good(deepseek_parts, lang)
                    if not value:
                        print(f"{p} file was fucked up. {info_text}")
                        skipped += 1
                        count(lang, info_text)
                        continue

                    record = build_record(base_dict_list, deepseek_parts)
                    out.write(json.dumps(record) + "\n")
                    kept += 1

                except TaskTimeout:
                    print(f"{p.name} TIMEOUT")
                    skipped += 1
                    count(lang, "timeout error")

                except Exception as e:
                    print(p.name, e)
                    skipped += 1
                    count(lang, "exception")

                finally:
                    signal.alarm(0)  # stop the clock


    

    

# # load a deepseek reply
# starting_point = Path(__file__).parent
# full_raw_path = starting_point / "raw" / "test_1.txt"
# with open(full_raw_path) as f:
#     raw_ds_output = f.read()

# # dictionary with unique ds replies chopped into indiv. entries
# deepseek_parts = split_reply(text=raw_ds_output)

# # run the core file that creates the record ({"messages": filled_d}) we need for training 
# record = build_record(base_dict_list, deepseek_parts)

# starting_point = Path(__file__).parent
# full_out_path = starting_point / "out" / "toy.jsonl"

# # store it all into a .json file
# with open(full_out_path, "a") as f:
#     f.write(json.dumps(record) + "\n")



