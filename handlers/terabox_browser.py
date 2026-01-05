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
                
                # Intercept ALL network requests to debug what's being loaded
                logger.info("Setting up network interception for video URLs...")
                
                video_urls = []
                all_requests = []
                
                async def handle_response(response):
                    nonlocal video_urls, all_requests
                    url = response.url
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # Skip analytics and tracking URLs completely
                    if any(skip in url.lower() for skip in ['analytics', 'google', 'facebook', 'doubleclick', 'clarity.ms', '/api/analytics']):
                        return
                    
                    # Log all other requests for debugging
                    all_requests.append({
                        'url': url[:200],
                        'content_type': content_type,
                        'status': response.status
                    })
                    
                    # Look for actual video streaming URLs (strict filtering)
                    # Must have .mp4/.m3u8 in URL OR video/* content-type
                    is_video_url = '.mp4' in url or '.m3u8' in url or '.ts' in url
                    is_video_content = content_type.startswith('video/')
                    
                    if is_video_url or is_video_content:
                        logger.info(f"Found potential video URL: {url[:150]}... (content-type: {content_type})")
                        if url not in video_urls:
                            video_urls.append(url)
                
                page.on('response', handle_response)
                
                # Try to trigger video preview/player to load the streaming URL
                logger.info("Looking for video player or preview...")
                
                # Try to find and click play button or video preview
                play_selectors = [
                    'video',
                    '.video-player',
                    '[class*="video"]',
                    '[class*="player"]',
                    'button[class*="play"]',
                    '.play-button',
                ]
                
                for selector in play_selectors:
                    try:
                        logger.info(f"Trying to find video element: {selector}")
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            logger.info(f"Found video element with selector: {selector}")
                            # Try to click or interact with it
                            try:
                                await element.click()
                                logger.info("Clicked video element")
                            except:
                                pass
                            # Wait for video to load
                            await asyncio.sleep(3)
                            break
                    except PlaywrightTimeout:
                        continue
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue
                
                # Wait a bit more for any lazy-loaded video URLs
                await asyncio.sleep(2)
                
                # Log all captured requests for debugging
                logger.info(f"Captured {len(all_requests)} network requests")
                for req in all_requests[:10]:  # Log first 10 for debugging
                    logger.info(f"Request: {req['url']} | Type: {req['content_type']} | Status: {req['status']}")
                
                # Check if we found any video URLs
                if video_urls:
                    logger.info(f"Found {len(video_urls)} video URL(s) from network interception")
                    for i, url in enumerate(video_urls):
                        logger.info(f"Video URL {i+1}: {url[:200]}...")
                    
                    # Use the first video URL found
                    filename = file_info.get('fileName', 'video.mp4').strip()
                    return {
                        'file_name': filename,
                        'url': video_urls[0],
                        'size': file_info.get('fileSize', 'Unknown'),
                    }
                
                # If no video URLs intercepted, try external API as fallback
                logger.info("No video URLs intercepted, trying external API as fallback...")
                
                # Try multiple external APIs
                external_apis = [
                    f"https://terabox-dl.qtcloud.workers.dev/api/get-info?shorturl={surl}",
                    f"https://teradl-api.deno.dev/download?url=https://www.terabox.com/sharing/link?surl={surl}",
                ]
                
                for api_url in external_apis:
                    try:
                        logger.info(f"Trying external API: {api_url[:100]}...")
                        
                        external_response = await page.request.get(api_url, timeout=20000)
                        logger.info(f"External API status: {external_response.status}")
                        
                        if external_response.ok:
                            external_data = await external_response.json()
                            logger.info(f"External API response keys: {list(external_data.keys())}")
                            
                            # Try different response formats
                            download_link = None
                            filename = None
                            size = None
                            
                            # Format 1: {downloadLink, fileName, fileSize}
                            if external_data.get('downloadLink'):
                                download_link = external_data['downloadLink']
                                filename = external_data.get('fileName', 'video.mp4')
                                size = external_data.get('fileSize', 'Unknown')
                            # Format 2: {download_url, file_name, size}
                            elif external_data.get('download_url'):
                                download_link = external_data['download_url']
                                filename = external_data.get('file_name', 'video.mp4')
                                size = external_data.get('size', 'Unknown')
                            # Format 3: {dlink, server_filename}
                            elif external_data.get('dlink'):
                                download_link = external_data['dlink']
                                filename = external_data.get('server_filename', 'video.mp4')
                                size = external_data.get('size', 'Unknown')
                            
                            if download_link:
                                logger.info(f"Got download link from external API: {download_link[:100]}...")
                                return {
                                    'file_name': filename,
                                    'url': download_link,
                                    'size': size,
                                }
                            else:
                                logger.warning(f"External API returned no download link: {external_data}")
                        else:
                            logger.warning(f"External API returned status {external_response.status}")
                    except Exception as e:
                        logger.error(f"External API failed: {e}", exc_info=True)
                
                # Last resort: try internal API
                api_url = f"https://www.terabox.com/share/list?shorturl={surl}&root=1"
                response = await page.request.get(api_url)
                
                if response.ok:
                    data = await response.json()
                    logger.info(f"Internal API response errno: {data.get('errno')}")
                    
                    if data.get('errno') == 0:
                        file_list = data.get('list', [])
                        if file_list:
                            file = file_list[0]
                            filename = file.get('server_filename', 'video.mp4')
                            size = file.get('size', 0)
                            
                            logger.warning("No download link available - Terabox requires verification")
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
