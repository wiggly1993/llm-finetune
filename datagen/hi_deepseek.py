import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com")


def deepseek_interaction(input_text):
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": input_text},
        ],
        stream=True,
        timeout=70,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}},
    )

    ds_response = ""
    for chunk in response:
        if not chunk.choices:
            continue
        piece = chunk.choices[0].delta.content
        if piece is None:
            continue
        ds_response += piece

    return ds_response




if __name__ == "__main__":
    # store the response into some local txtfile
    starting_point = Path(__file__).parent

    full_path = starting_point / "raw" / "test1.txt"

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(deepseek_interaction(input_text="hi mark"))

    # with open(full_path, "w", encoding="utf-8") as f:
    #     f.write(response.choices[0].message.content)