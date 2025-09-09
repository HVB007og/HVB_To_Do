import asyncio
import sys
import subprocess
from main import main
from config import PORT

def run_bot_and_server():
    """Starts the Gunicorn server as a subprocess and then runs the bot."""
    # Command to start Gunicorn
    # It will run the Flask app defined in the 'app.py' file
    # Render provides a PORT environment variable that the web service must bind to.
    gunicorn_command = ["gunicorn", "app:app", "--bind", f"0.0.0.0:{PORT}"]

    print("Starting Gunicorn server...", flush=True)
    # Start Gunicorn as a background process
    # Redirect stdout and stderr to the parent's streams to see its output in logs
    gunicorn_process = subprocess.Popen(
        gunicorn_command,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    print("Starting Discord bot...", flush=True)
    # On Windows, the default event loop policy can sometimes cause issues
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down bot and server...", flush=True)
    finally:
        gunicorn_process.terminate() # Ensure Gunicorn is stopped when the bot stops

if __name__ == "__main__":
    run_bot_and_server()