# HVB To-Do Bot

A simple and efficient Discord bot for managing a collaborative shopping or to-do list within a specific text channel. The bot uses a persistent storage method by saving the task list to a designated private channel, ensuring data is not lost on restart.

## Features

- **Add Tasks**: Quickly add single or multiple tasks to the list.
- **Complete Tasks**: Mark tasks as completed with a simple command.
- **Clear List**: Securely clear the entire task list with a backup mechanism.
- **Persistent Storage**: Uses a secondary Discord channel to store the task list, making it robust and easy to manage.
- **Clean Interface**: Automatically deletes user commands to keep the to-do list channel clean and readable.

## How It Works

The bot operates primarily in a designated "input" channel. It maintains a single message that it continuously edits to reflect the current state of the to-do list.

- **Data Persistence**: The task list (as a JSON array) is saved in a message within a separate, private "storage" channel. The bot loads from and saves to this message.
- **Command Handling**: The bot listens for messages in the input channel and processes them based on specific prefixes.

## Commands

All commands are sent in the designated input channel.

### Chat in the Channel 
To send a normal message that is not a command, simply start it with a period (.). The bot will ignore it, allowing for conversation. 
```
. Hey everyone, are we out of electrical tape?
```

### Add Tasks
Use the `add` prefix to add one or more tasks. For multiple tasks, place each on a new line.
```
add flux
Buy wires
```

### Complete a Task
Use the `del` prefix followed by the task number(s) you want to mark as complete.
```
del 2
```
```
del 1 3 5
```

### Clear the Entire List
To clear all tasks, purge the channel, and create a backup.
```
>clear_hvb_to_do
```

## Setup

1.  **Clone the repository.**
2.  **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```
3.  **Create a `.env` file** in the root directory and add your configuration details:
    ```env
    DISCORD_BOT_TOKEN="your_bot_token_here"
    INPUT_CHANNEL_ID="your_target_channel_id_for_the_list"
    STORAGE_CHANNEL_ID="your_private_storage_channel_id"
    ```
4.  **Run the bot**:
    ```sh
    python run.py
    ```