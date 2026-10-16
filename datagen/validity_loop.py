from validate import build_diff
from split_reply import split_reply
from parse_template import fill_messages, parse_template
from task_filter import task_is_good

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


if __name__ == "__main__":
    ###### play times here ######
    # this is the templated based base. we will fill in the missing stuff based on a 
    # deepseek reply
    lang = "java"
    base_dict_list = parse_template()

    kept, skipped = 0, 0

    # prepare the .jsonl file where we will contain all the fine-tune samples
    starting_point = Path(__file__).parent

    full_out_path = starting_point / "out" / f"{lang}_pilot.jsonl"
    counter_dict = {}

    with open(full_out_path, "w") as out:

        for p in Path(starting_point / "raw" / lang).glob("*.txt"):
            print(f"processing: {p}")
            with open(p) as f:
                raw_ds_output = f.read()

            try:
                # dictionary with unique ds replies chopped into indiv. entries
                deepseek_parts = split_reply(text=raw_ds_output)

                # clean these parts so diff apply does not fail
                deepseek_parts["stub"] = washer(deepseek_parts["stub"])
                deepseek_parts["solution"] = washer(deepseek_parts["solution"])

                # we run the deepseek parts through our validation tests
                value, info_text = task_is_good(deepseek_parts)
                if not value:
                    print(f"{p} file was fucked up. {info_text}")
                    skipped += 1
                    counter_dict[info_text] = counter_dict.get(info_text, 0) + 1
                    continue

                # run the core file that creates the record ({"messages": filled_d}) we need for training 
                record = build_record(base_dict_list, deepseek_parts)

                out.write(json.dumps(record) + "\n")



                kept += 1

            except Exception as e:
                print(p.name, e)
                skipped += 1


    print(f"kept: {kept}, skipped: {skipped}")
    print(counter_dict)


    

    

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



