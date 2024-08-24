import json
import sys
import os
from elasticsearch import Elasticsearch, exceptions
from sentence_transformers import SentenceTransformer

# Initialize Elasticsearch client
es = Elasticsearch(['http://elasticsearch:9200'])

# Initialize SentenceTransformer model
model_name = os.environ.get('SENTENCE_TRANSFORMERS_MODEL')
model = SentenceTransformer(model_name)

# Index name
INDEX_NAME = 'website_content'


def create_index():
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "url": {"type": "keyword"},
                "header": {"type": "text"},
                "content": {"type": "text"},
                "vector": {"type": "dense_vector", "dims": 768, "index": True, "similarity": "cosine"},
            }
        }
    }

    try:
        if not es.indices.exists(index=INDEX_NAME):
            es.indices.create(index=INDEX_NAME, body=index_settings)
            print(f"Index '{INDEX_NAME}' created successfully.")
        else:
            print(f"Index '{INDEX_NAME}' already exists.")
    except exceptions.ElasticsearchException as e:
        print(f"Error creating index: {e}")
        sys.exit(1)


def chunk_content(content, chunk_size=2000, overlap=100):
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

    with open(filename, 'r') as f:
        data = json.load(f)

    total_chunks = 0
    for url, doc in data.items():
        header = doc['header']
        content = doc['main_content']
        content_chunks = chunk_content(content)

        for i, chunk in enumerate(content_chunks):
            combined_text = f"{header} {chunk}"
            vector = model.encode(combined_text)

            index_doc = {
                'url': url,
                'header': header,
                'content': chunk,
                'vector': vector.tolist(),
                'chunk_index': i
            }

            es.index(index=INDEX_NAME, body=index_doc, id=f"{url}_{i}")

        total_chunks += len(content_chunks)
        print(f"Indexed: {url} ({len(content_chunks)} chunks)")

    print(f"Indexed {len(data)} documents with a total of {total_chunks} chunks from {filename}")


def index_document(filename):
    create_index()  # Ensure index exists before indexing

    with open(filename, 'r') as f:
        data = json.load(f)

    for url, doc in data.items():
        header = doc['header']
        content = doc['main_content']
        vector = model.encode(header + " " + content)

        index_doc = {
            'url': url,
            'header': header,
            'content': content,
            'vector': vector.tolist()
        }

        es.index(index=INDEX_NAME, body=index_doc, id=url)
        print(f"Indexed: {url}")

    print(f"Indexed {len(data)} documents from {filename}")


def search(prompt):
    query_vector = model.encode(prompt).tolist()

    search_query = {
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
    }

    results = es.search(index=INDEX_NAME, body=search_query, size=5)

    print(f"Search results for: '{prompt}'")
    for hit in results['hits']['hits']:
        print(f"URL: {hit['_source']['url']} (Chunk: {hit['_source'].get('chunk_index', 'N/A')})")
        print(f"Score: {hit['_score']}")
        print(f"Content snippet: {hit['_source']['content'][:200]}...")
        print()


def flush_index():
    es.indices.delete(index='website_content', ignore=[404])
    print("Index 'website_content' has been deleted.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python indexer.py [index filename|search prompt|flush]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'index':
        if len(sys.argv) != 3:
            print("Usage: python indexer.py index filename")
            sys.exit(1)
        index_document(sys.argv[2])
    elif command == 'search':
        if len(sys.argv) < 3:
            print("Usage: python indexer.py search prompt")
            sys.exit(1)
        search(" ".join(sys.argv[2:]))
    elif command == 'flush':
        flush_index()
    else:
        print("Unknown command. Use 'index', 'search', or 'flush'.")
        sys.exit(1)