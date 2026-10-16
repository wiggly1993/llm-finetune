from pathlib import Path


section_names = ["===INSTRUCTIONS===", 
                 "===STUB===", 
                 "===SOLUTION===", 
                 "===TESTS===", 
                 "===PLAN===",
                 "===FILENAME==="]


# def split_reply(text):
#     new_list = list(zip(section_names, section_names[1:]))
#     new_list.append((section_names[-1], None))

#     d = {sec_1.strip("=").lower(): get_section(text, sec_1, sec_2)  
#         for sec_1, sec_2 in new_list}

#     return d


def get_section(text, start_text, end_text=None):
    start = text.find(start_text) + len(start_text)

    if end_text:
        end = text.find(end_text)
        section = text[start:end]

    else:
        section = text[start:]

    return section.strip()

if __name__ == "__main__":
    starting_point = Path(__file__).parent

    full_path = starting_point / "raw" / "test_1.txt"

    text = open(full_path).read()