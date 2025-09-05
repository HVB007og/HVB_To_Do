import asyncio
from keep_alive import run_flask
from config import TOKEN
import discord
from discord.ext import commands

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def main():
    from cogs.task_cog import TaskCog
    async with bot:
        await bot.add_cog(TaskCog(bot))
        await bot.start(TOKEN)
