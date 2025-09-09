from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    """Keep-alive endpoint for Render."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Ping received at {timestamp}. Service is active.", flush=True)
    return "Bot is running and active."
