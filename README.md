# Telegram "Hello World" Bot

A simple Telegram bot built with Python and `python-telegram-bot`.

## Prerequisites

1.  **Python 3.8+**
2.  **Telegram Account**
3.  **Bot Token**: Get one from [@BotFather](https://t.me/botfather) by sending `/newbot`.

## Setup

1.  **Clone/Open this project** in your terminal.
2.  **Create a Virtual Environment** (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\Scripts\activate  # On Windows
    ```
3.  **Install Dependencies**:
    ```bash
    pip install python-telegram-bot python-dotenv
    ```
4.  **Configure Environment Variables**:
    - Open the `.env` file.
    - Replace `YOUR_ACTUAL_BOT_TOKEN_HERE` with the token you got from @BotFather.

## Running the Bot

```bash
python bot.py
```

Once the bot is running, open Telegram and send `/start` to your bot.

## Commands
- `/start`: Returns a "Hello World" greeting.
- `/help`: Returns a help message.
