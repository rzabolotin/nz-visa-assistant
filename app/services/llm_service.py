import re

from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, LLM_MODEL
from services.elastic_service import search_documents

client = Anthropic(api_key=ANTHROPIC_API_KEY)


async def process_query(query: str) -> tuple[str, int, int]:
    search_results = await search_documents(query)
    prompt = build_prompt(query, search_results)
    response, input_tokens, output_tokens = await call_llm(prompt)
    answer = extract_answer(response)
    return answer, input_tokens, output_tokens


async def call_llm(prompt: str) -> tuple[str, int, int]:
    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    )
    return (
        response.content[0].text,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )


def format_search_results(search_results: list[dict]) -> str:
    formatted_results = ""
    for result in search_results:
        formatted_results += f"- **{result['header']}**\n  {result['main_content']}\n  URL: {result['url']}\n\n"
    return formatted_results.strip()


def build_prompt(query: str, search_results: list) -> str:
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

    Write your answer using short markdown syntax, as it will be displayed in a Telegram chat. Follow these formatting guidelines:
    - Use **bold** for emphasis on key points.
    - Use *italics* for titles of documents or important terms.
    - Use bullet points or numbered lists for multiple items or steps.
    - Use `inline code` for specific visa codes or short official terms.

    Always include at least one relevant URL from the context as a reference. Format the URL reference at the end of your answer like this:
    [Source](URL)

    If multiple sources are used, include them as separate reference links at the end of your answer.

    Keep your answer concise and well-structured, using short paragraphs and appropriate markdown formatting to enhance readability.

    Provide your answer within <answer> tags.
    """.strip()
    return prompt_template


def extract_answer(response: str) -> str:
    match = re.search(r"<answer>(.*?)</answer>", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return response.strip()
