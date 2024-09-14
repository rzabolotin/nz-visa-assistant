import argparse
import json
import random
import re
from typing import Dict, List

from anthropic import Anthropic
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Constants
MODEL_NAME = "all-MiniLM-L12-v2"
INDEX_NAME_VECTOR = "esearchvector_chunks_2"
ELASTICSEARCH_URL = "http://localhost:9200"
DATA_FILE_PATH = "../data/site_content.json"
LLM_MODEL = "claude-3-haiku-20240307"


def load_data(file_path: str) -> Dict:
    with open(file_path, "r") as f_in:
        return json.load(f_in)


def initialize_es_client() -> Elasticsearch:
    return Elasticsearch(ELASTICSEARCH_URL)


def initialize_sentence_transformer() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def setup_es_index(es_client: Elasticsearch, model: SentenceTransformer):
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
    es_client.indices.delete(index=INDEX_NAME_VECTOR, ignore_unavailable=True)
    es_client.indices.create(index=INDEX_NAME_VECTOR, body=index_settings)


def chunk_data(raw_doc: Dict, chunk_size: int = 1000, overlap: int = 100) -> List[Dict]:
    def chunk_content(
        content: str, chunk_size: int = 1000, overlap: int = 100
    ) -> List[str]:
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


def encode_and_index_data(
    es_client: Elasticsearch, model: SentenceTransformer, data_chunk: List[Dict]
):
    for doc in data_chunk:
        doc["header_vector"] = model.encode(doc["header"]).tolist()
        doc["main_content_vector"] = model.encode(doc["main_content"]).tolist()

    for doc in tqdm(data_chunk):
        es_client.index(index=INDEX_NAME_VECTOR, document=doc)


def elastic_search_combined_10(
    es_client: Elasticsearch, model: SentenceTransformer, query: str
) -> List[Dict]:
    vector = model.encode(query).tolist()
    search_query = {
        "_source": [
            "url",
            "header",
            "main_content",
            "header_vector",
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

    es_results = es_client.search(index=INDEX_NAME_VECTOR, body=search_query)

    return [hit["_source"] for hit in es_results["hits"]["hits"]]


def llm(client: Anthropic, prompt: str) -> str:
    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    )
    return response.content[0].text


def format_search_results(search_results: List[Dict]) -> str:
    formatted_results = ""
    for result in search_results:
        formatted_results += f"- **{result['header']}**\n  {result['main_content']}\n  URL: {result['url']}\n\n"
    return formatted_results.strip()


def build_big_prompt(query: str, search_results: List[Dict]) -> str:
    prompt_template = f"""
You are an AI assistant specializing in answering questions about New Zealand visas. Your knowledge comes from official New Zealand immigration information. You will be provided with context from relevant articles and a specific question to answer.

First, review the following context:

<context>
{format_search_results(search_results)}
</context>

Process this context carefully. Each item in the context contains a URL, a header, and main content. Use this information to inform your answers, ensuring you provide accurate and up-to-date information about New Zealand visas.

Now, answer the following question:

<question>
{query}
</question>

To answer the question:
1. Analyze the question and identify the key points related to New Zealand visas.
2. Search through the provided context for relevant information.
3. Formulate a clear, concise answer based on the official information.
4. If the question cannot be fully answered with the given context, state this clearly and provide the most relevant information available.

Write your answer using short markdown syntax, as it will be displayed in a Telegram chat. Use **bold** for emphasis and *italics* for titles or important terms.

Always include at least one relevant URL from the context as a reference. Format the URL reference at the end of your answer like this:
[Source](URL)

If multiple sources are used, include them as separate reference links.

Provide your answer within <answer> tags.
""".strip()
    return prompt_template


def extract_big_answer(llm_response: str) -> str:
    match = re.search(r"<answer>(.*?)</answer>", llm_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return llm_response.strip()


def rag(
    query: str,
    es_client: Elasticsearch,
    model: SentenceTransformer,
    anthropic_client: Anthropic,
) -> str:
    search_results = elastic_search_combined_10(es_client, model, query)
    prompt = build_big_prompt(query, search_results)
    answer = llm(anthropic_client, prompt)
    return extract_big_answer(answer)


def main():
    parser = argparse.ArgumentParser(
        description="RAG-based question answering system for New Zealand visa information"
    )
    parser.add_argument("query", type=str, help="The question to be answered")
    args = parser.parse_args()

    raw_doc = load_data(DATA_FILE_PATH)
    es_client = initialize_es_client()
    model = initialize_sentence_transformer()
    anthropic_client = Anthropic()

    setup_es_index(es_client, model)
    data_chunk = chunk_data(raw_doc)
    encode_and_index_data(es_client, model, data_chunk)

    answer = rag(args.query, es_client, model, anthropic_client)
    print(answer)


if __name__ == "__main__":
    main()
