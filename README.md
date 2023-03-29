# AI Documentation Chatbot (Powered by ChatGPT 3.5)

The source code for James Bot, a bot that makes reference to a corpus of documents to answer questions.

![A screenshot of James Bot, a chatbot that can answer questions using information from James' Coffee Blog](screenshot.png)

## How it Works

This AI documentation bot has three components:

1. Data ingestion, where a reference index and vector store are compiled. At this stage, the program calculates the embeddings associated with the text documents you want to ingest. You may want to write custom ingestion scripts that work with your data. An example is provided in the `example_ingest.py` file. The reference index maps to the ID associated with each item in a vector store, both of which are queried in the web application.
2. Prompt generation, where you create a prompt configuration for use in the application.
3. The web application, where:
   1. A user enters a query;
   2. The vector index and reference index are queried to return information about the entry;
   3. A prompt is generated to send to ChatGPT and;
   4. The response from the OpenAI API is returned to the client.
   
### Disclaimer
   
This application sends data from the sources you provide to OpenAI in a prompt for use in answering questions. You should independently research the data policies of OpenAI to understand how your data may be used.

## Getting Started

### Install Dependencies

To get started with this project, first set up a virtual environment and install the required dependencies:

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Export OpenAI Key

You will need an OpenAI API key to use this project. Create an OpenAI account, then retrieve your API key. Export the key into an environment variable like this:

```
export OPENAI_KEY = "YOUR_KEY"
```

### Ingest Content

Next, you will need to ingest content to create a reference index and data store. Open `example_ingest.py` and modify the code to retrieve information from the format in which your data is stored. In the example file, information is read from a folder of markdown files and compiled into an index.

The reference index can contain any aribitrary JSON, but recommended values are:

- `title`: The title of the document.
- `date`: The date on which the content was published.
- `content`: The content in the document.
- `url`: The URL where content can be found.

These values can be used at query time to provide more information to your prompt.

### Set Up a Prompt

Next, you need to configure a prompt.

To do so, open the `generate_prompt.py` file and replace the example text with the prompt that you want to use in the web application. By using this file, you can generate different versions of a prompt for use in your application. This makes it easy for you to track changes to your prompts over time and revert back to previous versions if required.

You should specify a `System` prompt and the start of the `Assistant` prompt, to which the text a user submits as a query in the web interface will be appended.

### Configure Application Database

Finally, you need to set up a database for this application. The required database schema is stored in the `schema.sql` file. Run this command to create the database from the schema:

```
psql -f schema.sql
```

Now, run the following commands so the application knows how to access your database:

```
export DB_HOST="localhost"
export DB_NAME="name"
export DB_USER="user"
export DB_PASS="password"
```

You can then run the ingestion script to create the reference index and vector store:

```
python3 example_ingest.py
```

### Configure IndieAuth Authentication

This application uses IndieAuth to support the administration panel. To authenticate as an admin, you must set up IndieAuth on your website.

When you have set up IndieAuth, you can set the following environment variables to enable the admin panel:

```
export CALLBACK_URL="https://example.com/callback"
export CLIENT_ID="https://example.com"
export ME = "https://yoursite.com" # the URL of your personal website with which you will authenticate.
```

### Run the Web Application

Next, you can run the web application:

```
python3 web.py
```

The chatbot will be available at `http://localhost:5000`.

## Schemas and Indices

The `ingest.py` script stores indices in the `indices/` directory. For each new index, a new directory is created with the number corresponding with the index.

The most recent index is stored in `indices/current.json`.

Each numbered folder will contain two types of files:

1. A JSON file with the structured information you have ingested.
2. The vector store, which contains the embeddings for each item in the index. This is stored in a `.bin` file.

If you have created multiple indices for a single version, they will all appear in the numbered folder associated with that version.

## Application Routes

The web application has a few user-facing routes:

- `/`: Send a query to the API.
- `/adminpage`: View all prompts added to the system.
- `/login`: Authenticate with [IndieAuth](https://indieweb.org/IndieAuth).
- `/session`: See all the prompts that you have created, stored in `localStorage`.
- `/logout`: Log out of the application.
- `/prompt/<id>`: View a specific prompt.

## API

You can send a query to the API to retrieve a response in a JSON format. To do so, use the following query structure:

```
curl -X POST -d "query=What books do you like?" http://localhost:5000/query
```

This query returns a payload in this form:

```
{
   "id": "prompt",
   "knn": [
      "Books!!!","## Reading Books",
      "I do not read books very often but I do enjoy reading. While I have read more books on coffee than anything else, I am very fond of fiction, particularly Japanese fiction. I like getting to know the characters and seeing them change throughout a book.",
      ...
   ],
   "references": {
      "inline":[],
      "sources":[
         {"title":"https://chat.indieweb.org/{\"type\":\"m","url":"https://chat.indieweb.org/{\"type\":\"m"},
         {"title":"How I Learn About Speciality Coffee","url":"https://jamesg.blog/2020/10/25-how-i-learn-about-speciality-coffee/"},
         ...
      ]
   },
   "response": "Answer: I do not read books very often but I do enjoy reading. While I have read more books on coffee than anything else, I am very fond of fiction, particularly Japanese fiction.\n\nEvaluation: This is my answer based on my personal preference when it comes to books.\n\nTruth: N/A Since this is a personal preference and not a factual statement, it cannot be evaluated as true or false based on the sources provided."
}
```

Where:

- `id`: The unique ID associated with the answer.
- `knn`: The nearest neighbours of the query in the vector store, used as Sources (if configured).
- `references`: The references associated with the answer.
- `response`: The response from the OpenAI API.

## Contributors

- capjamesg

## License

This project is licensed under an [MIT 0 (No-Attribution) License](LICENSE).
