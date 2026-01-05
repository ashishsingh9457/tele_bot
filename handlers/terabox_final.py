"""
Final working Terabox implementation.
Uses browser-like behavior to extract actual download links from the page.
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
    
    if 'surl' in query:
        return query['surl'][0]
    
    match = re.search(r'/s/([^/?\s]+)', url)
    if match:
        return match.group(1)
    
    return ""


async def get_terabox_file(url: str) -> dict:
    """
    Get Terabox file info by extracting data from the page itself.
    This mimics what a browser does.
    """
    try:
        surl = extract_surl(url)
        if not surl:
            logger.error("Could not extract surl from URL")
            return {}
        
        logger.info(f"Processing surl: {surl}")
        
        # Use browser-like headers
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
            # Get the share page
            logger.info("Fetching share page")
            share_url = f"https://www.terabox.com/sharing/link?surl={surl}"
            
            response = await client.get(share_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to get share page: {response.status_code}")
                return {}
            
            html = response.text
            cookies = dict(response.cookies)
            logger.info(f"Got page, cookies: {list(cookies.keys())}")
            
            # Extract file info from page
            file_info = extract_file_from_page(html)
            if not file_info:
                logger.error("Could not extract file info from page")
                return {}
            
            logger.info(f"Extracted file: {file_info.get('filename')}")
            
            # Now try to get the actual download link
            # The page contains a download button that makes a request
            fs_id = file_info.get('fs_id')
            share_id = file_info.get('share_id')
            uk = file_info.get('uk')
            sign = file_info.get('sign')
            timestamp = file_info.get('timestamp')
            
            # Build download URL with all parameters
            download_url = build_download_url(surl, fs_id, share_id, uk, sign, timestamp)
            
            if download_url:
                logger.info(f"Built download URL: {download_url[:100]}...")
                
                # Test the URL
                test_response = await client.head(download_url, headers=headers, cookies=cookies)
                logger.info(f"Download URL test: {test_response.status_code}")
                logger.info(f"Content-Type: {test_response.headers.get('content-type')}")
                
                return {
                    'file_name': file_info.get('filename', 'video.mp4'),
                    'url': download_url,
                    'size': format_size(file_info.get('size', 0)),
                    'sizebytes': file_info.get('size', 0),
                }
            
            logger.error("Could not build download URL")
            return {}
            
    except Exception as e:
        logger.error(f"Error in get_terabox_file: {e}", exc_info=True)
        return {}


def extract_file_from_page(html: str) -> dict:
    """Extract file information from the HTML page."""
    try:
        # Save a sample of the HTML for debugging
        logger.info(f"HTML length: {len(html)}")
        
        # Look for the yunData or similar embedded JSON with more flexible patterns
        patterns = [
            r'window\.yunData\s*=\s*(\{[^;]+\});',
            r'locals\.mset\((\{[^)]+\})\);',
            r'var\s+yunData\s*=\s*(\{[^;]+\});',
            r'yunData\s*=\s*(\{[^;]+\});',
            # Try to find any large JSON object that might contain file info
            r'"file_list"\s*:\s*\[(\{[^\]]+\})\]',
        ]
        
        for pattern in patterns:
            logger.info(f"Trying pattern: {pattern[:50]}...")
            matches = re.findall(pattern, html, re.DOTALL)
            logger.info(f"Found {len(matches)} matches")
            
            for match in matches:
                try:
                    # Clean up the JSON
                    match = match.strip()
                    
                    # Try to parse as JSON
                    data = json.loads(match)
                    
                    logger.info(f"Successfully parsed JSON with keys: {list(data.keys())}")
                    
                    # Extract file list
                    file_list = data.get('file_list', [])
                    if not file_list:
                        # Maybe the match itself is a file object
                        if 'server_filename' in data or 'fs_id' in data:
                            file = data
                            file_list = [file]
                        else:
                            continue
                    
                    file = file_list[0] if isinstance(file_list, list) else file_list
                    
                    logger.info(f"Found file: {file.get('server_filename', 'unknown')}")
                    
                    return {
                        'filename': file.get('server_filename', 'video.mp4'),
                        'size': file.get('size', 0),
                        'fs_id': str(file.get('fs_id', '')),
                        'share_id': str(data.get('shareid', data.get('share_id', ''))),
                        'uk': str(data.get('uk', '')),
                        'sign': str(data.get('sign', '')),
                        'timestamp': str(data.get('timestamp', '')),
                    }
                except (json.JSONDecodeError, TypeError) as e:
                    logger.debug(f"Failed to parse match: {str(e)[:100]}")
                    continue
        
        # If no patterns worked, try to find script tags with JSON
        logger.info("Trying to extract from script tags")
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html, re.DOTALL)
        logger.info(f"Found {len(scripts)} script tags")
        
        for script in scripts:
            if 'server_filename' in script and 'fs_id' in script:
                logger.info("Found script with file info")
                # Try to extract JSON object
                json_pattern = r'\{[^{}]*"server_filename"[^{}]*"fs_id"[^{}]*\}'
                json_matches = re.findall(json_pattern, script)
                for json_match in json_matches:
                    try:
                        data = json.loads(json_match)
                        logger.info(f"Extracted from script: {data.get('server_filename')}")
                        return {
                            'filename': data.get('server_filename', 'video.mp4'),
                            'size': data.get('size', 0),
                            'fs_id': str(data.get('fs_id', '')),
                            'share_id': '',
                            'uk': '',
                            'sign': '',
                            'timestamp': '',
                        }
                    except json.JSONDecodeError:
                        continue
        
        logger.warning("Could not find file info in page using any method")
        return {}
        
    except Exception as e:
        logger.error(f"Error extracting from page: {e}", exc_info=True)
        return {}


def build_download_url(surl: str, fs_id: str, share_id: str, uk: str, sign: str, timestamp: str) -> str:
    """Build download URL with all necessary parameters."""
    if not fs_id:
        return ""
    
    # Try different URL constructions
    if share_id and uk:
        # Full parameter version
        url = f"https://www.terabox.com/share/download?shareid={share_id}&uk={uk}&fid={fs_id}"
        if sign:
            url += f"&sign={sign}"
        if timestamp:
            url += f"&timestamp={timestamp}"
        return url
    
    # Simpler version
    return f"https://www.terabox.com/share/download?surl={surl}&fid={fs_id}"


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
