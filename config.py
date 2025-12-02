"""Configuration management for the bot."""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

# Bot Settings
MAX_RECENT_MESSAGES = 300
MAX_USER_MESSAGES = 50
CONTEXT_WINDOW_SIZE = 15
DEFAULT_AI_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7

# Web Search Settings
ENABLE_WEB_SEARCH = True
MAX_SEARCH_RESULTS = 5

# Sticker Settings
ENABLE_STICKERS = True
STICKER_CHANCE = 0.15  # 15% chance to send a sticker
STICKER_SET_NAME = "SHREK.PACK"  # Default sticker set name

# Logging Configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

