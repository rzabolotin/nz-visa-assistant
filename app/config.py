import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db/botdb")
SENTENCE_TRANSFORMERS_MODEL = os.getenv("SENTENCE_TRANSFORMERS_MODEL")
ELASTIC_URL = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
ELASTIC_INDEX_NAME = os.getenv("ELASTIC_INDEX_NAME", "my_index")
DATA_FILE_PATH = os.getenv("DATA_FILE_PATH", "data/site_content.json")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-haiku-20240307")
