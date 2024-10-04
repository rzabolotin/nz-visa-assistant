import json

from config import (
    DATA_FILE_PATH,
    ELASTIC_INDEX_NAME,
    ELASTIC_URL,
    SENTENCE_TRANSFORMERS_MODEL,
)
from elasticsearch import AsyncElasticsearch
from langchain_elasticsearch import ElasticsearchRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm
from utils.logger import logger


async def search_documents(query: str) -> list:
    vector = embeddings.embed_query(query)

    knn_results = knn_retriever.invoke(vector)
    keyword_results = keyword_retriever.invoke(query)

    rrf_scores = {}

    # Calculate RRF using vector search results
    for rank, hit in enumerate(knn_results):
        doc_id: str = hit.metadata["_id"]
        rrf_scores[doc_id] = compute_rrf(rank + 1)

    # Adding keyword search result scores
    for rank, hit in enumerate(keyword_results):
        doc_id: str = hit.metadata["_id"]
        if doc_id in rrf_scores:
            rrf_scores[doc_id] += compute_rrf(rank + 1)
        else:
            rrf_scores[doc_id] = compute_rrf(rank + 1)

    # Sort RRF scores in descending order
    reranked_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    # Get top-K documents by the score
    final_results = []
    for doc_id, score in reranked_docs[:10]:
        results = id_retriever.invoke(doc_id)
        if results:
            final_results.append(results[0])
        else:
            logger.error(f"Warning: Document with id {doc_id} not found")

    return final_results


def get_sentence_embedding_dimension() -> int:
    text = "This is a sample text"
    return len(embeddings.embed_query(text))


async def find_or_create_index() -> None:
    if not await es_client.indices.exists(index=ELASTIC_INDEX_NAME):
        logger.info(f"Index '{ELASTIC_INDEX_NAME}' does not exist. Creating...")
        index_settings = {
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "url": {"type": "text"},
                    "header": {"type": "text"},
                    "main_content": {"type": "text"},
                    "main_content_vector": {
                        "type": "dense_vector",
                        "dims": get_sentence_embedding_dimension(),
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        }
        await es_client.indices.create(index=ELASTIC_INDEX_NAME, body=index_settings)
        logger.info(f"Index '{ELASTIC_INDEX_NAME}' created successfully.")
        raw_doc = await load_data(DATA_FILE_PATH)
        data_chunk = chunk_data(raw_doc)
        await encode_and_index_data(data_chunk)
        logger.info("Data indexed successfully.")

    else:
        logger.info(f"Index '{ELASTIC_INDEX_NAME}' already exists.")


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
        doc["main_content_vector"] = embeddings.embed_query(doc["main_content"])
        await es_client.index(index=ELASTIC_INDEX_NAME, document=doc)


async def close_es_client():
    await es_client.close()


def compute_rrf(rank: int, k=60) -> float:
    return 1 / (k + rank)


def knn_query(vector_query: list[float]) -> dict:
    return {
        "knn": {
            "field": "main_content_vector",
            "query_vector": vector_query,
            "k": 10,
            "num_candidates": 10000,
        },
        "size": 20,
    }


def keyword_query(query: str) -> dict:
    return {
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["main_content", "main_content"],
                        "type": "best_fields",
                    }
                }
            }
        },
        "size": 20,
    }


def id_query(doc_id: str) -> dict:
    return {"query": {"ids": {"values": [doc_id]}}}


es_client = AsyncElasticsearch([ELASTIC_URL])
embeddings = HuggingFaceEmbeddings(
    model_name=f"sentence-transformers/{SENTENCE_TRANSFORMERS_MODEL}"
)

knn_retriever = ElasticsearchRetriever.from_es_params(
    index_name=ELASTIC_INDEX_NAME,
    body_func=knn_query,
    content_field="main_content",
    url=ELASTIC_URL,
)

keyword_retriever = ElasticsearchRetriever.from_es_params(
    index_name=ELASTIC_INDEX_NAME,
    body_func=keyword_query,
    content_field="main_content",
    url=ELASTIC_URL,
)

id_retriever = ElasticsearchRetriever.from_es_params(
    index_name=ELASTIC_INDEX_NAME,
    body_func=id_query,
    content_field="main_content",
    url=ELASTIC_URL,
)

logger.info(f"Initialized Elasticsearch client with URL: {ELASTIC_URL}")
logger.info(f"Loaded HuggingFaceEmbeddings model: {SENTENCE_TRANSFORMERS_MODEL}")
