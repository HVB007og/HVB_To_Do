import discord
from discord.ext import commands
import json
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Channel IDs
input_channel_id = 1365690115808039153   # channel where users send checklist
storage_channel_id = 1365699587377201173  # channel where hidden JSON is stored

# Data
tasks = []
storage_message = None
task_message = None  # 🆕 This will store the "master list" message

async def save_data():
    global storage_message
    storage_channel = bot.get_channel(storage_channel_id)

    if not storage_channel:
        print("Storage channel not found!")
        return

    data_text = json.dumps(tasks)

    if storage_message:
        try:
            # Attempt to edit the existing storage message
            await storage_message.edit(content=f"```json\n{data_text}\n```")
        except discord.errors.NotFound:
            # If the message was deleted, create a new one
            print("Storage message not found, creating a new one.")
            storage_message = await storage_channel.send(f"```json\n{data_text}\n```")
    else:
        # If no storage message exists, create a new one
        storage_message = await storage_channel.send(f"```json\n{data_text}\n```")


async def load_data():
    global storage_message, tasks
    storage_channel = bot.get_channel(storage_channel_id)

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
            # If data loading fails, create a new task list and send it
            tasks = []  # Clear the tasks list
            await create_new_storage_message()  # Create a new storage message with the empty list

async def create_new_storage_message():
    global storage_message
    storage_channel = bot.get_channel(storage_channel_id)

    if not storage_channel:
        print("Storage channel not found!")
        return

    # Send a new message with an empty task list
    storage_message = await storage_channel.send("```json\n[]\n```")


async def find_task_message():
    global task_message
    input_channel = bot.get_channel(input_channel_id)
    if not input_channel:
        print("Input channel not found!")
        return

    async for message in input_channel.history(limit=50):  # scan last 50 messages
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

    if message.channel.id != input_channel_id:
        return

    global tasks, task_message, storage_message

    content = message.content.strip()

    # ⚡ If message does NOT start with '.', delete it and warn
    if not content.startswith(".") and not content.lower().startswith(("del ", "add", ">clear_hvb_to_do")):
        await message.delete()
        warning = await message.channel.send(
            "⚠️ Invalid input! Please start your message with a period (.)",
            delete_after=5
        )
        return

    if content.lower().startswith("del "):
        # (deletion logic stays the same)
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
        # (addition logic stays the same)
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
        # (improved clearing logic)
        backup_channel = bot.get_channel(storage_channel_id)

        if not backup_channel:
            print("Storage channel not found!")
            return

        # Backup the current list
        backup_text = "\n".join(f"{i + 1}. {task}" for i, task in enumerate(tasks))
        await backup_channel.send(f"Backup of tasks before clearing:\n```txt\n{backup_text}\n```")

        # Delete old storage message
        if storage_message:
            await storage_message.delete()

        tasks.clear()

        # Delete all messages from input channel (users + bot messages)
        input_channel = bot.get_channel(input_channel_id)
        if input_channel:
            async for msg in input_channel.history(limit=None):
                try:
                    await msg.delete()
                except:
                    pass

        # After clearing, send a new message "Task list is currently empty."
        task_message = await input_channel.send("📜 Task list is currently empty.")

        await save_data()

    else:
        # Ignore anything else
        return

    # Allow commands still
    await bot.process_commands(message)

# Start the bot
bot.run("MTM2NTY5NzM4NDEyNTk1NjA5Ng.GK22hW.vvGIhU35UZpJAsM2Bl5LFWNhwjGN_OS1KCmYnU")

