from pathlib import Path
import sys
import subprocess

from split_reply import split_reply

starting_point = Path(__file__).parent.parent


def parse_template():
    '''
    this function accesses the template.md
    based on that it cleans then data inside and creates a number of dicts
    which then are stored in a list [d1, d2, ...] where each contains one role and the content
    returns then list of the dictionaries
    '''
    template_md_path = starting_point / "golden" / "template.md"
    with open(template_md_path, encoding="utf-8") as f:
        template_md_raw = f.read()

    # we break the entire .md file into a list separted by ---
    block_list = template_md_raw.split("\n-------\n")

    template_dict_list = []
    for block in block_list:
        #print(block)

        role_loc = block.find(" ")
        role = block[:role_loc].lower()
        #print(f"role of current block: {role}")

        cleaned_split_block = []
        split_block = block.splitlines()
        # we break down this one block into individual lines 
        for line in split_block:
            line = line[role_loc+1:]
            cleaned_split_block.append(line)

        combined_split_block = "\n".join(cleaned_split_block)
        d = {"role": role, "content": combined_split_block.strip()}

        template_dict_list.append(d)

    return template_dict_list


def fill_messages(messages, filename, stub, instructions):
    '''
    arse_template() (based on a template) provides a list of dictionaries that contain the fake convo
    it also has some placeholders like [[STUB]], which will be filled by the other 3 parameters
    crucial: these other 3 params are to be provided from the deepseek generated answer
    returns: a LIST of dictionaries for the entire fake convo
    '''

    updated_dict_list = []
    for i, d in enumerate(messages):
        # replace one string with another
        # we are replacing the placeholders with actual content
        role = d["role"] 
        text = d["content"] 

        text = text.replace("[[FILENAME]]", filename)
        text = text.replace("[[INSTRUCTIONS]]", instructions)
        text = text.replace("[[STUB]]", stub)

        new_d = {"role": role, "content": text}

        updated_dict_list.append(new_d)

        # we check whether all content checks give us -1. if any does NOT give us -1
        # it means either of those 3 has fired which then will raise an error
        if (new_d["content"].find("[[FILENAME]]") != -1 or new_d["content"].find("[[INSTRUCTIONS]]") != -1 
            or new_d["content"].find("[[STUB]]") != -1):
            
            raise ValueError(f"blank left in message {new_d["role"]} dict nr:{i}")

    return updated_dict_list
        
        



if __name__ == "__main__":
    template_dict_list = parse_template()
    # fill_messages(messages=template_dict_list, 
    #             filename="dummy.py", stub="stupoo", instructions="instr bla bla")

    tasks = [
    {
        "filename": "greet.py",
        "stub": "def greet(name):\n    pass",
        "instructions": "# Instructions\n\nReturn 'Hello, <name>!'.",
    },
    {
        "filename": "add.py",
        "stub": "# [[FILENAME]]\ndef add(a, b):\n    pass",
        "instructions": "# Instructions\n\nReturn the sum of a and b.",
    },
]


    final_dict_list = []
    kept = 0
    skipped = 0
    for t in tasks:
        try:
            updated_dict_list = fill_messages(template_dict_list, t["filename"], t["stub"], t["instructions"])
            final_dict_list.append(updated_dict_list)
            add += 1


        except ValueError as e:
            print(f"{t["filename"]} has issues: {e}")
            skipped += 1
            continue

    #print(final_dict_list)
    print(f"in total {kept} have been kept and {skipped} have been skipped")