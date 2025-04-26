from flask import Flask
import threading
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Start Flask in a separate thread so that the bot can still run
threading.Thread(target=run_flask).start()

# Fetch the token and channel IDs from environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
INPUT_CHANNEL_ID = int(os.getenv('INPUT_CHANNEL_ID'))
STORAGE_CHANNEL_ID = int(os.getenv('STORAGE_CHANNEL_ID'))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Data
tasks = []
storage_message = None
task_message = None

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
            print("Storage message not found, creating a new one.")
            storage_message = await storage_channel.send(f"```json\n{data_text}\n```")
    else:
        storage_message = await storage_channel.send(f"```json\n{data_text}\n```")

async def load_data():
    global storage_message, tasks
    storage_channel = bot.get_channel(STORAGE_CHANNEL_ID)

    if not storage_channel:
        print("Storage channel not found!")
        return

    async for message in storage_channel.history(limit=1):
        storage_message = message
        try:
            content = message.content.strip("```json\n")
            loaded_data = json.loads(content)
            if isinstance(loaded_data, list):
                tasks = loaded_data
            else:
                tasks = []
        except Exception as e:
            print(f"Failed to load data: {e}")
            tasks = []
            await create_new_storage_message()

async def create_new_storage_message():
    global storage_message
    storage_channel = bot.get_channel(STORAGE_CHANNEL_ID)

    if not storage_channel:
        print("Storage channel not found!")
        return

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
            print("Found existing task list message.")
            return

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await load_data()
    await find_task_message()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id != INPUT_CHANNEL_ID:
        return

    global tasks, task_message, storage_message

    content = message.content.strip()

    if not content.startswith(".") and not content.lower().startswith(("del ", "add", ">clear_hvb_to_do")):
        await message.delete()
        warning = await message.channel.send(
            "⚠️ Invalid input! Please start your message with a period (.)",
            delete_after=5
        )
        return

    if content.lower().startswith("del "):
        try:
            numbers_to_delete = [int(num) for num in content[4:].strip().split()]

            for number in numbers_to_delete:
                if 1 <= number <= len(tasks):
                    task_text = tasks[number - 1]

                    if task_text.startswith("~~") and task_text.endswith("~~"):
                        await message.channel.send(f"Task {number} is already deleted or completed!", delete_after=5)
                    else:
                        tasks[number - 1] = f"~~{task_text}~~ ✅"
                else:
                    await message.channel.send(f"Invalid task number: {number}", delete_after=5)
                    return

            task_list_text = "\n".join(f"{i + 1}. {task}" for i, task in enumerate(tasks))

            if task_message:
                await task_message.edit(content=task_list_text)

            await save_data()

        except ValueError:
            await message.channel.send("Invalid format! Use `del <number1> <number2> ...`.", delete_after=5)

        await message.delete()

    elif content.lower().startswith("add"):
        new_content = content[3:].strip()

        lines = [line.strip() for line in new_content.split("\n") if line.strip()]
        tasks.extend(lines)

        task_list_text = "\n".join(f"{i + 1}. {task}" for i, task in enumerate(tasks))

        if task_message:
            await task_message.edit(content=task_list_text)
        else:
            task_message = await message.channel.send(task_list_text)

        await message.delete()
        await save_data()

    elif content.lower() == ">clear_hvb_to_do":
        backup_channel = bot.get_channel(STORAGE_CHANNEL_ID)

        if not backup_channel:
            print("Storage channel not found!")
            return

        backup_text = "\n".join(f"{i + 1}. {task}" for i, task in enumerate(tasks))
        await backup_channel.send(f"Backup of tasks before clearing:\n```txt\n{backup_text}\n```")

        if storage_message:
            await storage_message.delete()

        tasks.clear()

        input_channel = bot.get_channel(INPUT_CHANNEL_ID)
        if input_channel:
            async for msg in input_channel.history(limit=None):
                try:
                    await msg.delete()
                except:
                    pass

        task_message = await input_channel.send("📜 Task list is currently empty.")
        await save_data()

    else:
        return

    await bot.process_commands(message)

# Start the bot
bot.run(TOKEN)
