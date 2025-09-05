import discord
from discord.ext import commands
from config import INPUT_CHANNEL_ID, STORAGE_CHANNEL_ID
import json


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

async def load_data(bot):
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
