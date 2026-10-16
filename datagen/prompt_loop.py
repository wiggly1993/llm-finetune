import random
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

from prompt_builder import difficulties, prompt_builder
from hi_deepseek import deepseek_interaction

topics = [
    # strings
    "string parsing", "palindromes and anagrams", "text encoding and ciphers",
    "word counting", "string compression", "pattern matching",
    # lists
    "list manipulation", "sorting and searching", "sliding window",
    "merging and deduplication", "running totals", "rotating and reversing",
    # dicts and sets
    "dictionaries and counting", "grouping by key", "set operations",
    "caching and memoization", "inventory tracking", "graph as adjacency map",
    # math
    "math and number theory", "prime numbers", "base conversion",
    "fractions and rounding", "combinatorics", "roman numerals",
    # time and data formats
    "date and time", "calendar calculations", "unit conversion",
    "simple CSV parsing", "simple JSON-like parsing", "version number comparison",
    # structures
    "stack and queue", "linked list", "binary tree",
    "priority queue", "ring buffer", "matrix and grid",
    # objects and state
    "classes and objects", "state machine", "bank account simulation",
    "tic-tac-toe or board games", "text-based robot movement", "simple tokenizer",
    # algorithms
    "recursion", "bit manipulation", "dynamic programming",
    "path finding in a grid", "scheduling and intervals", "validation and checksums",
]

difficulties = ["easy", "medium", "hard"]

LANGS = {
    "python":     {"name": "Python",     "tool": "pytest",     "ext": ".py"},
    "javascript": {"name": "JavaScript", "tool": "jest",       "ext": ".js"},
    "cpp":        {"name": "C++",        "tool": "Catch2",     "ext": ".cpp"},
    "rust":       {"name": "Rust",       "tool": "cargo test", "ext": ".rs"},
    "go":         {"name": "Go",         "tool": "go test",    "ext": ".go"},
    "java":       {"name": "Java",       "tool": "JUnit 5",    "ext": ".java"},
}


def generate_all(per_lang, topics, difficulties):
    base = Path(__file__).parent / "raw"

    for i in range(per_lang):
        for key, cfg in LANGS.items():
            folder = base / key
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"{key}_{i}.txt"

            if path.exists() and path.stat().st_size > 0:
                continue

            topic = random.choice(topics)
            difficulty = random.choice(difficulties)

            print(f"generating {key} nr {i}. t: {topic}, d:{difficulty}")
            extra = ""
            # section of language specfic instructions that will be added at the end
            if key == "java":
                print("extra being added")
                extra = "Extra info for Java not part of the filename: ignore the lowercase rule above. " \
                "Use CamelCase, same as the public class name, ending with .java"

            if key == "cpp":
                print("extra being added")
                extra = "Extra info for C++ not part of the filename: tests must start with #include <catch2/catch_test_macros.hpp>"

            if key == "javascript":
                print("extra being added")
                extra = "Extra info for JavaScript not part of the filename: the STUB and the SOLUTION must both end with module.exports = { ... } listing every function or class the tests call. Use CommonJS only, no import or export keywords."

            input_ds_prompt = prompt_builder(
                topic, difficulty,
                cfg["name"], cfg["tool"], cfg["ext"],
                extra
            )
            try:
                out = deepseek_interaction(input_text=input_ds_prompt)
            except Exception as e:
                print(f"Error {key} {i}: {e}")
                continue

            if not out.strip():
                print(f"empty reply {key} {i}")
                continue

            path.write_text(out, encoding="utf-8")


if __name__ == "__main__":
    generate_all(100, topics, difficulties)
    #print("hi")








# for i in range(22,50):
#     print(f"we are generating file nr: {i}")
#     input_text = prompt_builder(random.choice(topics), random.choice(difficulties))
#     try:
#         ds_output = deepseek_interaction(input_text=input_text)

#         # store the response into some local txtfile
#         starting_point = Path(__file__).parent

#         full_path = starting_point / "raw" / f"test_{i}.txt"

#         with open(full_path, "w", encoding="utf-8") as f:
#             f.write(ds_output)

#     except Exception as e:
#         print(f"Error during generation iteration {i} error: {e}")