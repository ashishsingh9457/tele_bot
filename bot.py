from telegram.ext import Application, CommandHandler

from config import TOKEN
from handlers import start, help_command, show_time, show_date

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
    application.run_polling()

if __name__ == "__main__":
    main()
