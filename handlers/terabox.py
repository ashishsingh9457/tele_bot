import re
import httpx
from telegram import Update
from telegram.ext import ContextTypes


async def terabox_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Terabox URL and extract MP4 files."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a Terabox URL.\n\n"
            "Usage: /terabox <url>\n"
            "Example: /terabox https://terabox.com/s/xxxxx"
        )
        return

    url = context.args[0]
    
    if not is_valid_terabox_url(url):
        await update.message.reply_text(
            "❌ Invalid Terabox URL.\n\n"
            "Please provide a valid Terabox share link."
        )
        return

    await update.message.reply_text("🔍 Processing Terabox URL... Please wait.")

    try:
        mp4_files = await extract_mp4_files(url)
        
        if not mp4_files:
            await update.message.reply_text(
                "❌ No MP4 files found in this Terabox link."
            )
            return

        response = "✅ *Found MP4 Files:*\n\n"
        for idx, file_info in enumerate(mp4_files, 1):
            response += f"{idx}. `{file_info['name']}`\n"
            response += f"   Size: {file_info['size']}\n"
            response += f"   Link: {file_info['url']}\n\n"

        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error processing Terabox URL:\n{str(e)}\n\n"
            "Please make sure the link is accessible and try again."
        )


def is_valid_terabox_url(url: str) -> bool:
    """Validate if the URL is a Terabox share link."""
    terabox_patterns = [
        r'https?://(?:www\.)?terabox\.com/s/\w+',
        r'https?://(?:www\.)?1024terabox\.com/s/\w+',
        r'https?://(?:www\.)?teraboxapp\.com/s/\w+',
    ]
    return any(re.match(pattern, url) for pattern in terabox_patterns)


async def extract_mp4_files(url: str) -> list:
    """
    Extract MP4 files from Terabox URL.
    
    Note: Terabox has anti-scraping measures. This is a basic implementation
    that may need to be enhanced with:
    - User-Agent rotation
    - Cookie handling
    - JavaScript rendering (using playwright/selenium)
    - API reverse engineering
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.terabox.com/',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

            mp4_files = []
            
            # Pattern 1: Look for direct MP4 links in the HTML
            mp4_pattern = r'https?://[^\s<>"]+\.mp4[^\s<>"]*'
            mp4_urls = re.findall(mp4_pattern, html_content)
            
            for mp4_url in set(mp4_urls):
                mp4_files.append({
                    'name': extract_filename_from_url(mp4_url),
                    'url': mp4_url,
                    'size': 'Unknown'
                })

            # Pattern 2: Look for JSON data that might contain file information
            json_pattern = r'window\.jsToken\s*=\s*({[^}]+})'
            json_matches = re.findall(json_pattern, html_content)
            
            # Pattern 3: Look for file list in JavaScript variables
            file_list_pattern = r'file_list":\s*\[([^\]]+)\]'
            file_list_matches = re.findall(file_list_pattern, html_content)

            return mp4_files

        except httpx.HTTPError as e:
            raise Exception(f"HTTP error occurred: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to fetch Terabox content: {str(e)}")


def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL."""
    parts = url.split('/')
    filename = parts[-1].split('?')[0]
    return filename if filename else 'video.mp4'
