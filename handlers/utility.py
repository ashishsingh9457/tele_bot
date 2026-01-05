from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes


async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with the current time."""
    current_time = datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"🕒 The current time is: {current_time}")


async def show_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with today's date."""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    await update.message.reply_text(f"📅 Today's date is: {current_date}")
