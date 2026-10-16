from pathlib import Path



section_names = ["===INSTRUCTIONS===", 
                 "===STUB===", 
                 "===SOLUTION===", 
                 "===TESTS===", 
                 "===PLAN===",
                 "===FILENAME==="]



def get_section(text, start_text, end_text=None):
    start = text.find(start_text) + len(start_text)

    if end_text:
        end = text.find(end_text)
        section = text[start:end]

    else:
        section = text[start:]

    return section.strip()



def split_reply(text):
    '''
    creates a dictionary based on a .md file
    where all sections are broken into individual parts
    and these parts then result it indiv. entries in a dictionary 
    {instruction: blabla, stub: blabla, etc.}
    we will use this to access the specific parts we need from the ds reply
    to fill it into our template.md to create the fake convo we need for fine tuning

    input: raw .md file text
    output: dictionary where each section has its own key
    '''
    new_list = list(zip(section_names, section_names[1:]))
    new_list.append((section_names[-1], None))

    d = {sec_1.strip("=").lower(): get_section(text, sec_1, sec_2)  
        for sec_1, sec_2 in new_list}

    return d

if __name__ == "__main__":
    starting_point = Path(__file__).parent
    full_path = starting_point / "raw" / "test_1.txt"
    with open(full_path) as f:
        raw_ds_output = f.read()
    
        d = split_reply(text=raw_ds_output)
        print(d["filename"])