import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ELASTIC_URL = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db/botdb")
