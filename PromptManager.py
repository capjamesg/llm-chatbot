import json
import os
from copy import deepcopy

import openai

openai.api_key = os.environ["OPENAI_KEY"]

# if prompts.json not present, raise error
if not os.path.exists(f"prompts.json"):
    raise Exception("prompts.json not found. You must generate a prompt with `python3 generateprompt.py` before running the web app.")

with open("prompts.json", "r") as f:
    prompts = json.load(f)

prompt_list = prompts["prompts"]


class Prompt:
    def __init__(self, prompt_id=prompts["latest_id"]):
        self.prompt_id = prompt_id
        self.substitutions = prompt_list[self.prompt_id]["substitutions"]
        self.date_created = prompt_list[self.prompt_id]["date"]
        self.index_id = prompt_list[self.prompt_id]["index_id"]
        self.index_name = prompt_list[self.prompt_id]["index_name"]

    def __repr__(self):
        print(f"Prompt ID: {self.prompt_id}")
        print(self.prompt)

    def seek_substitutions(self):
        print(self.substitutions)

    def raw_prompt(self):
        return prompt_list[self.prompt_id]["prompt"]

    def execute(self, substitutions={}):
        new_prompt = deepcopy(prompt_list[self.prompt_id])

        for message in new_prompt["prompt"]:
            for key in substitutions:
                if key in message["content"]:
                    message["content"] = message["content"].replace(
                        f"[[[{key}]]]", substitutions[key]
                    )

        return openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=new_prompt["prompt"],
        )["choices"][0]["message"]["content"]
