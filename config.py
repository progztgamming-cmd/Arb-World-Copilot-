import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.3-70b-versatile")

ASK_CHANNEL_ID = int(os.getenv("ASK_CHANNEL_ID", "1528325597363961946"))
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID", "1534182485502464071"))
CREW_CHAT_CHANNEL_ID = int(os.getenv("CREW_CHAT_CHANNEL_ID", "1527338458668990514"))
BOTS_COMMANDS_CHANNEL_ID = int(os.getenv("BOTS_COMMANDS_CHANNEL_ID", "1484892482914357381"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", "1534179066775732286"))

ASK_MESSAGE_LIFETIME_SECONDS = int(os.getenv("ASK_MESSAGE_LIFETIME_SECONDS", "180"))
ASK_CLEANUP_INTERVAL_SECONDS = int(os.getenv("ASK_CLEANUP_INTERVAL_SECONDS", "45"))

SYSTEM_DOCS_PATH = BASE_DIR / "data" / "arb_world_official_docs.txt"

EXEMPT_ROLE_NAMES = {
    "Administrator",
    "Moderator",
    "The fastest man alive - Head",
}

BAD_WORDS = {
    "fuck",
    "shit",
    "bitch",
    "asshole",
    "idiot",
    "stupid",
    "كلب",
    "حمار",
    "غبي",
    "وسخ",
    "زفت",
    "خرا",
}
