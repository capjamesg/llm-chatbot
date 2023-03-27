import datetime
import json
import os
import re
import uuid

if not os.path.exists("prompts.json"):
    data_structure = {"prompts": {}, "latest_id": ""}

    with open("prompts.json", "w") as f:
        json.dump(data_structure, f)

with open("prompts.json", "r") as f:
    prompt_data = json.load(f)

# MUST FILL OUT
INDEX_ID = 16
INDEX_NAME = "index"

prompt_to_add = {
    "id": uuid.uuid4().hex,
    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    "index_id": INDEX_ID,
    "index_name": INDEX_NAME,
    "prompt": [
        {
            "role": "system",
            "content": f"""System prompt.""",
        },
        {
            "role": "user",
            "content": """Example user prompt.""",
        },
        {
            "role": "assistant",
            "content": """Example assistant response.""",
        },
        {
            "role": "user",
            "content": """Example user question.""",
        },
        {
            "role": "assistant",
            "content": """Example assistant response.""",
        },
        {
            "role": "user",
            "content": f"""Full user question.""",
        },
    ],
}

required_substitutions = []

for prompt in prompt_data["prompts"]:
    # find text in [[[TEXT]]] format
    contents = [i["content"] for i in prompt_to_add["prompt"]]
    matches = re.findall(r"\[\[\[(.*?)\]\]\]", "".join(contents))

    for match in matches:
        if match not in required_substitutions:
            required_substitutions.append(match)

prompt_data["prompts"][prompt_to_add["id"]] = prompt_to_add
prompt_data["prompts"][prompt_to_add["id"]]["substitutions"] = required_substitutions
prompt_data["latest_id"] = prompt_to_add["id"]

with open("prompts.json", "w") as f:
    json.dump(prompt_data, f)
