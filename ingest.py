import json
import os
import sys
import time

import faiss
import numpy as np
import openai
import requests

import config

openai.api_key = config.OPENAI_KEY


def initialize_loading():
    # create indices/ if it doesn't exist
    if not os.path.exists("indices"):
        os.makedirs("indices")

    first_start = False

    # create indices/current.json if it doesn't exist
    if not os.path.exists("indices/current.json"):
        first_start = True
        with open("indices/current.json", "w") as f:
            json.dump({"index": 1}, f)

    with open("indices/current.json", "r") as f:
        current_index = json.load(f)["index"]

    if first_start or "--new" in sys.argv:
        if not first_start:
            current_index = current_index + 1
        
        with open("indices/current.json", "w") as f:
            json.dump({"index": current_index}, f)

    # mkdir if it doesn't exist
    if not os.path.exists("indices/" + str(current_index)):
        os.makedirs("indices/" + str(current_index))

    # read all files in logs
    # if first start or "--new" is an argument, use fresh index

    if first_start or "--new" in sys.argv:
        vector_index = faiss.IndexFlatL2(1536)
        schema = []
    else:
        # open most recent index, which should have the name "main.bin"
        print("Opening index "+str(current_index))
        vector_index = faiss.read_index("indices/" + str(current_index) + "/main_vector_index.bin")

        with open("indices/" + str(current_index) + "/main_schema.json", "r") as f:
            schema = json.load(f)

    return vector_index, schema, current_index


def exponential_backoff(embedding_text: str, max_retries: int = 5):
    """
    Retry a request if it fails due to rate limiting.
    """
    num_retries = 0

    while num_retries < max_retries:
        try:
            return openai.Embedding.create(
                input=embedding_text, model="text-embedding-ada-002"
            )
        except openai.error.RateLimitError:
            time.sleep(1 * num_retries)
            num_retries += 1
            print(f"Rate limited, retrying {num_retries} of {max_retries}...")

    raise requests.exceptions.ConnectionError("Could not connect to OpenAI API")


def save_index_and_schema(
    vector_index, schema: dict, current_index: int, stage: str = "main"
):
    """
    Save index and schema to disk.
    """
    print("Saving index and schema for stage " + stage)
    dir = "indices/" + str(current_index) + "/" + stage
    faiss.write_index(vector_index, dir + "_vector_index.bin")
    with open(dir + "_schema.json", "w") as f:
        json.dump(schema, f)


def get_embedding(vector_index, document: str, schema: list = []):
    """
    Get embedding for a document and add it to the vector index.
    """
    response = exponential_backoff(document["text"])

    embeddings = response["data"][0]["embedding"]
    vector_index.add(np.array([embeddings]).reshape(1, 1536))

    schema.append(document)
    time.sleep(1)
    return vector_index, schema


def index_pending(
    vector_index,
    current_index: int,
    schema: list = [],
    chunking_mechanism: str = "words",
    word_count: int = 750,
) -> tuple:
    """
    Index all pending documents in pending_indexing/*.json.

    Chunking mechanism can be either "words" or "paragraphs".

    "words" will split documents into "words" word chunks.
    "paragraphs" will split documents into paragraphs.

    "paragraphs" is recommended for documents where paragraphs hold a lot of context.

    If key context is not available at the paragraph level of a document -- such as may the the case for a wiki page, for instance -- "words" is recommended.
    """
    # if not exists, return
    if not os.path.exists("pending_indexing"):
        return vector_index, schema

    if not os.path.exists("indexed_docs"):
        os.mkdir("indexed_docs")

    for file in os.listdir("pending_indexing"):
        if file.endswith(".json"):
            with open("pending_indexing/" + file, "r") as f:
                data = json.load(f)

            sys.stdout.write(f"Indexing {file}\n")
            sys.stdout.flush()

            document_text = data["text"].split(" ")

            # divide document into 750 word chunks, max
            if chunking_mechanism == "words":
                chunks = [
                    " ".join(document_text[i : i + word_count])
                    for i in range(0, len(document_text), word_count)
                ]
            elif chunking_mechanism == "paragraphs":
                chunks = data["text"].split("\n\n")
            else:
                raise ValueError("Invalid chunking mechanism.")

            other_metadata = data.copy()

            # remove text from other_metadata
            del other_metadata["text"]

            fully_assembled_docs = []

            for chunk in chunks:
                fully_assembled_docs.append({"text": chunk, **other_metadata})

            print("  Indexing in "+str(len(chunks))+" chunks")

            for data in fully_assembled_docs:
                vector_index, schema = get_embedding(vector_index, data, schema)
                save_index_and_schema(vector_index, schema, current_index, stage="main")

            os.rename("pending_indexing/" + file, "indexed_docs/" + file)

    return vector_index, schema


vector_index, schema, current_index = initialize_loading()
vector_index, schema = index_pending(
    vector_index, current_index, schema, chunking_mechanism="words"
)
