from telegram import Update
from telegram.ext import ContextTypes


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message with all available commands."""
    help_text = (
        "🤖 *Available Commands* 🤖\n\n"
        "/start - Start the bot and see welcome message\n"
        "/terabox <url> - Extract MP4 files from Terabox links\n"
        "/terabox <url> download - Download and send MP4 files (max 50MB)\n"
        "/time - Show current time\n"
        "/date - Show today's date\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')
