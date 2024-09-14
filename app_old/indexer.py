import json
import sys
import os
import warnings

import anthropic
from elasticsearch import Elasticsearch, exceptions
from sentence_transformers import SentenceTransformer


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Initialize Elasticsearch client
elasticsearch_url = os.environ.get("ELASTICSEARCH_URL")
if not elasticsearch_url:
    print("Error: ELASTICSEARCH_URL environment variable is not set.")
    sys.exit(1)
es = Elasticsearch(elasticsearch_url)

# Initialize SentenceTransformer model
model_name = os.environ.get("SENTENCE_TRANSFORMERS_MODEL")
model = SentenceTransformer(model_name)

# Index name
INDEX_NAME = os.environ.get("ELASTICSEARCH_INDEX", "website_content")


def create_index():
    index_settings = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "url": {"type": "keyword"},
                "header": {"type": "text"},
                "content": {"type": "text"},
                "vector": {
                    "type": "dense_vector",
                    "dims": model.get_sentence_embedding_dimension(),
                    "index": True,
                    "similarity": "cosine",
                },
            }
        },
    }

    try:
        if not es.indices.exists(index=INDEX_NAME):
            es.indices.create(index=INDEX_NAME, body=index_settings)
            print(
                f"Index '{INDEX_NAME}' created successfully with embedding dimension: {model.get_sentence_embedding_dimension()}"
            )
        else:
            print(f"Index '{INDEX_NAME}' already exists.")
    except exceptions.ElasticsearchException as e:
        print(f"Error creating index: {e}")
        sys.exit(1)


def chunk_content(content, chunk_size=1000, overlap=100):
    chunks = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        chunk = content[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def index_document(filename):
    create_index()  # Ensure index exists before indexing

    # Construct the full path
    full_path = os.path.join("/app/data", filename)

    with open(full_path, "r") as f:
        data = json.load(f)

    total_chunks = 0
    for url, doc in data.items():
        header = doc["header"]
        content = doc["main_content"]
        content_chunks = chunk_content(content)

        for i, chunk in enumerate(content_chunks):
            combined_text = f"{header} {chunk}"
            vector = model.encode(combined_text)

            index_doc = {
                "url": url,
                "header": header,
                "content": chunk,
                "vector": vector.tolist(),
            }

            es.index(index=INDEX_NAME, body=index_doc, id=f"{url}_{i}")

        total_chunks += len(content_chunks)
        print(f"Indexed: {url} ({len(content_chunks)} chunks)")

    print(
        f"Indexed {len(data)} documents with a total of {total_chunks} chunks from {filename}"
    )


def search(prompt, return_results=False):
    query_vector = model.encode(prompt).tolist()

    search_query = {
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                    "params": {"query_vector": query_vector},
                },
            }
        }
    }

    results = es.search(index=INDEX_NAME, body=search_query, size=5)

    if return_results:
        return [
            {"url": hit["_source"]["url"], "content": hit["_source"]["content"]}
            for hit in results["hits"]["hits"]
        ]

    print(f"Search results for: '{prompt}'")
    for hit in results["hits"]["hits"]:
        print(
            f"URL: {hit['_source']['url']} (Chunk: {hit['_source'].get('chunk_index', 'N/A')})"
        )
        print(f"Score: {hit['_score']}")
        print(f"Content snippet: {hit['_source']['content'][:200]}...")
        print()


def flush_index():
    es.indices.delete(index="website_content", ignore=[404])
    print("Index 'website_content' has been deleted.")


def answer_visa_question(question):
    # Search for relevant context
    search_results = search(question, return_results=True)

    # Prepare context from search results
    context = "\n\n".join(
        [
            f"URL: {result['url']}\nContent: {result['content']}"
            for result in search_results
        ]
    )

    # Prepare prompt for Anthropic
    prompt = f"""You're a smart assistant that can answer questions about getting visas in New Zealand.
Use the following context to answer the user's question. If you can't find the answer in the context,
say you don't have enough information to answer accurately.

Context:
{context}

User's question: {question}

Answer:"""

    # Use Anthropic API to generate answer
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.completions.create(
        model="claude-3-5-sonnet-20240620", max_tokens_to_sample=300, prompt=prompt
    )

    print(response.completion)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python indexer.py [index filename|search prompt|flush|answer question]"
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "index":
        if len(sys.argv) != 3:
            print("Usage: python indexer.py index filename")
            print("Note: The file should be in the /app/data directory.")
            sys.exit(1)
        index_document(sys.argv[2])
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python indexer.py search prompt")
            sys.exit(1)
        search(" ".join(sys.argv[2:]))
    elif command == "flush":
        flush_index()
    elif command == "answer":
        if len(sys.argv) < 3:
            print("Usage: python indexer.py answer 'your question about NZ visas'")
            sys.exit(1)
        answer_visa_question(" ".join(sys.argv[2:]))
    else:
        print("Unknown command. Use 'index', 'search', 'flush', or 'answer'.")
        sys.exit(1)
