from discord.ext import commands
import discord

from tasks import delete_tasks_by_number, add_tasks_to_list, clear_task_list
from config import INPUT_CHANNEL_ID


def setup_handlers(bot: commands.Bot):
    @bot.event
    async def on_message(message: discord.Message):
        # Ignore messages from the bot itself or from the wrong channel
        if message.author == bot.user or message.channel.id != INPUT_CHANNEL_ID:
            return

        content = message.content.strip()

        # Warn users if they don't follow command formatting
        if not content.startswith(".") and not content.lower().startswith(("add", "del", ">clear_hvb_to_do")):
            await message.channel.send(
                "⚠️ Please start your message with a period (.)",
                delete_after=5
            )
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            return

        # Handle deleting tasks: "del 1 2 3"
        if content.lower().startswith("del "):
            try:
                numbers = [int(n) for n in content[4:].split()]
                await delete_tasks_by_number(bot, numbers, message.channel)
            except ValueError:
                await message.channel.send("❌ Please provide valid task numbers to delete.", delete_after=5)

        # Handle adding tasks: "add task1\ntask2"
        elif content.lower().startswith("add"):
            task_lines = [line.strip() for line in content[3:].strip().split("\n") if line.strip()]
            if task_lines:
                await add_tasks_to_list(bot, task_lines, message.channel)
            else:
                await message.channel.send("⚠️ No tasks provided to add.", delete_after=5)

            # Try to delete original message to keep channel clean
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass

        # Handle clearing task list
        elif content.lower() == ">clear_hvb_to_do":
            await clear_task_list(bot)

        # Allow other command processing
        await bot.process_commands(message)
