"""
Browser automation for Terabox downloads using Playwright.
This bypasses verification by using a real browser.
"""
import re
import asyncio
import logging
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

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


async def get_terabox_download_with_browser(url: str) -> dict:
    """
    Use browser automation to get Terabox download link.
    This bypasses anti-bot protection by using a real browser.
    """
    try:
        surl = extract_surl(url)
        if not surl:
            logger.error("Could not extract surl from URL")
            return {}
        
        logger.info(f"Starting browser automation for surl: {surl}")
        
        async with async_playwright() as p:
            # Launch browser in headless mode
            logger.info("Launching browser...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            # Create context with realistic settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to Terabox share page
                share_url = f"https://www.terabox.com/sharing/link?surl={surl}"
                logger.info(f"Navigating to: {share_url}")
                
                await page.goto(share_url, wait_until='networkidle', timeout=30000)
                
                # Wait for page to load
                await asyncio.sleep(2)
                
                # Extract file information from the page
                logger.info("Extracting file information...")
                
                # Try to get file info from page content
                file_info = await page.evaluate('''() => {
                    // Try to find file information in various places
                    const fileNameElement = document.querySelector('.file-name, .filename, [class*="filename"]');
                    const fileSizeElement = document.querySelector('.file-size, .filesize, [class*="filesize"]');
                    
                    // Try to extract from JavaScript variables
                    let yunData = null;
                    try {
                        if (window.yunData) yunData = window.yunData;
                    } catch(e) {}
                    
                    return {
                        fileName: fileNameElement ? fileNameElement.textContent : null,
                        fileSize: fileSizeElement ? fileSizeElement.textContent : null,
                        yunData: yunData
                    };
                }''')
                
                logger.info(f"Page data: {file_info}")
                
                # Try to click download button and intercept the download URL
                logger.info("Looking for download button...")
                
                download_url = None
                
                # Set up request interception to catch download URLs
                async def handle_request(request):
                    nonlocal download_url
                    url = request.url
                    # Look for download-related URLs, but exclude analytics
                    if 'analytics' in url.lower() or 'google' in url.lower():
                        return  # Skip analytics URLs
                    
                    # Look for actual download URLs
                    if ('download' in url or 'dlink' in url or '.mp4' in url) and 'terabox' in url:
                        logger.info(f"Intercepted potential download URL: {url[:100]}...")
                        if not download_url:
                            download_url = url
                
                page.on('request', handle_request)
                
                # Try to find and click download button
                download_selectors = [
                    'button:has-text("Download")',
                    'a:has-text("Download")',
                    '.download-button',
                    '[class*="download"]',
                    'button[class*="download"]',
                ]
                
                for selector in download_selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            logger.info(f"Found download element with selector: {selector}")
                            await element.click()
                            # Wait for download to start
                            await asyncio.sleep(3)
                            break
                    except PlaywrightTimeout:
                        continue
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue
                
                # Don't rely on intercepted URLs - use API directly
                logger.info("Using API to get file info and construct download URL...")
                
                # Make API call to get file list
                api_url = f"https://www.terabox.com/share/list?shorturl={surl}&root=1"
                response = await page.request.get(api_url)
                
                if response.ok:
                    data = await response.json()
                    logger.info(f"API response errno: {data.get('errno')}")
                    
                    if data.get('errno') == 0:
                        file_list = data.get('list', [])
                        if file_list:
                            file = file_list[0]
                            filename = file.get('server_filename', 'video.mp4')
                            size = file.get('size', 0)
                            fs_id = file.get('fs_id', '')
                            dlink = file.get('dlink', '')
                            
                            logger.info(f"Got file info from API: {filename}, fs_id: {fs_id}")
                            
                            # If dlink is available, use it
                            if dlink:
                                logger.info(f"Found dlink in API response: {dlink[:100]}...")
                                return {
                                    'file_name': filename,
                                    'url': dlink,
                                    'size': format_size(size),
                                }
                            
                            # Try to get download link via download API
                            download_api_url = f"https://www.terabox.com/share/download?surl={surl}&fid_list=[{fs_id}]"
                            logger.info(f"Trying download API: {download_api_url}")
                            
                            download_response = await page.request.get(download_api_url)
                            if download_response.ok:
                                download_data = await download_response.json()
                                logger.info(f"Download API errno: {download_data.get('errno')}")
                                
                                if download_data.get('errno') == 0:
                                    dlink = download_data.get('dlink')
                                    if not dlink and 'list' in download_data and download_data['list']:
                                        dlink = download_data['list'][0].get('dlink')
                                    
                                    if dlink:
                                        logger.info(f"Got dlink from download API: {dlink[:100]}...")
                                        return {
                                            'file_name': filename,
                                            'url': dlink,
                                            'size': format_size(size),
                                        }
                                else:
                                    logger.warning(f"Download API error: {download_data.get('errno')} - {download_data.get('errmsg')}")
                            
                            # If all else fails, return file info without URL
                            logger.warning("Could not get download link, returning file info only")
                            return {
                                'file_name': filename,
                                'url': '',
                                'size': format_size(size),
                            }
                
                logger.error("Could not extract download information")
                return {}
                
            finally:
                await browser.close()
                logger.info("Browser closed")
    
    except Exception as e:
        logger.error(f"Error in browser automation: {e}", exc_info=True)
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
