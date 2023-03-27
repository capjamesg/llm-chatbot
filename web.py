import base64
import datetime
import hashlib
import json
import os
import pprint
import random
import re
import string
import uuid

import faiss
import numpy as np
import openai
import psycopg2
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from indieweb_utils import Paginator, discover_endpoints, indieauth_callback_handler

from PromptManager import Prompt

openai.api_key = os.environ["OPENAI_KEY"]

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    database=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASS"],
)

prompt_data = Prompt()

index_number = prompt_data.index_id
queried_index = prompt_data.index_name
prompt_id = prompt_data.prompt_id

ME = os.environ["ME"]
CALLBACK_URL = ""
CLIENT_ID = ""

vector_index = faiss.read_index(
    f"indices/{index_number}/{queried_index}_vector_index.bin"
)

app = Flask(__name__)
app.secret_key = random.choice(string.ascii_letters) + "".join(
    random.choices(string.ascii_letters + string.digits, k=15)
)

with open(f"indices/{index_number}/{queried_index}_schema.json", "r") as f:
    schema = json.load(f)


def prompt_is_safe(prompt: str) -> bool:
    response = openai.Moderation.create(input=prompt)

    results = response["results"][0]

    values = list(results.values())

    # if any value is equal to True, the prompt is not safe
    if True in values:
        return False

    return True


@app.route("/")
def index():
    prompt_value = request.args.get("prompt", "")

    return render_template(
        "index.html", prompt=prompt_value, username=session.get("me")
    )


@app.route("/prompt/<prompt_id>")
def prompt(prompt_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM answers WHERE id = %s", (prompt_id,))
        prompt = cur.fetchone()

        if not prompt:
            return render_template("404.html"), 404

        return render_template("prompt.html", prompt=prompt, slug="prompt/" + prompt[2])


@app.route("/session", methods=["GET"])
def user_session():
    return render_template("session.html")


@app.route("/adminpage", methods=["GET"])
def admin():
    if not session.get("me") or session.get("me") != ME:
        return redirect("/")

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM answers ORDER BY date DESC")
        all_posts = cur.fetchall()

    # reverse posts
    all_posts = all_posts[::-1]

    paginator = Paginator(all_posts, 1)

    page = request.args.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    all_posts = paginator.get_page(page)
    num_pages = paginator.total_pages

    return render_template(
        "admin.html",
        prompts=all_posts,
        index_number=index_number,
        queried_index=queried_index,
        prompt_id=prompt_id,
        current_prompt=pprint.pformat(prompt_data.raw_prompt()),
        username=session.get("me"),
        num_pages=num_pages,
        page=page,
    )


@app.route("/defend", methods=["POST"])
def defend():
    """
    This endpoint is not in active use.
    """
    id = request.form["id"]

    # remove all punctuation aside from question marks, commas, and full stops
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM answers WHERE id = %s", (id,))
        prompt = cur.fetchone()

    query = prompt[0]

    print(prompt)

    # get Sources from prompt
    prompt_text = prompt[0]

    sources = prompt_text.split("Sources")[-1].split("[STOP]")[0]

    prompt = f"""
    Your task is to evaluate whether the following statement is backed up by the Sources provided.

    You must only use the sources in the Sources section. The end of the Sources is marked by the line [END OF SOURCES].

    You must not query the internet or reference any information not in this prompt.

    Statement
    ---------

    {query}

    Sources
    -------

    {sources}

    [END OF SOURCES]

    Explain your response in bullet points, with reference to quotations from the sources.
    """

    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """
                    You are a helpful AI bot tasked with evaluating the validity of a statement based on sources.

                    Given a statement and a list of sources, you must determine whether the statement is backed up by the sources.

                    You have no name. You must not reference your own existence in your response. You must not reference any sources not in the Sources section of a prompt.
                    """,
            },
            {
                "role": "assistant",
                "content": prompt,
            },
        ],
    )["choices"][0]["message"]["content"]

    return jsonify(
        {"response": result + "\n\n------------------------\n\nSources:\n\n" + sources}
    )


