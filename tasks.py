# tasks.py

import json
import discord
from state import tasks, task_message, storage_message
from config import INPUT_CHANNEL_ID, STORAGE_CHANNEL_ID
from utils.formatting import format_task_list


async def find_task_message(bot):
    """Find the existing task list message in the input channel."""
    global task_message
    input_channel = bot.get_channel(INPUT_CHANNEL_ID)

    if not input_channel:
        print("❌ Input channel not found!")
        return

    async for message in input_channel.history(limit=50):
        if message.author == bot.user and message.content.startswith("1. "):
            task_message = message
            print("✅ Found existing task list message.")
            return


async def add_tasks_to_list(bot, new_tasks, channel):
    """Add new tasks to the task list and update the task message."""
    global task_message
    tasks.extend(new_tasks)

    content = format_task_list(tasks)
    if task_message:
        await task_message.edit(content=content)
    else:
        task_message = await channel.send(content)

    await save_data(bot)


async def delete_tasks_by_number(bot, numbers, channel):
    """Soft delete tasks by their number (index), marking them as completed."""
    global task_message
    for number in numbers:
        if 1 <= number <= len(tasks):
            if tasks[number - 1].startswith("~~") and tasks[number - 1].endswith("~~ ✅"):
                await channel.send(f"⚠️ Task {number} already deleted.", delete_after=5)
            else:
                tasks[number - 1] = f"~~{tasks[number - 1]}~~ ✅"
        else:
            await channel.send(f"❌ Invalid task number: {number}", delete_after=5)
            return

    content = format_task_list(tasks)
    if task_message:
        await task_message.edit(content=content)

    await save_data(bot)


async def clear_task_list(bot):
    """Clear the task list, back up old tasks, and delete message history."""
    global tasks, task_message, storage_message
    input_channel = bot.get_channel(INPUT_CHANNEL_ID)
    storage_channel = bot.get_channel(STORAGE_CHANNEL_ID)

    if not input_channel or not storage_channel:
        print("❌ Input or storage channel not found!")
        return

    # Backup
    if tasks:
        backup = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
        await storage_channel.send(f"📦 Backup before clearing:\n```txt\n{backup}\n```")

    if storage_message:
        await storage_message.delete()

    # Clear tasks and purge messages
    tasks.clear()
    try:
        deleted = await input_channel.purge(limit=None)
        print(f"🧹 Cleared {len(deleted)} messages from input channel.")
    except Exception as e:
        print(f"⚠️ Error during purge: {e}")

    # Reset task message
    task_message = await input_channel.send("📜 Task list is currently empty.")
    await save_data(bot)


async def save_data(bot):
    """Update the storage channel with the latest task list in JSON format."""
    global storage_message
    storage_channel = bot.get_channel(STORAGE_CHANNEL_ID)

    if not storage_channel:
        print("❌ Storage channel not found!")
        return

    data_text = json.dumps(tasks, indent=2)

    try:
        if storage_message:
            await storage_message.edit(content=f"```json\n{data_text}\n```")
        else:
            storage_message = await storage_channel.send(f"```json\n{data_text}\n```")
    except discord.errors.NotFound:
        storage_message = await storage_channel.send(f"```json\n{data_text}\n```")
