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

## Getting Started

To get started with this project, first set up a virtual environment and install the required dependencies:

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

You will need an OpenAI API key to use this project. Create an OpenAI account, then retrieve your API key. Export the key into an environment variable like this:

```
export OPENAI_KEY = "YOUR_KEY"
```

Next, you will need to ingest content to create a reference index and data store. Open `example_ingest.py` and modify the code to retrieve information from the format in which your data is stored. In the example file, information is read from a folder of markdown files and compiled into an index.

The reference index can contain any aribitrary JSON, but recommended values are:

- `title`: The title of the document.
- `date`: The date on which the content was published.
- `content`: The content in the document.
- `url`: The URL where content can be found.

These values can be used at query time to provide more information to your prompt.

Next, you need to configure a prompt.

To do so, open the `generate_prompt.py` file and replace the example text with the prompt that you want to use in the web application. By using this file, you can generate different versions of a prompt for use in your application. This makes it easy for you to track changes to your prompts over time and revert back to previous versions if required.

You should specify a `System` prompt and the start of the `Assistant` prompt, to which the text a user submits as a query in the web interface will be appended.

Once you have written your ingestion logic, run this command:

```
python3 example_ingest.py
```

Next, you can run the web application:

```
python3 web.py
```

The chatbot will be available at `http://localhost:5000`.

## Application Routes

The web application has a few routes:

- `/`: Send a query to the API.
- `/adminpage`: View all prompts added to the system.
- `/login`: Authenticate with [IndieAuth](https://indieweb.org/IndieAuth).

## API

You can send a query to the API to retrieve a response in a JSON format. To do so, use the following query structure:

```
curl -X POST http://localhost:5000/query -H "Content-Type: application/json" -d [add data here]
```

## Contributors

- capjamesg

## License

This project is licensed under an [MIT 0 (No-Attribution) License](LICENSE).
