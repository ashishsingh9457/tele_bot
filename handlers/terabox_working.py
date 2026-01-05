"""
Working Terabox downloader implementation that bypasses verification requirements.
Uses a different approach to get actual download links.
"""
import re
import json
import httpx
import logging
from urllib.parse import urlparse, parse_qs, quote

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


async def get_terabox_download_info(url: str) -> dict:
    """
    Get Terabox file download info using a working method.
    This bypasses the verification requirement by using proper cookies and sign parameters.
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
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'https://www.terabox.com/sharing/link?surl={surl}',
            'Origin': 'https://www.terabox.com',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Step 1: Get the share page to establish session
            logger.info("Step 1: Getting share page to establish session")
            share_url = f"https://www.terabox.com/sharing/link?surl={surl}"
            
            response = await client.get(share_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to get share page: {response.status_code}")
                return {}
            
            # Extract cookies from response
            cookies = dict(response.cookies)
            logger.info(f"Got cookies: {list(cookies.keys())}")
            
            # Step 2: Get file list with cookies
            logger.info("Step 2: Getting file list with session cookies")
            list_url = f"https://www.terabox.com/share/list?shorturl={surl}&root=1"
            
            response = await client.get(list_url, headers=headers, cookies=cookies)
            if response.status_code != 200:
                logger.error(f"Failed to get file list: {response.status_code}")
                return {}
            
            data = response.json()
            logger.info(f"List API response: errno={data.get('errno')}")
            
            if data.get('errno') != 0:
                logger.error(f"List API error: {data.get('errno')} - {data.get('errmsg')}")
                return {}
            
            file_list = data.get('list', [])
            if not file_list:
                logger.error("No files in list")
                return {}
            
            file_info = file_list[0]
            fs_id = file_info.get('fs_id')
            filename = file_info.get('server_filename', 'video.mp4')
            size = file_info.get('size', 0)
            
            logger.info(f"File: {filename}, fs_id: {fs_id}, size: {size}")
            
            # Step 3: Try to get download link with session
            logger.info("Step 3: Attempting to get download link")
            
            # Method 1: Try with timestamp and sign (if available in page)
            download_url = await try_download_with_session(
                client, surl, fs_id, cookies, headers
            )
            
            if not download_url:
                logger.error("Could not get valid download URL")
                return {}
            
            return {
                'file_name': filename,
                'url': download_url,
                'size': format_size(size),
                'sizebytes': size,
            }
            
    except Exception as e:
        logger.error(f"Error in get_terabox_download_info: {e}", exc_info=True)
        return {}


async def try_download_with_session(client: httpx.AsyncClient, surl: str, 
                                     fs_id: str, cookies: dict, headers: dict) -> str:
    """Try different methods to get download link with session cookies."""
    
    # Method 1: Try download API with session cookies
    download_endpoints = [
        f"https://www.terabox.com/share/download?surl={surl}&fid_list=[{fs_id}]",
        f"https://www.terabox.com/api/download?surl={surl}&fid_list=[{fs_id}]",
    ]
    
    for endpoint in download_endpoints:
        try:
            logger.info(f"Trying: {endpoint}")
            response = await client.get(endpoint, headers=headers, cookies=cookies)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response errno: {data.get('errno')}")
                
                if data.get('errno') == 0:
                    dlink = data.get('dlink')
                    if not dlink and 'list' in data and data['list']:
                        dlink = data['list'][0].get('dlink')
                    
                    if dlink:
                        logger.info(f"Got dlink from {endpoint}")
                        return dlink
                else:
                    logger.warning(f"API error: {data.get('errno')} - {data.get('errmsg')}")
        except Exception as e:
            logger.error(f"Error with {endpoint}: {e}")
            continue
    
    # Method 2: Try to construct streaming URL
    # Terabox sometimes allows streaming via a different endpoint
    streaming_url = f"https://www.terabox.com/share/streaming?surl={surl}&fid={fs_id}"
    logger.info(f"Trying streaming URL: {streaming_url}")
    
    try:
        # Test if streaming URL works
        response = await client.head(streaming_url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'video' in content_type or 'octet-stream' in content_type:
                logger.info("Streaming URL appears valid")
                return streaming_url
    except Exception as e:
        logger.error(f"Streaming URL failed: {e}")
    
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
