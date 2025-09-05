import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
INPUT_CHANNEL_ID = int(os.getenv("INPUT_CHANNEL_ID"))
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID"))
PORT = int(os.getenv("PORT", 8080))
