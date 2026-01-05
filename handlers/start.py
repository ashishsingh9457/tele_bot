from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    welcome_text = (
        "👋 Hello! I'm your personal assistant bot!\n\n"
        "Here's what I can do:\n"
        "/terabox <url> - Download and send MP4 files from Terabox\n"
        "/terabox <url> list - Just show file links without downloading\n"
        "/time - Show current time\n"
        "/date - Show today's date\n"
        "/help - Show all available commands"
    )
    await update.message.reply_text(welcome_text)
