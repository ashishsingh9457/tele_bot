import re
import httpx
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def extract_surl_from_url(url: str) -> str:
    """Extract surl parameter from Terabox URL."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])
    
    if surl:
        return surl[0]
    
    # Try to extract from path patterns like /s/xxxxx
    match = re.search(r'/s/([^/\s]+)', url)
    if match:
        return match.group(1)
    
    return ""


def find_between(data: str, first: str, last: str) -> str:
    """Find text between two strings."""
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return ""


async def get_terabox_download_link(url: str) -> dict:
    """
    Get download link from Terabox URL using external API service.
    
    Returns:
        dict with keys: file_name, link, direct_link, thumb, size, sizebytes
    """
    try:
        # Change domain to 1024terabox.com for better compatibility
        netloc = urlparse(url).netloc
        modified_url = url.replace(netloc, "1024terabox.com")
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Get the page to extract thumbnail
            response = await client.get(modified_url)
            default_thumbnail = ""
            if response.status_code == 200:
                default_thumbnail = find_between(response.text, 'og:image" content="', '"')
            
            # Use external API to get download link
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.5",
                "Content-Type": "application/json",
                "Origin": "https://ytshorts.savetube.me",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
            
            api_response = await client.post(
                "https://ytshorts.savetube.me/api/v1/terabox-downloader",
                headers=headers,
                json={"url": modified_url},
            )
            
            if api_response.status_code != 200:
                logger.error(f"API returned status code: {api_response.status_code}")
                return {}
            
            data = api_response.json()
            logger.info(f"API response keys: {list(data.keys())}")
            
            responses = data.get("response", [])
            if not responses:
                logger.warning("No response data from API")
                return {}
            
            resolutions = responses[0].get("resolutions", {})
            if not resolutions:
                logger.warning("No resolutions in response")
                return {}
            
            download_link = resolutions.get("Fast Download", "")
            video_link = resolutions.get("HD Video", "")
            
            logger.info(f"Got video link: {bool(video_link)}, download link: {bool(download_link)}")
            
            # Get file info from video link
            file_name = None
            size_bytes = None
            
            if video_link:
                head_response = await client.head(video_link)
                content_length = head_response.headers.get("Content-Length")
                if content_length:
                    size_bytes = int(content_length)
                
                content_disposition = head_response.headers.get("content-disposition")
                if content_disposition:
                    fname_match = re.findall(r'filename="(.+)"', content_disposition)
                    if fname_match:
                        file_name = fname_match[0]
            
            # Get direct download link
            direct_link = None
            if download_link:
                head_response = await client.head(download_link)
                direct_link = head_response.headers.get("location", download_link)
            
            result = {
                "file_name": file_name,
                "link": video_link if video_link else None,
                "direct_link": direct_link if direct_link else download_link if download_link else None,
                "thumb": default_thumbnail if default_thumbnail else None,
                "size": format_size(size_bytes) if size_bytes else "Unknown",
                "sizebytes": size_bytes,
            }
            
            logger.info(f"Extracted file: {file_name}, size: {result['size']}")
            return result
            
    except Exception as e:
        logger.error(f"Error getting download link: {e}")
        return {}


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if not size_bytes:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
