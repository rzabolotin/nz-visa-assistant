# New Zealand Visa Information Chatbot

## Project Overview

This project demonstrates the practical application of Large Language Models (LLMs) in creating an interactive and informative chatbot for visa-related queries.  
This project is developed as a final project for the [LLM Zoomcamp course](https://github.com/DataTalksClub/llm-zoomcamp/). It aims to create a Telegram chatbot that answers user questions about obtaining a visa for New Zealand, based on information from the official immigration website: https://www.immigration.govt.nz/new-zealand-visas


## Project Status

Current status: In progress

### Tasks
- [x] Implement a web scraper to download data from the immigration website and create a JSON file
- [x] Set up docker-compose configuration for building images for indexing and searching
- [x] Implement command-line argument for custom output filename in parser script
- [x] Implement indexing data from the JSON file to Elasticsearch
- [x] Implement a search algorithm for efficient information retrieval
- [ ] Integrate RAG (Retrieval-Augmented Generation) using Anthropic's LLM
- [ ] Develop and deploy a Telegram chatbot interface
- [ ] Add License information
- [ ] Adopt parser script for running in a Docker container
- [ ] Parse additional information from https://www.immigration.govt.nz/opsmanual/
- [ ] Draft of the chatbot
- [ ] Transform user's question into a query using LLM (translation and adoption for elasticsearch)


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
