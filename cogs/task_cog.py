import json
import discord
from discord.ext import commands
from config import INPUT_CHANNEL_ID, STORAGE_CHANNEL_ID

def format_task_list(tasks):
    """Formats the list of tasks into a string for Discord."""
    if not tasks:
        return "📜 Task list is currently empty."
    return "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))

class TaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tasks = []
        self.task_message = None
        self.storage_message = None

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        print(f"Logged in as {self.bot.user}", flush=True)
        await self._load_data()
        await self._find_task_message()
        print("✅ Bot is ready and data is loaded.", flush=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle incoming messages for task management."""
        if message.author == self.bot.user or message.channel.id != INPUT_CHANNEL_ID:
            return

        content = message.content.strip()

        # Command-like processing
        if content.lower().startswith("del "):
            try:
                numbers = [int(n) for n in content[4:].split()]
                await self._delete_tasks(numbers, message.channel)
            except ValueError:
                await message.channel.send("❌ Please provide valid task numbers to delete.", delete_after=5)
            finally:
                await message.delete()

        elif content.lower().startswith("add "):
            task_lines = [line.strip() for line in content[4:].strip().split("\n") if line.strip()]
            if task_lines:
                await self._add_tasks(task_lines, message.channel)
            else:
                await message.channel.send("⚠️ No tasks provided to add.", delete_after=5)
            await message.delete()

        elif content.lower() == ">clear_hvb_to_do":
            await self._clear_tasks()
            await message.delete()
        
        # If the message is not a valid command or a chat message, delete it and warn the user.
        else:
            # A message is valid if it's for chat or is a known command. Otherwise, it's invalid.
            is_chat = content.startswith('.')
            is_known_command = content.lower().startswith(('add ', 'del ', '>clear_hvb_to_do'))

            if not is_chat and not is_known_command:
                await message.channel.send(
                    "⚠️ Please start your message with a period (.) to chat, or `add`/`del` to interact with the list.",
                    delete_after=10
                )
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass # Message was already deleted, which is fine.

    async def _update_task_message(self, channel: discord.TextChannel):
        """Edit the existing task message or send a new one."""
        content = format_task_list(self.tasks)
        if self.task_message:
            try:
                await self.task_message.edit(content=content)
            except discord.errors.NotFound:
                self.task_message = await channel.send(content)
        else:
            self.task_message = await channel.send(content)

    async def _add_tasks(self, new_tasks, channel):
        """Add new tasks to the list."""
        self.tasks.extend(new_tasks)
        await self._update_task_message(channel)
        await self._save_data()

    async def _delete_tasks(self, numbers, channel):
        """Mark tasks as completed."""
        for number in sorted(list(set(numbers)), reverse=True): # Process in reverse to avoid index shifts
            if 1 <= number <= len(self.tasks):
                task_text = self.tasks[number - 1]
                if not task_text.startswith("~~"):
                    self.tasks[number - 1] = f"~~{task_text}~~ ✅"
                else:
                    await channel.send(f"⚠️ Task {number} is already marked as done.", delete_after=5)
            else:
                await channel.send(f"❌ Invalid task number: {number}", delete_after=5)
        
        await self._update_task_message(channel)
        await self._save_data()

    async def _clear_tasks(self):
        """Clear the entire task list."""
        input_channel = self.bot.get_channel(INPUT_CHANNEL_ID)
        storage_channel = self.bot.get_channel(STORAGE_CHANNEL_ID)
        if not input_channel or not storage_channel:
            return

        if self.tasks:
            backup = format_task_list(self.tasks)
            await storage_channel.send(f"📦 Backup before clearing:\n```txt\n{backup}\n```")

        self.tasks.clear()
        await input_channel.purge(limit=100) # Purge messages
        self.task_message = None # Reset message reference
        await self._update_task_message(input_channel)
        await self._save_data()

    async def _find_task_message(self):
        """Find the existing task list message on startup."""
        channel = self.bot.get_channel(INPUT_CHANNEL_ID)
        if not channel:
            print("❌ Input channel not found!", flush=True)
            return
        async for message in channel.history(limit=50):
            if message.author == self.bot.user and (message.content.startswith("1. ") or "Task list is currently empty" in message.content):
                self.task_message = message
                print("✅ Found existing task list message.", flush=True)
                return

    async def _load_data(self):
        """Load tasks from the storage channel."""
        channel = self.bot.get_channel(STORAGE_CHANNEL_ID)
        if not channel:
            print("❌ Storage channel not found!", flush=True)
            return
        async for message in channel.history(limit=1):
            self.storage_message = message
            try:
                # Extract JSON from the code block
                content = message.content.strip("` \n").removeprefix("json\n")
                data = json.loads(content)
                if isinstance(data, list):
                    self.tasks = data
                else:
                    self.tasks = []
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"⚠️ Could not load or parse tasks: {e}. Starting fresh.", flush=True)
                self.tasks = []
            return # We only care about the most recent message

        # If no message was found, we start with an empty list
        print("No storage message found. Starting with an empty task list.", flush=True)
        self.tasks = []

    async def _save_data(self):
        """Save the current tasks to the storage channel."""
        channel = self.bot.get_channel(STORAGE_CHANNEL_ID)
        if not channel:
            print("❌ Storage channel not found!", flush=True)
            return

        data_text = json.dumps(self.tasks, indent=2)
        content = f"```json\n{data_text}\n```"

        try:
            if self.storage_message:
                await self.storage_message.edit(content=content)
            else:
                self.storage_message = await channel.send(content)
        except discord.errors.NotFound:
            print("Storage message was deleted. Creating a new one.", flush=True)
            self.storage_message = await channel.send(content)