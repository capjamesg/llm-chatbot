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

# get most current index from indices/current.json
if not os.path.exists("indices/current.json"):
    if not os.path.exists("indices"):
        os.makedirs("indices")

    with open("indices/current.json", "w") as f:
        json.dump({"index": 0}, f)

    current_index = 0
else:
    with open("indices/current.json", "r") as f:
        current_index = json.load(f)["index"]

# MUST FILL OUT
INDEX_ID = current_index
INDEX_NAME = "main"

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
            "content": """You are Bot. Answer the question '[[[QUERY]]]?'.

If you use text in a section to make a statement, you must cite the source in a HTML <a> tag. The text in the Sources section is formatted with a URL and a passage. You can only cite sources that are in the Sources section. The anchor text must be the title of source. You must never generate the anchor text.

Use the Sources text below, as well as your facts above, to answer. Sources have dates at the end. You should prefer more recent information. And add a caveat such as "this may be out of date since my Source was published on [date]", where [date] is the date on which the source was published. if you are citing information older than one year from [[[CURRENT_DATE]]]

[STOP] means end of sources.\n

Sources
-------

[[[SOURCES]]]

[STOP]""",
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
