
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
> Script has optional arguments, use `--help` to see them.


## How to Run the Project

### Prerequisites

- Docker and Docker Compose installed on your system
- Python 3.9 or higher
- Elasticsearch 8.4.3 or compatible version

### Setting Up the Environment

1. Clone the repository:
   ```
   git clone https://github.com/rzabolotin/nz-visa-assistant.git
   cd <repository-directory>
   ```

2. Build the Docker images:
   ```
   docker-compose build
   ```

3. Start the services:
   ```
   docker-compose up -d
   ```

This will start Elasticsearch and the indexer application.

### Parsing Data

Before indexing, you need to parse the website data. Run:
```
python scripts/parser-v2.py [-o OUTPUT_FILENAME]
```

For example:
```
python scripts/parser-v2.py -o custom_output.json
```

If no output filename is specified, it will default to 'site_content.json'.
The parsed data will be automatically saved in the `./data` directory.

### Indexing Data

To index the scraped data:

1. Ensure your JSON file with the scraped data is in the `./data` directory.

2. Run the indexing command:
   ```
   docker-compose exec app runner index your_data_file.json
   ```

Replace `your_data_file.json` with the actual name of your JSON file.

3. You should see output indicating the indexing progress and completion.

Note: The indexer automatically looks for files in the `/app/data` directory within the container, which is mapped to the `./data` directory on your host machine.

### Running a Search

To perform a search:

```
docker-compose exec app runner search "Your search query here"
```

Replace "Your search query here" with the actual question or query you want to search for.

### Flushing the Index

If you need to clear the index:

The search will return the top 5 most relevant results, showing:
- The URL of the page
- The chunk index (if applicable)
- The relevance score
- A snippet of the content

```
docker-compose exec app runner flush
```

This will delete the entire 'website_content' index from Elasticsearch.
