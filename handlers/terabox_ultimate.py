"""
Ultimate Terabox implementation - combines API for file info with direct download construction.
Since Terabox API blocks download endpoint, we'll use the file info to construct alternative access methods.
"""
import re
import httpx
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def extract_surl(url: str) -> str:
    """Extract surl from Terabox URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    
    if 'surl' in query:
        return query['surl'][0]
    
    match = re.search(r'/s/([^/?\s]+)', url)
    if match:
        return match.group(1)
    
    return ""


async def get_terabox_info(url: str) -> dict:
    """
    Get Terabox file using a hybrid approach:
    1. Use API to get file metadata (this works)
    2. Construct download URL that bypasses verification
    """
    try:
        surl = extract_surl(url)
        if not surl:
            logger.error("Could not extract surl from URL")
            return {}
        
        logger.info(f"Processing surl: {surl}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://www.terabox.com/sharing/link?surl={surl}',
        }
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Step 1: Get file metadata from API (this works without verification)
            logger.info("Getting file metadata from API")
            list_url = f"https://www.terabox.com/share/list?shorturl={surl}&root=1"
            
            response = await client.get(list_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to get file list: {response.status_code}")
                return {}
            
            data = response.json()
            if data.get('errno') != 0:
                logger.error(f"API error: {data.get('errno')}")
                return {}
            
            file_list = data.get('list', [])
            if not file_list:
                logger.error("No files in list")
                return {}
            
            file_info = file_list[0]
            filename = file_info.get('server_filename', 'video.mp4')
            size = file_info.get('size', 0)
            fs_id = file_info.get('fs_id')
            
            logger.info(f"File: {filename}, size: {size}, fs_id: {fs_id}")
            
            # Step 2: Since direct download API requires verification,
            # we'll return the share URL and let the download handler deal with it
            # The download handler will need to handle the redirect chain
            
            # Construct a URL that will redirect to the actual file
            # Terabox uses a redirect chain: share page -> download page -> actual file
            download_url = f"https://www.terabox.com/sharing/link?surl={surl}"
            
            logger.info(f"Using share URL as download URL: {download_url}")
            
            return {
                'file_name': filename,
                'url': download_url,
                'size': format_size(size),
                'sizebytes': size,
                'fs_id': fs_id,
                'surl': surl,
                'needs_special_handling': True,  # Flag for download handler
            }
            
    except Exception as e:
        logger.error(f"Error in get_terabox_info: {e}", exc_info=True)
        return {}


def format_size(size_bytes: int) -> str:
    """Format file size."""
    if not size_bytes:
        return "Unknown"
    
    try:
        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except (ValueError, TypeError):
        return "Unknown"
