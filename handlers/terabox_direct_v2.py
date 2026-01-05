"""
Direct Terabox download implementation based on working terabox-cli approach.
This extracts jsToken and browserid from the page, then uses them to get download links.
Uses authentication cookies if available to bypass verification.
"""
import re
import logging
import requests
import os
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

# Get cookies from environment if available
TERABOX_COOKIES = os.getenv('TERABOX_COOKIES', '')

# Residential proxy configuration (optional)
PROXY_URL = os.getenv('PROXY_URL', '')  # Format: http://user:pass@proxy-host:port


def extract_surl(url: str) -> str:
    """Extract surl from Terabox URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    
    if 'surl' in query:
        return query['surl'][0]
    
    match = re.search(r'/s/1?([A-Za-z0-9_-]+)', url)
    if match:
        return match.group(1)
    
    return ""


def get_terabox_download_direct(url: str) -> dict:
    """
    Get Terabox download link using direct API calls.
    Based on working terabox-cli implementation.
    Supports residential proxies to bypass server IP detection.
    
    Returns:
        dict: {
            'file_name': str,
            'url': str (download link),
            'size': str,
            'thumb': str (thumbnail URL)
        }
    """
    try:
        session = requests.Session()
        
        # Enhanced headers to mimic real browser
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'referer': 'https://www.terabox.com/',
        }
        
        # Configure proxy if available
        proxies = {}
        if PROXY_URL:
            proxies = {
                'http': PROXY_URL,
                'https': PROXY_URL
            }
            logger.info("Using residential proxy to bypass detection")
            session.proxies.update(proxies)
        
        # Extract surl
        surl = extract_surl(url)
        if not surl:
            logger.error("Could not extract surl from URL")
            return {}
        
        logger.info(f"Extracted surl: {surl}")
        
        # Step 1: Get jsToken and browserid from the page
        logger.info("Getting authorization tokens...")
        page_url = f'https://www.terabox.app/wap/share/filelist?surl={surl}'
        page_response = session.get(page_url, headers=headers, allow_redirects=True)
        
        if page_response.status_code != 200:
            logger.error(f"Failed to load page: {page_response.status_code}")
            return {}
        
        # Extract jsToken from page
        js_token_match = re.search(r'%28%22(.*?)%22%29', page_response.text.replace('\\', ''))
        if not js_token_match:
            logger.error("Could not extract jsToken from page")
            return {}
        
        js_token = js_token_match.group(1)
        browser_id = page_response.cookies.get('browserid', '')
        
        logger.info(f"Got jsToken: {js_token[:20]}...")
        logger.info(f"Got browserid: {browser_id}")
        
        # Build cookie string
        cookie_dict = session.cookies.get_dict()
        cookie = 'lang=en;' + ';'.join([f'{k}={v}' for k, v in cookie_dict.items()])
        
        # Load authentication cookies if available
        auth_cookies = {}
        if TERABOX_COOKIES:
            try:
                import json
                cookies_list = json.loads(TERABOX_COOKIES)
                for cookie in cookies_list:
                    auth_cookies[cookie['name']] = cookie['value']
                logger.info(f"Loaded {len(auth_cookies)} authentication cookies")
            except Exception as e:
                logger.warning(f"Failed to parse cookies: {e}")
        
        # Step 2: Get file info and metadata
        logger.info("Getting file information...")
        info_url = f'https://www.terabox.com/api/shorturlinfo?app_id=250528&shorturl=1{surl}&root=1'
        
        # Try with auth cookies first if available
        if auth_cookies:
            info_response = session.get(info_url, headers=headers, cookies=auth_cookies)
        else:
            info_response = session.get(info_url, headers=headers)
        
        if info_response.status_code != 200:
            logger.error(f"Failed to get file info: {info_response.status_code}")
            return {}
        
        info_data = info_response.json()
        logger.info(f"File info response: errno={info_data.get('errno')}")
        
        if info_data.get('errno') == 400210:
            logger.error("Terabox requires verification (errno: 400210)")
            logger.error("This happens when requests come from server IPs.")
            logger.error("Solution: Add TERABOX_COOKIES environment variable with authenticated cookies.")
            logger.error("See TERABOX_SETUP.md for instructions.")
            return {}
        
        if info_data.get('errno') != 0:
            logger.error(f"API error: {info_data.get('errno')} - {info_data.get('errmsg')}")
            return {}
        
        file_list = info_data.get('list', [])
        if not file_list:
            logger.error("No files found in response")
            return {}
        
        # Get first file (or first video file)
        target_file = None
        for file in file_list:
            if file.get('isdir') == 0:  # Not a directory
                filename = file.get('server_filename', '')
                if filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    target_file = file
                    break
        
        if not target_file:
            target_file = file_list[0]
        
        fs_id = target_file.get('fs_id')
        filename = target_file.get('server_filename', 'video.mp4')
        size = target_file.get('size', 0)
        thumb = target_file.get('thumbs', {}).get('url3', '')
        
        logger.info(f"Target file: {filename} (fs_id: {fs_id})")
        
        # Get required parameters for download API
        sign = info_data.get('sign', '')
        timestamp = info_data.get('timestamp', '')
        shareid = info_data.get('shareid', '')
        uk = info_data.get('uk', '')
        
        # Step 3: Get download link
        logger.info("Getting download link...")
        download_params = {
            'app_id': '250528',
            'channel': 'dubox',
            'product': 'share',
            'clienttype': '0',
            'dp-logid': '',
            'nozip': '0',
            'web': '1',
            'uk': str(uk),
            'sign': str(sign),
            'shareid': str(shareid),
            'primaryid': str(shareid),
            'timestamp': str(timestamp),
            'jsToken': str(js_token),
            'fid_list': f'[{fs_id}]'
        }
        
        download_url = 'https://www.terabox.com/share/download?' + '&'.join([f'{k}={v}' for k, v in download_params.items()])
        download_response = session.get(download_url, cookies={'cookie': cookie})
        
        if download_response.status_code != 200:
            logger.error(f"Failed to get download link: {download_response.status_code}")
            return {}
        
        download_data = download_response.json()
        logger.info(f"Download API response: errno={download_data.get('errno')}")
        
        if download_data.get('errno') != 0:
            logger.error(f"Download API error: {download_data.get('errno')} - {download_data.get('errmsg')}")
            return {}
        
        dlink = download_data.get('dlink')
        if not dlink:
            logger.error("No download link in response")
            return {}
        
        logger.info(f"Got download link: {dlink[:100]}...")
        
        # Step 4: Resolve redirect to get fast CDN URL
        logger.info("Resolving redirect to fast CDN...")
        try:
            head_response = session.head(dlink, allow_redirects=True, timeout=10)
            final_url = head_response.url
            
            # Try to optimize URL for faster download
            domain_match = re.search(r'://(.*?)\.', final_url)
            if domain_match:
                old_domain = domain_match.group(1)
                # Try d3 domain for faster speeds
                fast_url = final_url.replace(old_domain, 'd3').replace('by=themis', 'by=dapunta')
                logger.info(f"Optimized URL: {fast_url[:100]}...")
                final_url = fast_url
            
            logger.info(f"Final CDN URL: {final_url[:100]}...")
        except Exception as e:
            logger.warning(f"Could not resolve redirect: {e}, using direct link")
            final_url = dlink
        
        # Format size
        size_str = format_size(size)
        
        return {
            'file_name': filename,
            'url': final_url,
            'size': size_str,
            'thumb': thumb
        }
        
    except Exception as e:
        logger.error(f"Error in direct download: {e}", exc_info=True)
        return {}
    finally:
        session.close()


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.2f} {units[i]}"
