import json
import os
import sys
import time

import faiss
import numpy as np
import openai
import requests

openai.api_key = os.environ["OPENAI_KEY"]

# create indices/ if it doesn't exist
if not os.path.exists("indices"):
    os.makedirs("indices")

# create indices/current.json if it doesn't exist
if not os.path.exists("indices/current.json"):
    with open("indices/current.json", "w") as f:
        json.dump({"index": 0}, f)

with open("indices/current.json", "r") as f:
    current_index = json.load(f)["index"] + 1

with open("indices/current.json", "w") as f:
    json.dump({"index": current_index}, f)

# mkdir if it doesn't exist
if not os.path.exists("indices/" + str(current_index)):
    os.makedirs("indices/" + str(current_index))

# read all files in logs
# if "--new" is an argument, use fresh index

if current_index == 1 or "--new" in sys.argv:
    vector_index = faiss.IndexFlatL2(1536)
    schema = []
else:
    # open most recent index, which should have the name "main.bin"
    with open("indices/" + str(current_index - 1) + "/main_vector_index.bin", "rb") as f:
        vector_index = faiss.read_index(f)

    with open("indices/" + str(current_index - 1) + "/main_schema.json", "r") as f:
        schema = json.load(f)

def save_index_and_schema(vector_index, schema, stage):
    print("Saving index and schema for stage " + stage)
    dir = "indices/" + str(current_index) + "/" + stage
    faiss.write_index(vector_index, dir + "_vector_index.bin")
    with open(dir + "_schema.json", "w") as f:
        json.dump(schema, f)


def get_embedding(vector_index, document: str, schema=[]):
    # embed post
    try:
        response = openai.Embedding.create(
            input=document["text"], model="text-embedding-ada-002"
        )
    except:
        print("Rate limited...")
        time.sleep(0.1)

    embeddings = response["data"][0]["embedding"]
    vector_index.add(np.array([embeddings]).reshape(1, 1536))

    schema.append(document)

    return vector_index, schema


def get_source_code_docs(vector_index, schema=[]):
    source_code_docs = []
    source_code_doc_urls = []

    docs_directories = []

    for directory in docs_directories:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".rst") or file.endswith(".md"):
                    with open(os.path.join(root, file), "r") as f:
                        source_code_docs.append(f.read())
                        source_code_doc_urls.append(str(os.path.join(root, file)))

    counter = 0

    for doc in source_code_docs:
        doc = {
            "source": "source_code_docs",
            "text": doc,
            "title": file.replace(".md", ""),
            "url": source_code_doc_urls[source_code_docs.index(doc)],
        }

        get_embedding(vector_index, doc, schema)
        sys.stdout.flush()
        sys.stdout.write(f"\r{counter + 1} / {len(source_code_docs)}")
        sys.stdout.flush()
        counter += 1

    return vector_index, schema


def get_breakfast_and_coffee_wiki_pages(vector_index, schema=[]):
    wiki_pages = []
    wiki_page_urls = []

    for page in requests.get(
        "https://breakfastand.coffee/api.php?action=query&list=allpages&aplimit=500&format=json"
    ).json()["query"]["allpages"]:
        wiki_pages.append(page["title"])
        wiki_page_urls.append(
            "https://breakfastand.coffee/" + page["title"].replace(" ", "_")
        )

    counter = 0

    # get contents for each page
    contents = []

    for page in wiki_pages:
        data = requests.get(
            "https://breakfastand.coffee/api.php?action=query&prop=revisions&rvprop=content&format=json&titles="
            + page.replace(" ", "_")
        ).json()

        for key in data["query"]["pages"]:
            contents.append(data["query"]["pages"][key]["revisions"][0]["*"])

    for page in wiki_pages:
        page_data = None
        contents = requests.get(
            "https://breakfastand.coffee/api.php?action=query&prop=revisions&rvprop=content&format=json&titles="
            + page.replace(" ", "_")
        ).json()

        for key in contents["query"]["pages"]:
            page_data = contents["query"]["pages"][key]["revisions"][0]["*"]

        if page_data is None:
            counter += 1
            continue

        try:
            response = openai.Embedding.create(
                input=page_data, model="text-embedding-ada-002"
            )
        except:
            print("Rate limited...")
            time.sleep(0.1)
            counter += 1
            continue

        embeddings = response["data"][0]["embedding"]
        vector_index.add(np.array([embeddings]).reshape(1, 1536))
        schema.append(
            {
                "source": "wiki",
                "text": page_data,
                "embedding": np.array([embeddings]).reshape(1, 1536).tolist(),
                "title": page,
                "url": wiki_page_urls[wiki_pages.index(page)],
            }
        )
        sys.stdout.flush()
        sys.stdout.write(f"\r{counter + 1} / {len(wiki_pages)}")
        sys.stdout.flush()
        counter += 1

    return vector_index, schema


