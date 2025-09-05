import os
import json
import threading
import asyncio
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app to keep bot alive (for platforms like Replit, etc.)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

# Start Flask server in separate thread
threading.Thread(target=run_flask, daemon=True).start()

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Global Variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
INPUT_CHANNEL_ID = int(os.getenv('INPUT_CHANNEL_ID'))
STORAGE_CHANNEL_ID = int(os.getenv('STORAGE_CHANNEL_ID'))

tasks = []
task_message = None
storage_message = None

# Helper Functions
async def save_data():
    global storage_message
    storage_channel = bot.get_channel(STORAGE_CHANNEL_ID)
    if not storage_channel:
        print("Storage channel not found!")
        return

    data_text = json.dumps(tasks)

    if storage_message:
        try:
            await storage_message.edit(content=f"```json\n{data_text}\n```")
        except discord.errors.NotFound:
            print("Storage message not found. Creating new.")
            storage_message = await storage_channel.send(f"```json\n{data_text}\n```")
    else:
        storage_message = await storage_channel.send(f"```json\n{data_text}\n```")

async def load_data():
    global tasks, storage_message
    storage_channel = bot.get_channel(STORAGE_CHANNEL_ID)
    if not storage_channel:
        print("Storage channel not found!")
        return

    async for message in storage_channel.history(limit=1):
        storage_message = message
        try:
            content = message.content.strip("```json\n")
            tasks = json.loads(content)
            if not isinstance(tasks, list):
                tasks = []
        except Exception as e:
            print(f"Error loading tasks: {e}")
            tasks = []
            await create_new_storage_message()

async def create_new_storage_message():
    global storage_message
    storage_channel = bot.get_channel(STORAGE_CHANNEL_ID)
    if storage_channel:
        storage_message = await storage_channel.send("```json\n[]\n```")

async def find_task_message():
    global task_message
    input_channel = bot.get_channel(INPUT_CHANNEL_ID)
    if not input_channel:
        print("Input channel not found!")
        return

    async for message in input_channel.history(limit=50):
        if message.author == bot.user and message.content.startswith("1. "):
            task_message = message
            print("Found existing task list.")
            return

# Events
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await load_data()
    await find_task_message()

@bot.event
async def on_message(message):
    global tasks, task_message, storage_message

    if message.author == bot.user or message.channel.id != INPUT_CHANNEL_ID:
        return

    content = message.content.strip()

    if not content.startswith(".") and not content.lower().startswith(("add", "del", ">clear_hvb_to_do")):
        warning = await message.channel.send(
            "⚠️ Please start your message with a period (.)",
            delete_after=5
        )
        try:
            await message.delete()
        except discord.errors.NotFound:
            pass
        return

    if content.lower().startswith("del "):
        try:
            numbers_to_delete = [int(num) for num in content[4:].strip().split()]
            for number in numbers_to_delete:
                if 1 <= number <= len(tasks):
                    task_text = tasks[number - 1]
                    if task_text.startswith("~~") and task_text.endswith("~~"):
                        await message.channel.send(f"Task {number} already deleted.", delete_after=5)
                    else:
                        tasks[number - 1] = f"~~{task_text}~~ ✅"
                else:
                    await message.channel.send(f"Invalid task number: {number}", delete_after=5)
                    return

            task_list_text = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
            if task_message:
                await task_message.edit(content=task_list_text)

            await save_data()

        except ValueError:
            await message.channel.send("❌ Invalid format! Use: `del <number1> <number2> ...`", delete_after=5)

        try:
            await message.delete()
        except discord.errors.NotFound:
            pass

    elif content.lower().startswith("add"):
        new_tasks = [line.strip() for line in content[3:].strip().split("\n") if line.strip()]
        tasks.extend(new_tasks)

        task_list_text = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
        if task_message:
            await task_message.edit(content=task_list_text)
        else:
            task_message = await message.channel.send(task_list_text)

        try:
            await message.delete()
        except discord.errors.NotFound:
            pass

        await save_data()

    elif content.lower() == ">clear_hvb_to_do":
        input_channel = bot.get_channel(INPUT_CHANNEL_ID)
        storage_channel = bot.get_channel(STORAGE_CHANNEL_ID)

        if not input_channel or not storage_channel:
            print("Input or Storage channel not found!")
            return

        # Backup tasks
        backup_text = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
        await storage_channel.send(f"📦 Backup before clearing:\n```txt\n{backup_text}\n```")

        if storage_message:
            await storage_message.delete()

        # Clear task list
        tasks.clear()

        # Bulk delete all messages (faster)
        try:
            deleted = await input_channel.purge(limit=None)
            print(f"Deleted {len(deleted)} messages.")
        except Exception as e:
            print(f"Error during purge: {e}")

        # Send empty task list message
        task_message = await input_channel.send("📜 Task list is currently empty.")

        await save_data()

        print("Successfully cleared the task list.")

    await bot.process_commands(message)

# Run the bot
bot.run(TOKEN)
