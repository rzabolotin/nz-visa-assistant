from elasticsearch import AsyncElasticsearch
from config import ELASTIC_URL

es_client = AsyncElasticsearch([ELASTIC_URL])


async def search_documents(query: str) -> list:
    # Implement Elasticsearch search logic here
    pass