def get_public_readmes(vector_index, schema=[]):
    url_structure = (
        "https://raw.githubusercontent.com/YOUR_USERNAME/{}/master/README.md"
    )
    repositories = []

    counter = 0

    for repo in repositories:
        url = url_structure.format(repo)
        data = requests.get(url).text

        paragraphs = data.split("\n")

        for p in paragraphs:
            if p == "":
                counter += 1
                continue

            try:
                response = openai.Embedding.create(
                    input=p, model="text-embedding-ada-002"
                )
            except:
                print("Rate limited...")
                time.sleep(0.1)
                counter += 1
                continue
            embeddings = response["data"][0]["embedding"]
            vector_index.add(np.array([embeddings]).reshape(1, 1536))
            schema.append(
                {
                    "source": "github",
                    "text": p,
                    "embedding": np.array([embeddings]).reshape(1, 1536).tolist(),
                    "title": repo,
                    "url": url_structure.format(repo),
                }
            )

            sys.stdout.flush()
            sys.stdout.write(f"\r{counter + 1} / {len(repositories)}")
            sys.stdout.flush()

    return vector_index, schema


def get_facts(vector_index, schema=[]):
    # open facts.txt, delimit with /n, ingest
    with open("facts.txt", "r") as f:
        data = f.read()

    paragraphs = data.split("\n")

    counter = 0

    for p in paragraphs:
        if p == "":
            counter += 1
            continue

        try:
            response = openai.Embedding.create(input=p, model="text-embedding-ada-002")
        except:
            print("Rate limited...")
            time.sleep(0.1)
            counter += 1
            continue
        embeddings = response["data"][0]["embedding"]
        vector_index.add(np.array([embeddings]).reshape(1, 1536))
        schema.append(
            {
                "source": "facts",
                "text": p,
                "embedding": np.array([embeddings]).reshape(1, 1536).tolist(),
                "title": "Facts",
                "url": "",
            }
        )

        sys.stdout.flush()
        sys.stdout.write(f"\r{counter + 1} / {len(paragraphs)}")
        sys.stdout.flush()

        counter += 1

    return vector_index, schema


def index_pending(vector_index, schema=[]):
    # index all items in pending_indexing/*.json
    # if not exists, return
    if not os.path.exists("pending_indexing"):
        return vector_index, schema
    
    if not os.path.exists("indexed_docs"):
        os.mkdir("indexed_docs")

    for file in os.listdir("pending_indexing"):
        if file.endswith(".json"):
            with open("pending_indexing/" + file, "r") as f:
                data = json.load(f)

            for item in data:
                vector_index, schema = get_embedding(vector_index, item, schema)

            os.rename("pending_indexing/" + file, "indexed_docs/" + file)

    return vector_index, schema


vector_index, schema = index_pending(vector_index)
save_index_and_schema(vector_index, schema, "main")

# vector_index, schema = get_source_code_docs(vector_index)
# save_index_and_schema(vector_index, schema)
# vector_index, schema = get_breakfast_and_coffee_wiki_pages(vector_index, schema)
# save_index_and_schema(vector_index, schema)
# vector_index, schema = get_public_readmes(vector_index, schema)
# save_index_and_schema(vector_index, schema)
