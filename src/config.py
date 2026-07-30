import os
from dotenv import load_dotenv

load_dotenv()

# Cấu hình Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

# Cấu hình OpenAI / LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Cấu hình RAG
try:
    TOP_K = int(os.getenv("TOP_K", "5"))
except ValueError:
    TOP_K = 5
