from anthropic import Anthropic
from services.elastic_service import search_documents
from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)


async def process_query(query: str) -> str:
    search_results = await search_documents(query)
    prompt = build_prompt(query, search_results)
    response = await call_llm(prompt)
    return extract_answer(response)


async def call_llm(prompt: str) -> str:
    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return "I'm sorry, but I encountered an error while processing your request. Please try again later."


def build_prompt(query: str, search_results: list) -> str:
    # Implement prompt building logic here
    pass


def extract_answer(response: str) -> str:
    # Implement answer extraction logic here
    pass
