import logging
from telegram import Update
from telegram.ext import ContextTypes

from .download import download_and_send_file
from .terabox_direct_v2 import get_terabox_download_direct, is_valid_terabox_url

logger = logging.getLogger(__name__)


async def terabox_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Terabox URL and extract/download MP4 files."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a Terabox URL.\n\n"
            "Usage: /terabox <url>\n"
            "Example: /terabox https://terabox.app/wap/share/filelist?surl=xxxxx\n\n"
            "Files will be downloaded and sent automatically.\n"
            "Add 'list' to only show links: /terabox <url> list"
        )
        return

    url = context.args[0]
    # Download by default, unless user specifies 'list' to just show links
    should_download = True
    if len(context.args) > 1 and context.args[1].lower() == 'list':
        should_download = False
    
    if not is_valid_terabox_url(url):
        await update.message.reply_text(
            "❌ Invalid Terabox URL.\n\n"
            "Please provide a valid Terabox share link."
        )
        return

    status_msg = await update.message.reply_text("🔍 Processing Terabox URL... Please wait.")

    try:
        # Use direct API method (works with residential IP)
        logger.info(f"Fetching download link for: {url}")
        logger.info("Using direct API method...")
        
        await status_msg.edit_text("🔍 Processing Terabox URL...\n\n⏳ Extracting download link...")
        
        file_data = get_terabox_download_direct(url)
        
        if not file_data or not file_data.get('url'):
            await status_msg.edit_text(
                "❌ Could not extract download link from this Terabox URL.\n\n"
                "Please make sure:\n"
                "• The link is valid and accessible\n"
                "• The file is not password protected\n"
                "• The file is a video (MP4)"
            )
            return

        # Prepare file info for display/download
        file_info = {
            'name': file_data.get('file_name', 'video.mp4'),
            'url': file_data.get('url'),
            'size': file_data.get('size', 'Unknown'),
        }
        
        logger.info(f"Successfully extracted: {file_info['name']}, size: {file_info['size']}")

        # Display found file
        response = "✅ *Found MP4 File:*\n\n"
        response += f"📁 `{file_info['name']}`\n"
        response += f"📊 Size: {file_info['size']}\n"
        
        if not should_download:
            response += f"🔗 Link: {file_info['url']}\n"
            response += "\n💡 *Tip:* Remove 'list' to download files automatically."
            await status_msg.edit_text(response, parse_mode='Markdown')
        else:
            response += "\n⏬ Downloading and sending..."
            await status_msg.edit_text(response, parse_mode='Markdown')
            
            # Download and send file
            await download_and_send_file(update, file_info, 1, 1)

    except Exception as e:
        logger.error(f"Error in terabox_handler: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ Error processing Terabox URL:\n{str(e)}\n\n"
            "Please make sure the link is accessible and try again."
        )
