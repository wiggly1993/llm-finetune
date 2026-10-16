import random

topics = [
    "string parsing", "list manipulation", "dictionaries and counting",
    "recursion", "sorting and searching", "math and number theory",
    "date and time", "classes and objects", "matrix and grid",
    "text encoding and ciphers", "stack and queue", "bit manipulation",
]

difficulties = ["easy", "medium", "hard"]

def prompt_builder(topic, difficulty, language="Python", tool="pytest", ext=".py", extra=""):
    return (
        f"Create a NEW {language} programming exercise in the style of Exercism. "
        f"Topic: {topic}. Difficulty: {difficulty}.\n\n"
        "Reply with exactly these delimiters, each on its own line, "
        "followed by its content. Nothing before the first delimiter, "
        "no markdown code fences anywhere.\n\n"
        "===INSTRUCTIONS===\n"
        "Markdown starting with '# Instructions'. Specify behavior and edge cases "
        "clearly enough to pass the tests without seeing them.\n"
        "===STUB===\n"
        "Starter file. Same names and signatures as the solution, "
        "bodies left empty or unimplemented. Must compile or run.\n"
        "===SOLUTION===\n"
        "Complete working file. Standard library only.\n"
        "===TESTS===\n"
        f"Tests written with {tool}. Must pass with the solution and fail with the stub. "
        "Do NOT import or include the solution, our script adds that.\n"
        "===PLAN===\n"
        "3-5 numbered sentences, first person, describing the approach and edge cases. "
        "Plain text only, no code, no backticks. Max 130 words.\n"
        "Describe only the solution approach. Never mention tests or testing.\n"
        "===FILENAME===\n"
        "Only the filename, nothing else. lowercase words joined by underscores, "
        f"ending with {ext}\n"
        f"{extra}"
    )





if __name__ == "__main__":
    #print(prompt_builder(random.choice(topics), random.choice(difficulties)))
    print(prompt_builder("strings", "easy", "JavaScript", "jest", ".js"))