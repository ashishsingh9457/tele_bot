import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    welcome_text = (
        "👋 Hello! I'm your personal assistant bot!\n\n"
        "Here's what I can do:\n"
        "/time - Show current time\n"
        "/date - Show today's date\n"
        "/help - Show all available commands"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message with all available commands."""
    help_text = (
        "🤖 *Available Commands* 🤖\n\n"
        "/start - Start the bot and see welcome message\n"
        "/time - Show current time\n"
        "/date - Show today's date\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with the current time."""
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"🕒 The current time is: {current_time}")

async def show_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with today's date."""
    from datetime import datetime
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    await update.message.reply_text(f"📅 Today's date is: {current_date}")

def main():
    """Start the bot."""
    if not TOKEN or TOKEN == "YOUR_ACTUAL_BOT_TOKEN_HERE":
        print("Error: Please set your TELEGRAM_BOT_TOKEN in the .env file.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # On different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("time", show_time))
    application.add_handler(CommandHandler("date", show_date))

    # Run the bot until the user presses Ctrl-C
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
