
# New Zealand Visa Information Chatbot

![new-zealand.png](media/new-zealand.png)

## Project Overview
This project aims to create a Telegram chatbot that serves as a RAG (Retrieval-Augmented Generation) assistant for answering user questions about obtaining visas and residency in New Zealand. The chatbot is designed to improve upon traditional search methods by providing more accurate and context-aware responses based on information from the official New Zealand immigration website: https://www.immigration.govt.nz/new-zealand-visas

### Key Features:
- Utilizes Large Language Models (LLMs) to provide interactive and informative responses
- Implements RAG technology for enhanced information retrieval and answer generation
- Provides links to official sources, ensuring users can verify information and access additional details

### Target Audience:
The primary audience for this chatbot includes individuals seeking to understand New Zealand's immigration laws, particularly those interested in obtaining visas or residency. This could include potential immigrants, students, workers, or anyone planning an extended stay in New Zealand.

### Scope of Capabilities:
The chatbot is designed to answer a wide range of questions related to New Zealand immigration, including but not limited to:
- Visa types and requirements
- Application processes
- Eligibility criteria for different visas and residency options
- Documentation needed for applications
- Processing times and fees
- Rights and responsibilities under different visa categories

### Problem Solved:
This chatbot addresses the challenge of navigating complex immigration information by providing an easy-to-use, conversational interface. It aims to simplify the process of finding accurate, up-to-date information about New Zealand's immigration policies and procedures, saving users time and reducing confusion often associated with parsing through extensive government websites.

This project is developed as a final project for the [LLM Zoomcamp course](https://github.com/DataTalksClub/llm-zoomcamp/), demonstrating the practical application of Large Language Models in creating an valuable tool for real-world information retrieval and assistance.

## Data Collection and Parsing

Data is collected by scraping the official New Zealand Immigration website. The data is then parsed and stored in a JSON file for indexing and retrieval.
The parsing [script](scripts/parser.py) extracts relevant information from the website.
Parsed data stored in the [data](data) directory, but if you want to parse the data yourself, follow the instructions below.

To run the parser script, use the following command:
```bash
pipenv install
pipenv run python scripts/parser.py
```
> [Script](scripts/parser.py) has optional arguments, use `--help` to see them.


### Basic RAG flow

The basic flow is presented in [this notebook](notebooks/1.basic_rag.ipynb).
It uses the `minisearch` library for search and the `anthropic' api for RAG.

### Evaluating different retrieval approaches

I created ground truth data for evaluating different retrieval approaches using the [script](scripts/generate_ground_truth.py).

In the [evaluation notebook](notebooks/2.retrieval_evaluation.ipynb) I tested various retrieval methods including Minsearch and Elasticsearch configurations. I compared text-based and vector-based search, with and without content chunking. My analysis, using metrics like Hit Rate, MRR, and NDCG, revealed that Elasticsearch's combined search method performed best. This approach, leveraging both text and vector capabilities, was chosen for its robust performance across diverse query types.


### Evaluating different RAG approaches

In this [evaluation notebook](notebooks/3.RAG_evaluation.ipynb), I compared different RAG approaches using Anthropic's LLM API. I evaluated multiple prompts and search strategies to determine the most effective method for generating responses. By analyzing metrics like LLM-as-a-judge and ROUGE scores, I identified the optimal RAG configuration for this chatbot. The chosen approach combines a specific prompt with a search query to produce accurate and informative answers.

## Interface
