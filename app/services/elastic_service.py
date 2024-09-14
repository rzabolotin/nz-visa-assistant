import json

from config import (
    DATA_FILE_PATH,
    ELASTIC_INDEX_NAME,
    ELASTIC_URL,
    SENTENCE_TRANSFORMERS_MODEL,
)
from elasticsearch import AsyncElasticsearch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

es_client = AsyncElasticsearch([ELASTIC_URL])
model = SentenceTransformer(SENTENCE_TRANSFORMERS_MODEL)


async def search_documents(query: str) -> list:
    vector = model.encode(query).tolist()
    search_query = {
        "_source": [
            "url",
            "header",
            "main_content",
            "main_content_vector",
        ],
        "query": {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["header", "main_content"],
                            "type": "best_fields",
                            "tie_breaker": 0.3,
                        }
                    },
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'main_content_vector') + 1.0",
                                "params": {"query_vector": vector},
                            },
                        }
                    },
                ]
            }
        },
        "size": 10,
    }

    es_results = await es_client.search(index=ELASTIC_INDEX_NAME, body=search_query)
    return [hit["_source"] for hit in es_results["hits"]["hits"]]


async def find_or_create_index() -> None:
    if not await es_client.indices.exists(index=ELASTIC_INDEX_NAME):
        index_settings = {
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "url": {"type": "text"},
                    "header": {"type": "text"},
                    "main_content": {"type": "text"},
                    "main_content_vector": {
                        "type": "dense_vector",
                        "dims": model.get_sentence_embedding_dimension(),
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        }
        await es_client.indices.create(index=ELASTIC_INDEX_NAME, body=index_settings)
        print(f"Index '{ELASTIC_INDEX_NAME}' created successfully.")
        raw_doc = await load_data(DATA_FILE_PATH)
        data_chunk = chunk_data(raw_doc)
        await encode_and_index_data(data_chunk)
        print(f"Data indexed successfully.")

    else:
        print(f"Index '{ELASTIC_INDEX_NAME}' already exists.")


async def load_data(file_path: str) -> dict:
    with open(file_path, "r") as f_in:
        return json.load(f_in)


def chunk_data(raw_doc: dict, chunk_size: int = 1000, overlap: int = 100) -> list[dict]:
    def chunk_content(
        content: str, chunk_size: int = 1000, overlap: int = 100
    ) -> list[str]:
        chunks = []
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks

    chunked_data = []
    for k, v in raw_doc.items():
        content_chunks = chunk_content(v["main_content"], chunk_size, overlap)
        for i, chunk in enumerate(content_chunks):
            chunked_data.append(
                {
                    "url": k,
                    "header": v["header"],
                    "main_content": chunk,
                    "chunk_index": i,
                }
            )

    return chunked_data


async def encode_and_index_data(data_chunk: list[dict]):
    for doc in tqdm(data_chunk, desc="Indexing documents"):
        doc["main_content_vector"] = model.encode(doc["main_content"]).tolist()
        await es_client.index(index=ELASTIC_INDEX_NAME, document=doc)


async def close_es_client():
    await es_client.close()
