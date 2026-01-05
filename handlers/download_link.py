import httpx
import logging

logger = logging.getLogger(__name__)


async def fetch_download_link(client: httpx.AsyncClient, fs_id: str, share_id: str, uk: str, surl: str, headers: dict) -> str:
    """
    Fetch download link for a specific file from Terabox.
    
    Args:
        client: HTTP client
        fs_id: File system ID
        share_id: Share ID from the list response
        uk: User key from the list response
        surl: Short URL parameter
        headers: Request headers
    
    Returns:
        Download link URL or empty string if failed
    """
    # Try multiple API endpoints to get download link
    endpoints = [
        # Method 1: Direct download API
        f'https://www.terabox.app/share/download?surl={surl}&fid_list=[{fs_id}]',
        f'https://www.terabox.com/share/download?surl={surl}&fid_list=[{fs_id}]',
        
        # Method 2: With share_id and uk
        f'https://www.terabox.app/api/download?share_id={share_id}&uk={uk}&fid_list=[{fs_id}]',
        f'https://www.terabox.com/api/download?share_id={share_id}&uk={uk}&fid_list=[{fs_id}]',
    ]
    
    for endpoint in endpoints:
        try:
            logger.info(f"Trying download link endpoint: {endpoint}")
            response = await client.get(endpoint, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Download API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                if isinstance(data, dict):
                    errno = data.get('errno', -1)
                    
                    if errno == 0:
                        # Success - extract download link
                        dlink = None
                        
                        # Check various possible structures
                        if 'dlink' in data:
                            dlink = data['dlink']
                        elif 'list' in data and isinstance(data['list'], list) and len(data['list']) > 0:
                            dlink = data['list'][0].get('dlink')
                        elif 'download_link' in data:
                            dlink = data['download_link']
                        
                        if dlink:
                            logger.info(f"Successfully fetched download link")
                            return dlink
                    else:
                        logger.warning(f"Download API returned errno: {errno}")
        except Exception as e:
            logger.error(f"Error fetching download link from {endpoint}: {e}")
            continue
    
    # If all API methods fail, try to construct a direct link
    # Some Terabox files can be accessed via direct URL patterns
    try:
        # Method 3: Try constructing streaming URL
        streaming_url = f'https://www.terabox.app/sharing/link?surl={surl}&path=%2F'
        logger.info(f"Attempting to use streaming URL: {streaming_url}")
        return streaming_url
    except Exception as e:
        logger.error(f"Error constructing streaming URL: {e}")
    
    return ''


async def get_file_metadata(client: httpx.AsyncClient, fs_id: str, share_id: str, uk: str, headers: dict) -> dict:
    """
    Get detailed metadata for a file including download link.
    
    Args:
        client: HTTP client
        fs_id: File system ID
        share_id: Share ID
        uk: User key
        headers: Request headers
    
    Returns:
        File metadata dict or empty dict
    """
    endpoints = [
        f'https://www.terabox.app/api/file/detail?fs_id={fs_id}&share_id={share_id}&uk={uk}',
        f'https://www.terabox.com/api/file/detail?fs_id={fs_id}&share_id={share_id}&uk={uk}',
    ]
    
    for endpoint in endpoints:
        try:
            response = await client.get(endpoint, headers=headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and data.get('errno') == 0:
                    return data
        except Exception:
            continue
    
    return {}
