import logging
import json

logger = logging.getLogger(__name__)


async def log_api_response(url: str, data: dict):
    """Log API response for debugging purposes."""
    try:
        logger.info(f"API Response from {url}:")
        logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        if isinstance(data, dict):
            # Log errno if present
            if 'errno' in data:
                logger.info(f"errno: {data['errno']}")
            
            # Log list structure if present
            if 'list' in data:
                list_data = data['list']
                logger.info(f"List type: {type(list_data)}")
                if isinstance(list_data, list) and len(list_data) > 0:
                    logger.info(f"First item keys: {list(list_data[0].keys()) if isinstance(list_data[0], dict) else 'Not a dict'}")
                    logger.info(f"First item sample: {json.dumps(list_data[0], indent=2)[:500]}")
    except Exception as e:
        logger.error(f"Error logging API response: {e}")


def extract_surl_from_url(url: str) -> str:
    """Extract surl parameter from various Terabox URL formats."""
    import re
    
    # Try different patterns
    patterns = [
        r'surl=([^&\s]+)',
        r'/s/([^/\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return ''