@app.route("/query", methods=["POST"])
def query():
    query = request.form["query"]
    username = session.get("me")

    # remove all punctuation aside from question marks, commas, and full stops
    query = re.sub(r"[^\w\s\?\.,]", "", query).strip("?")  # .lower()

    # query can be no more than 100 words
    query = " ".join(query.split()[:100])

    safe = prompt_is_safe(query)

    if not safe:
        return jsonify(
            {
                "response": "Sorry. I can't help you with that.",
                "references": [],
                "knn": [],
            }
        )

    # embed query
    embedded_query = openai.Embedding.create(
        input=query, model="text-embedding-ada-002"
    )

    # search for similar blocks
    D, I = vector_index.search(
        np.array([embedded_query["data"][0]["embedding"]]).reshape(1, 1536), 25
    )

    knn = []

    for i in I[0]:
        knn.append(schema[i]["text"])

    # ask gpt to complete the query

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    facts = []

    content_sources = [schema[i]["url"] for i in I[0]]
    titles = [schema[i].get("title", schema[i]["url"]) for i in I[0]]
    dates = [schema[i].get("date", "") for i in I[0]]

    # create text that looks like this
    # [fact] (Source: [source])

    facts_and_sources = []

    for fact in facts:
        facts_and_sources.append(fact + " (Source: https://jamesg.blog/about/)")

    skipped = []

    for i in range(len(knn)):
        # if there is html in the response, skip it
        # if "{" in content_sources[i]:
        #     skipped.append(i)
        #     continue

        facts_and_sources.append(
            knn[i]
            + ' (Source: <a href="'
            + content_sources[i]
            + '">'
            + titles[i]
            + "</a>, "
            + dates[i]
            + ")"
        )
    print(facts_and_sources)

    facts_and_sources_text = "\n\n".join(facts_and_sources)
    # cut off at 2000 words
    facts_and_sources_text = " ".join(facts_and_sources_text.split(" ")[:300])

    references = [
        {"url": content_sources[i], "title": titles[i]}
        for i in range(len(knn))
        if i not in skipped
    ]

    response = prompt_data.execute(
        {
            "CURRENT_DATE": current_date,
            "FACTS": "\n".join(facts),
            "SOURCES": facts_and_sources_text,
            "QUERY": query,
        }
    )

    # get all inline citations
    citations = re.findall(r"<a href=\"(.*?)\">(.*?)</a>", response)

    citations = [{"url": c[0], "title": c[1]} for c in citations]

    cursor = conn.cursor()

    # save prompt response and original question
    identifier = str(uuid.uuid4())

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO answers VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (response, query, identifier, prompt_id, date, username, "0"),
    )

    conn.commit()

    return jsonify(
        {
            "response": response,
            "knn": knn,
            "references": {
                "inline": citations,
                "sources": references,
            },
            "id": identifier,
        }
    )


@app.route("/callback")
def indieauth_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    # these are the scopes necessary for the application to run
    required_scopes = []

    try:
        response = indieauth_callback_handler(
            code=code,
            state=state,
            token_endpoint=session.get("token_endpoint"),
            code_verifier=session["code_verifier"],
            session_state=session.get("state"),
            me="https://jamesg.blog",
            callback_url=CALLBACK_URL,
            client_id=CLIENT_ID,
            required_scopes=required_scopes,
        )
    except Exception as e:
        flash("Sorry, there was an error. Please try again.")
        return redirect("/login")

    session.pop("code_verifier")

    session["me"] = response.response.get("me")
    session["access_token"] = response.response.get("access_token")
    session["scope"] = response.response.get("scope")

    return redirect("/bot")


@app.route("/logout")
def logout():
    session.pop("me")
    session.pop("access_token")

    return redirect("/login")


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/discover", methods=["POST"])
def discover_auth_endpoint():
    domain = request.form.get("domain")

    if domain.strip("/").strip() != ME:
        flash("Sorry, this domain is not supported.")
        return redirect("/login")

    headers_to_find = ["authorization_endpoint", "token_endpoint"]

    headers = discover_endpoints(domain, headers_to_find)

    if not headers.get("authorization_endpoint"):
        flash(
            "A valid IndieAuth authorization endpoint could not be found on your website."
        )
        return redirect("/login")

    if not headers.get("token_endpoint"):
        flash("A valid IndieAuth token endpoint could not be found on your website.")
        return redirect("/login")

    authorization_endpoint = headers.get("authorization_endpoint")
    token_endpoint = headers.get("token_endpoint")

    session["server_url"] = headers.get("microsub")

    random_code = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(30)
    )

    session["code_verifier"] = random_code
    session["authorization_endpoint"] = authorization_endpoint
    session["token_endpoint"] = token_endpoint

    sha256_code = hashlib.sha256(random_code.encode("utf-8")).hexdigest()

    code_challenge = base64.b64encode(sha256_code.encode("utf-8")).decode("utf-8")

    state = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
    )

    session["state"] = state

    return redirect(
        authorization_endpoint
        + "?client_id="
        + CLIENT_ID
        + "&redirect_uri="
        + CALLBACK_URL
        + "&scope=profile&response_type=code&code_challenge="
        + code_challenge
        + "&code_challenge_method=S256&state="
        + state
    )


@app.route("/feedback", methods=["POST"])
def feedback():
    feedback = request.form["feedback"]
    id = request.form["id"]

    # if id not 1 or 2, return error
    if id not in ["1", "2"]:
        return jsonify({"success": False})

    cursor = conn.cursor()

    cursor.execute(
        "UPDATE answers SET feedback = %s WHERE id = %s",
        (feedback, id),
    )

    conn.commit()

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run()
