import re
import json
import httpx
import logging
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes
from .download import download_and_send_file
from .terabox_direct import get_file_info_direct

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
        # Use direct Terabox API implementation
        logger.info(f"Fetching download link for: {url}")
        file_data = await get_file_info_direct(url)
        
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


def is_valid_terabox_url(url: str) -> bool:
    """Validate if the URL is a Terabox share link."""
    terabox_patterns = [
        r'https?://(?:www\.)?terabox\.com/s/[\w-]+',
        r'https?://(?:www\.)?terabox\.app/s/[\w-]+',
        r'https?://(?:www\.)?1024terabox\.com/s/[\w-]+',
        r'https?://(?:www\.)?teraboxapp\.com/s/[\w-]+',
        r'https?://(?:www\.)?terabox\.com/sharing/link\?surl=[\w-]+',
        r'https?://(?:www\.)?terabox\.app/sharing/link\?surl=[\w-]+',
        r'https?://(?:www\.)?terabox\.app/wap/share/filelist\?surl=[\w-]+',
        r'https?://(?:www\.)?terabox\.com/wap/share/filelist\?surl=[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in terabox_patterns)


async def extract_mp4_files(url: str) -> list:
    """
    Extract MP4 files from Terabox URL with robust parsing.
    
    Uses multiple extraction methods:
    1. Direct MP4 URLs from HTML
    2. JSON data embedded in JavaScript
    3. API endpoint reverse engineering
    4. BeautifulSoup HTML parsing
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=60.0) as client:
        try:
            # Fetch the main page
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

            mp4_files = []
            
            # Method 1: Parse with BeautifulSoup for structured data
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 2: Extract JSON data from script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_content = script.string
                if script_content:
                    # Look for file information in various JSON structures
                    json_patterns = [
                        r'window\.jsToken\s*=\s*({.+?});',
                        r'locals\.mset\(({.+?})\);',
                        r'window\.yunData\s*=\s*({.+?});',
                        r'file_list":\s*\[({.+?})\]',
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, script_content, re.DOTALL)
                        for match in matches:
                            try:
                                data = json.loads(match)
                                extracted = extract_files_from_json(data, include_without_dlink=True)
                                mp4_files.extend(extracted)
                            except (json.JSONDecodeError, TypeError):
                                continue
            
            # Method 3: Direct MP4 URL extraction with improved patterns
            mp4_patterns = [
                r'https?://[^\s<>"]+\.mp4(?:\?[^\s<>"]*)?',
                r'"(https?://[^"]+\.mp4[^"]*)"',
                r"'(https?://[^']+\.mp4[^']*)'",
            ]
            
            for pattern in mp4_patterns:
                mp4_urls = re.findall(pattern, html_content)
                for mp4_url in set(mp4_urls):
                    if mp4_url and is_valid_mp4_url(mp4_url):
                        mp4_files.append({
                            'name': extract_filename_from_url(mp4_url),
                            'url': clean_url(mp4_url),
                            'size': 'Unknown'
                        })
            
            # Method 4: Try to extract surl and make API call
            surl_match = re.search(r'surl=([\w-]+)', url)
            if surl_match:
                surl = surl_match.group(1)
                api_files = await fetch_from_api(client, surl, headers)
                mp4_files.extend(api_files)
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_files = []
            for file in mp4_files:
                if file['url'] not in seen_urls:
                    seen_urls.add(file['url'])
                    unique_files.append(file)
            
            return unique_files

        except httpx.HTTPError as e:
            raise Exception(f"HTTP error occurred: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to fetch Terabox content: {str(e)}")


def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL."""
    try:
        parts = url.split('/')
        filename = parts[-1].split('?')[0]
        # Decode URL encoding if present
        from urllib.parse import unquote
        filename = unquote(filename)
        return filename if filename and filename.endswith('.mp4') else 'video.mp4'
    except Exception:
        return 'video.mp4'


def is_valid_mp4_url(url: str) -> bool:
    """Validate if URL is a proper MP4 link."""
    if not url or len(url) < 10:
        return False
    if not url.startswith('http'):
        return False
    # Exclude common false positives
    exclude_patterns = ['thumbnail', 'preview', 'icon', '.js', '.css', '.png', '.jpg']
    return not any(pattern in url.lower() for pattern in exclude_patterns)


def clean_url(url: str) -> str:
    """Clean and normalize URL."""
    url = url.strip('"\'')
    url = url.replace('\\/', '/')
    return url


def extract_files_from_json(data: dict, include_without_dlink: bool = False) -> list:
    """Extract MP4 files from JSON data structure."""
    files = []
    
    def recursive_search(obj):
        if isinstance(obj, dict):
            # Look for common file info keys in Terabox API response
            has_filename = 'server_filename' in obj or 'filename' in obj or 'path' in obj
            
            if has_filename:
                filename = obj.get('server_filename') or obj.get('filename') or obj.get('path', '')
                # Extract just the filename if it's a path
                if '/' in filename:
                    filename = filename.split('/')[-1]
                
                # Check if it's an MP4 file (case insensitive) and not a directory
                isdir = obj.get('isdir', 0)
                is_mp4 = filename.lower().endswith('.mp4')
                logger.info(f"Checking file: {filename}, isdir: {isdir}, is_mp4: {is_mp4}")
                
                if is_mp4 and isdir == 0:
                    logger.info(f"Passed MP4 check for: {filename}")
                    # Get download link if available
                    download_link = obj.get('dlink') or obj.get('download_url') or obj.get('url', '')
                    
                    logger.info(f"Found MP4: {filename}, has_dlink: {bool(download_link)}, include_without_dlink: {include_without_dlink}")
                    
                    # Add file info (with or without download link depending on flag)
                    if download_link or include_without_dlink:
                        files.append({
                            'name': filename,
                            'url': download_link,
                            'size': format_size(obj.get('size', 0)),
                            'fs_id': obj.get('fs_id', ''),
                            'path': obj.get('path', ''),
                            'share_id': obj.get('share_id', ''),
                            'uk': obj.get('uk', ''),
                            'isdir': isdir
                        })
                        logger.info(f"Added file to list: {filename}")
            
            # Recursively search nested objects
            for value in obj.values():
                recursive_search(value)
        elif isinstance(obj, list):
            for item in obj:
                recursive_search(item)
    
    recursive_search(data)
    
    logger.info(f"Total files extracted: {len(files)}")
    return files


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    try:
        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except (ValueError, TypeError):
        return 'Unknown'


async def fetch_from_api(client: httpx.AsyncClient, surl: str, headers: dict) -> list:
    """Try to fetch file list from Terabox API endpoints."""
    api_endpoints = [
        f'https://www.terabox.app/share/list?shorturl={surl}&root=1',
        f'https://www.terabox.com/share/list?shorturl={surl}&root=1',
    ]
    
    for endpoint in api_endpoints:
        try:
            response = await client.get(endpoint, headers=headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                
                # Log the response for debugging
                logger.info(f"API Response from {endpoint}")
                logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Check if API returned an error
                if isinstance(data, dict):
                    errno = data.get('errno', 0)
                    if errno != 0:
                        logger.warning(f"API returned error code: {errno}")
                        continue
                    
                    # Log list structure
                    if 'list' in data:
                        list_data = data.get('list', [])
                        logger.info(f"Found {len(list_data)} items in list")
                        if list_data and isinstance(list_data, list) and len(list_data) > 0:
                            logger.info(f"First item keys: {list(list_data[0].keys()) if isinstance(list_data[0], dict) else 'Not a dict'}")
                
                # Extract files (including those without dlink)
                files = extract_files_from_json(data, include_without_dlink=True)
                logger.info(f"Extracted {len(files)} MP4 files")
                
                if files:
                    # Fetch download links for files that don't have them
                    share_id = data.get('share_id', '')
                    uk = data.get('uk', '')
                    
                    for file in files:
                        if not file['url'] and file['fs_id']:
                            # Fetch download link
                            dlink = await fetch_download_link(client, file['fs_id'], share_id, uk, surl, headers)
                            if dlink:
                                file['url'] = dlink
                                logger.info(f"Fetched download link for {file['name']}")
                    
                    # Filter out files without download links
                    files_with_links = [f for f in files if f['url']]
                    logger.info(f"Files with download links: {len(files_with_links)}")
                    
                    if files_with_links:
                        return files_with_links
        except Exception as e:
            logger.error(f"Error fetching from API {endpoint}: {e}")
            continue
    
    return []
