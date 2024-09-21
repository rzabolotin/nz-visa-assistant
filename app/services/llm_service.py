import re
from typing import List, Tuple

from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, LLM_MODEL
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain_anthropic import AnthropicLLM, ChatAnthropic
from langchain_community.callbacks.manager import get_openai_callback
from services.elastic_service import search_documents
from utils.logger import logger

client = Anthropic(api_key=ANTHROPIC_API_KEY)
llm = AnthropicLLM(model=LLM_MODEL, anthropic_api_key=ANTHROPIC_API_KEY)
chat_model = ChatAnthropic(model=LLM_MODEL, anthropic_api_key=ANTHROPIC_API_KEY)

logger.info(f"Initialized Anthropic client and models with model: {LLM_MODEL}")


class TokenCounter:
    def __init__(self):
        self.main_prompt_tokens = 0
        self.output_tokens = 0
        self.system_tokens = 0

    def add_main_prompt_tokens(self, tokens: int):
        self.main_prompt_tokens += tokens

    def add_output_tokens(self, tokens: int):
        self.output_tokens += tokens

    def add_system_tokens(self, tokens: int):
        self.system_tokens += tokens


async def process_query(query: str) -> Tuple[str, str, TokenCounter]:
    logger.info(f"Processing query: {query}")

    token_counter = TokenCounter()

    # Detect language and translate if necessary
    detected_language, translated_query = await detect_and_translate(
        query, token_counter
    )
    logger.info(f"Detected language: {detected_language}")

    # Check if the query is related to NZ immigration
    if not await is_related_to_nz_immigration(translated_query, token_counter):
        logger.info("Query not related to NZ immigration. Generating generic response.")
        answer = await generate_generic_response(translated_query, token_counter)
        if detected_language not in ["english", "en"]:
            logger.info(f"Translating answer back to {detected_language}")
            answer = await translate_text(
                answer, "english", detected_language, token_counter
            )

        return answer, detected_language, token_counter

    # Prepare relevant search query
    search_query = await prepare_search_query(translated_query, token_counter)
    logger.info(f"Prepared search query: {search_query}")

    search_results = await search_documents(search_query)
    logger.info(f"Found {len(search_results)} search results")

    prompt = build_prompt(translated_query, search_results)
    response = await call_llm(prompt, token_counter)
    answer = extract_answer(response)

    # Translate answer back to original language if necessary
    if detected_language not in ["english", "en"]:
        logger.info(f"Translating answer back to {detected_language}")
        answer = await translate_text(
            answer, "english", detected_language, token_counter
        )

    logger.info(
        f"Processed query. Main prompt tokens: {token_counter.main_prompt_tokens}, System tokens: {token_counter.system_tokens}, Output tokens: {token_counter.output_tokens}"
    )
    return answer, detected_language, token_counter


async def detect_and_translate(
    text: str, token_counter: TokenCounter
) -> Tuple[str, str]:
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
        Detect the language of the following text and translate it to English if it's not already in English.
        Respond in the following format:
        Language: [detected language]
        Translation: [English translation or original text if already in English]

        Text: {text}

        Response:
        """,
    )
    chain = prompt | chat_model
    with get_openai_callback() as cb:
        response = await chain.ainvoke({"text": text})
        token_counter.add_system_tokens(cb.total_tokens)

    lines = response.content.strip().split("\n")
    detected_language = lines[0].split(": ")[1].lower()
    translation = lines[1].split(": ")[1]

    return detected_language, translation


async def translate_text(
    text: str, source_lang: str, target_lang: str, token_counter: TokenCounter
) -> str:
    prompt = PromptTemplate(
        input_variables=["text", "source_lang", "target_lang"],
        template="""
        Translate the following text from {source_lang} to {target_lang}:
        Respond only with translated text, and without warm-up.
        Text: {text}

        Translation:
        """,
    )
    chain = prompt | chat_model
    with get_openai_callback() as cb:
        response = await chain.ainvoke(
            {"text": text, "source_lang": source_lang, "target_lang": target_lang}
        )
        token_counter.add_system_tokens(cb.total_tokens)

    logger.info(f"Response from translation model: {response}")

    return response.content.strip()


async def is_related_to_nz_immigration(query: str, token_counter: TokenCounter) -> bool:
    prompt = PromptTemplate(
        input_variables=["query"],
        template="Determine if the following query is related to New Zealand immigration or visas. Respond with only one word: 'Yes' or 'No'.\n\nQuery: {query}\n\nIs this related to New Zealand immigration or visas?",
    )
    chain = prompt | chat_model
    with get_openai_callback() as cb:
        response = await chain.ainvoke({"query": query})
        token_counter.add_system_tokens(cb.total_tokens)

    logger.info(f"Response from related query model: {response.content}")

    return "yes" in response.content.strip().lower()


async def generate_generic_response(query: str, token_counter: TokenCounter) -> str:
    prompt = PromptTemplate(
        input_variables=["query"],
        template="The following query is not related to New Zealand immigration or visas. Generate a polite response explaining that this bot specializes in New Zealand immigration and visa information, and cannot assist with this query.\n\nQuery: {query}\n\nResponse:",
    )
    chain = prompt | chat_model
    with get_openai_callback() as cb:
        response = await chain.ainvoke({"query": query})
        token_counter.add_system_tokens(cb.total_tokens)

    return response.content


async def prepare_search_query(query: str, token_counter: TokenCounter) -> str:
    prompt = PromptTemplate(
        input_variables=["query"],
        template="Given the following user query about New Zealand immigration or visas, rephrase it and make more good for searching. Respond only with reprhased query, and without warming-up. :\n\nUser Query: {query}\n\nSearch Query:",
    )
    chain = prompt | chat_model
    with get_openai_callback() as cb:
        response = await chain.ainvoke({"query": query})
        token_counter.add_system_tokens(cb.total_tokens)

    return response.content


async def call_llm(prompt: str, token_counter: TokenCounter) -> str:
    with get_openai_callback() as cb:
        response = chat_model([HumanMessage(content=prompt)])
        token_counter.add_main_prompt_tokens(cb.prompt_tokens)
        token_counter.add_output_tokens(cb.completion_tokens)

    return response.content


def format_search_results(search_results: List[dict]) -> str:
    formatted_results = ""
    for result in search_results:
        formatted_results += f"- **{result['header']}**\n  {result['main_content']}\n  URL: {result['url']}\n\n"
    return formatted_results.strip()


def build_prompt(query: str, search_results: List[dict]) -> str:
    prompt_template = PromptTemplate(
        input_variables=["query", "context"],
        template="""
        You are an AI assistant specializing in answering questions about New Zealand visas. Your knowledge comes from official New Zealand immigration information. You will be provided with context from relevant articles and a specific question to answer.

        First, review the following context:

        <context>
        {context}
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
        """,
    )
    context = format_search_results(search_results)
    return prompt_template.format(query=query, context=context)


def extract_answer(response: str) -> str:
    match = re.search(r"<answer>(.*?)</answer>", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return response.strip()
