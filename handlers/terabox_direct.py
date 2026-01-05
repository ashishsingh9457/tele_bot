"""
Direct Terabox API implementation without external dependencies.
Based on reverse-engineered Terabox API endpoints.
"""
import re
import json
import httpx
import logging
from urllib.parse import urlparse, parse_qs, quote

logger = logging.getLogger(__name__)


def extract_surl_from_url(url: str) -> str:
    """Extract surl/shorturl from Terabox URL."""
    # Try query parameter first
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])
    
    if surl:
        return surl[0]
    
    # Try path patterns
    patterns = [
        r'/s/([^/\s?]+)',
        r'surl=([^&\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return ""


def find_between(data: str, first: str, last: str) -> str:
    """Extract text between two strings."""
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except (ValueError, AttributeError):
        return ""


async def get_file_info_direct(url: str) -> dict:
    """
    Get file info directly from Terabox API without external services.
    Uses Terabox's own API endpoints.
    """
    try:
        surl = extract_surl_from_url(url)
        if not surl:
            logger.error("Could not extract surl from URL")
            return {}
        
        logger.info(f"Extracted surl: {surl}")
        
        # Headers mimicking browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.terabox.com/',
            'Origin': 'https://www.terabox.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Step 1: Get the share page to extract necessary tokens/cookies
            logger.info("Step 1: Fetching share page")
            share_url = f"https://www.terabox.com/sharing/link?surl={surl}"
            
            response = await client.get(share_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch share page: {response.status_code}")
                return {}
            
            html_content = response.text
            
            # Extract jsToken from page
            js_token = find_between(html_content, 'fn%28%22', '%22%29')
            if not js_token:
                js_token = find_between(html_content, 'jsToken = "', '"')
            
            logger.info(f"Extracted jsToken: {bool(js_token)}")
            
            # Extract logid
            logid = find_between(html_content, 'logid=', '&')
            if not logid:
                logid = find_between(html_content, '"logid":"', '"')
            
            logger.info(f"Extracted logid: {bool(logid)}")
            
            # Step 2: Call the list API to get file information
            logger.info("Step 2: Calling list API")
            
            # Try multiple API endpoints
            api_endpoints = [
                f"https://www.terabox.com/share/list?shorturl={surl}&root=1",
                f"https://www.terabox.com/api/list?shorturl={surl}&root=1",
                f"https://www.1024terabox.com/share/list?shorturl={surl}&root=1",
            ]
            
            list_data = None
            for api_url in api_endpoints:
                try:
                    logger.info(f"Trying API: {api_url}")
                    api_response = await client.get(api_url, headers=headers)
                    
                    if api_response.status_code == 200:
                        list_data = api_response.json()
                        logger.info(f"API response keys: {list(list_data.keys())}")
                        
                        if list_data.get('errno') == 0:
                            logger.info("Successfully got list data")
                            break
                        else:
                            logger.warning(f"API returned errno: {list_data.get('errno')}")
                except Exception as e:
                    logger.error(f"Error calling API {api_url}: {e}")
                    continue
            
            if not list_data or list_data.get('errno') != 0:
                logger.error("Failed to get valid list data from all APIs")
                return {}
            
            # Extract file information
            file_list = list_data.get('list', [])
            if not file_list:
                logger.error("No files in list")
                return {}
            
            # Get the first file (assuming single file share)
            file_info = file_list[0]
            logger.info(f"File info keys: {list(file_info.keys())}")
            
            fs_id = file_info.get('fs_id')
            server_filename = file_info.get('server_filename', 'video.mp4')
            size = file_info.get('size', 0)
            share_id = list_data.get('share_id', '')
            uk = list_data.get('uk', '')
            
            logger.info(f"File: {server_filename}, fs_id: {fs_id}, size: {size}")
            
            # Step 3: Get download link
            logger.info("Step 3: Fetching download link")
            
            # Try to get download link using various methods
            download_link = await get_download_link(
                client, surl, fs_id, share_id, uk, headers
            )
            
            if not download_link:
                logger.warning("Could not get direct download link, using streaming URL")
                # Fallback to streaming URL
                download_link = f"https://www.terabox.com/sharing/link?surl={surl}"
            
            result = {
                'file_name': server_filename,
                'url': download_link,
                'size': format_size(size),
                'sizebytes': size,
                'fs_id': fs_id,
                'share_id': share_id,
                'uk': uk,
            }
            
            logger.info(f"Final result: {result['file_name']}, has_url: {bool(result['url'])}")
            return result
            
    except Exception as e:
        logger.error(f"Error in get_file_info_direct: {e}", exc_info=True)
        return {}


async def get_download_link(client: httpx.AsyncClient, surl: str, fs_id: str, 
                            share_id: str, uk: str, headers: dict) -> str:
    """Try to get direct download link from Terabox."""
    
    # Method 1: Try download API with fs_id
    download_endpoints = [
        f"https://www.terabox.com/share/download?surl={surl}&fid_list=[{fs_id}]",
        f"https://www.1024terabox.com/share/download?surl={surl}&fid_list=[{fs_id}]",
    ]
    
    for endpoint in download_endpoints:
        try:
            logger.info(f"Trying download endpoint: {endpoint}")
            response = await client.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Download API response: {list(data.keys())}")
                
                if data.get('errno') == 0:
                    # Extract dlink
                    dlink = data.get('dlink')
                    if not dlink and 'list' in data and data['list']:
                        dlink = data['list'][0].get('dlink')
                    
                    if dlink:
                        logger.info("Successfully got download link from API")
                        return dlink
        except Exception as e:
            logger.error(f"Error with download endpoint {endpoint}: {e}")
            continue
    
    # Method 2: Try to construct download URL from file info
    if share_id and uk and fs_id:
        constructed_url = f"https://www.terabox.com/share/download?shareid={share_id}&uk={uk}&fid={fs_id}"
        logger.info(f"Using constructed URL: {constructed_url}")
        return constructed_url
    
    return ""


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
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
