"""
Self-contained Terabox scraper that extracts download links
by reverse-engineering Terabox's web interface and API.
No external service dependencies.
"""
import re
import json
import httpx
import logging
from urllib.parse import urlparse, parse_qs, unquote

logger = logging.getLogger(__name__)


def extract_surl(url: str) -> str:
    """Extract surl from Terabox URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    
    # Try query parameter
    if 'surl' in query:
        return query['surl'][0]
    
    # Try path patterns
    match = re.search(r'/s/([^/?\s]+)', url)
    if match:
        return match.group(1)
    
    return ""


async def get_terabox_file_info(url: str) -> dict:
    """
    Extract file info from Terabox by scraping and parsing the share page.
    This mimics what external APIs do but runs locally.
    """
    try:
        surl = extract_surl(url)
        if not surl:
            logger.error("Could not extract surl from URL")
            return {}
        
        logger.info(f"Processing surl: {surl}")
        
        # Use 1024terabox.com domain for better success rate
        base_url = f"https://www.1024terabox.com/sharing/link?surl={surl}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Step 1: Fetch the share page HTML
            logger.info(f"Fetching share page: {base_url}")
            response = await client.get(base_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch page: {response.status_code}")
                return {}
            
            html = response.text
            logger.info(f"Got HTML response, length: {len(html)}")
            
            # Step 2: Extract embedded JSON data from the page
            # Terabox embeds file information in JavaScript variables
            file_info = extract_file_info_from_html(html)
            
            if not file_info:
                logger.warning("Could not extract file info from HTML, trying API method")
                # Fallback to API method
                file_info = await fetch_via_api(client, surl, headers)
            
            if not file_info:
                logger.error("All extraction methods failed")
                return {}
            
            logger.info(f"Successfully extracted file: {file_info.get('file_name')}")
            return file_info
            
    except Exception as e:
        logger.error(f"Error in get_terabox_file_info: {e}", exc_info=True)
        return {}


def extract_file_info_from_html(html: str) -> dict:
    """
    Extract file information from Terabox HTML page.
    Terabox embeds data in JavaScript variables and JSON.
    """
    try:
        # Method 1: Look for window.jsToken or similar embedded data
        patterns = [
            r'window\.jsToken\s*=\s*({[^;]+});',
            r'locals\.mset\(({.+?})\);',
            r'window\.yunData\s*=\s*({.+?});',
            r'var\s+yunData\s*=\s*({.+?});',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    logger.info(f"Found embedded JSON data with keys: {list(data.keys())}")
                    
                    # Extract file list
                    file_list = data.get('file_list', [])
                    if not file_list and 'list' in data:
                        file_list = data['list']
                    
                    if file_list and isinstance(file_list, list):
                        file = file_list[0]
                        return parse_file_object(file)
                        
                except json.JSONDecodeError:
                    continue
        
        # Method 2: Look for specific data patterns in script tags
        # Extract file info from data-* attributes or inline JSON
        json_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(json_pattern, html, re.DOTALL)
        
        for script in scripts:
            # Look for file information patterns
            if 'server_filename' in script and 'fs_id' in script:
                # Try to extract JSON object
                json_match = re.search(r'\{[^{}]*"server_filename"[^{}]*\}', script)
                if json_match:
                    try:
                        file_data = json.loads(json_match.group(0))
                        return parse_file_object(file_data)
                    except json.JSONDecodeError:
                        continue
        
        logger.warning("Could not extract file info from HTML using any method")
        return {}
        
    except Exception as e:
        logger.error(f"Error extracting from HTML: {e}")
        return {}


def parse_file_object(file_obj: dict) -> dict:
    """Parse file object and extract relevant information."""
    try:
        filename = file_obj.get('server_filename', 'video.mp4')
        size = file_obj.get('size', 0)
        fs_id = file_obj.get('fs_id', '')
        
        # Try to get download link if available
        dlink = file_obj.get('dlink', '')
        
        # If no direct link, construct streaming URL
        if not dlink:
            path = file_obj.get('path', '')
            if path:
                # Construct a potential streaming URL
                dlink = f"https://www.1024terabox.com{path}"
        
        return {
            'file_name': filename,
            'url': dlink,
            'size': format_size(size),
            'sizebytes': size,
            'fs_id': fs_id,
        }
    except Exception as e:
        logger.error(f"Error parsing file object: {e}")
        return {}


async def fetch_via_api(client: httpx.AsyncClient, surl: str, headers: dict) -> dict:
    """
    Fallback method: Try to fetch file info via Terabox API endpoints.
    """
    api_urls = [
        f"https://www.1024terabox.com/share/list?shorturl={surl}&root=1",
        f"https://www.terabox.com/share/list?shorturl={surl}&root=1",
        f"https://www.terabox.app/share/list?shorturl={surl}&root=1",
    ]
    
    for api_url in api_urls:
        try:
            logger.info(f"Trying API: {api_url}")
            response = await client.get(api_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('errno') == 0:
                    file_list = data.get('list', [])
                    if file_list:
                        file = file_list[0]
                        
                        # Get additional metadata
                        share_id = data.get('share_id', '')
                        uk = data.get('uk', '')
                        fs_id = file.get('fs_id', '')
                        
                        # Try to get download link with proper authentication
                        dlink = await get_download_link_with_cookies(client, surl, fs_id, share_id, uk, headers)
                        
                        if not dlink:
                            logger.warning("Could not get download link, will fail")
                            return {}
                        
                        return {
                            'file_name': file.get('server_filename', 'video.mp4'),
                            'url': dlink,
                            'size': format_size(file.get('size', 0)),
                            'sizebytes': file.get('size', 0),
                            'fs_id': fs_id,
                            'share_id': share_id,
                            'uk': uk,
                        }
        except Exception as e:
            logger.error(f"Error with API {api_url}: {e}")
            continue
    
    return {}


async def get_download_link(client: httpx.AsyncClient, surl: str, fs_id: str, 
                            share_id: str, uk: str, headers: dict) -> str:
    """Try to get direct download link."""
    if not fs_id:
        logger.warning("No fs_id provided for download link")
        return ""
    
    logger.info(f"Attempting to get download link for fs_id: {fs_id}")
    
    download_urls = [
        f"https://www.1024terabox.com/share/download?surl={surl}&fid_list=[{fs_id}]",
        f"https://www.terabox.com/share/download?surl={surl}&fid_list=[{fs_id}]",
    ]
    
    for url in download_urls:
        try:
            logger.info(f"Trying download URL: {url}")
            response = await client.get(url, headers=headers)
            logger.info(f"Download API status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Download API response keys: {list(data.keys())}")
                logger.info(f"Download API errno: {data.get('errno')}")
                
                if data.get('errno') == 0:
                    dlink = data.get('dlink')
                    if not dlink and 'list' in data and data['list']:
                        dlink = data['list'][0].get('dlink')
                    
                    if dlink:
                        logger.info(f"Got dlink: {dlink[:100]}...")
                        return dlink
                    else:
                        logger.warning("No dlink in successful response")
                else:
                    logger.warning(f"API returned error: {data.get('errno')} - {data.get('errmsg', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error getting download link from {url}: {e}")
            continue
    
    logger.warning("All download link attempts failed")
    return ""


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
