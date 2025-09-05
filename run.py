import asyncio
import sys
from main import main

if __name__ == "__main__":
    # On Windows, the default event loop policy can sometimes cause issues
    # with libraries like discord.py. Setting it explicitly can prevent them.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is shutting down.")