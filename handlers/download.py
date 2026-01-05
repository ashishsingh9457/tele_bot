import httpx
import tempfile
import os
from telegram import Update


async def download_and_send_file(update: Update, file_info: dict, current: int, total: int):
    """
    Download MP4 file and send it via Telegram.
    
    Args:
        update: Telegram update object
        file_info: Dict with 'name', 'url', 'size'
        current: Current file number
        total: Total number of files
    """
    # Telegram file size limits
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB for bots (2GB for premium users)
    
    file_url = file_info['url']
    file_name = file_info['name']
    file_size_str = file_info['size']
    
    try:
        # Send progress message
        progress_msg = await update.message.reply_text(
            f"⬇️ Downloading file {current}/{total}:\n`{file_name}`\n\nPlease wait..."
        )
        
        # Check if file size is available and within limits
        if file_size_str != 'Unknown':
            file_size = parse_size_to_bytes(file_size_str)
            if file_size and file_size > MAX_FILE_SIZE:
                await progress_msg.edit_text(
                    f"❌ File {current}/{total} is too large:\n"
                    f"`{file_name}`\n"
                    f"Size: {file_size_str} (Max: 50 MB)\n\n"
                    f"Direct link: {file_url}"
                )
                return
        
        # Download file with streaming
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Referer': 'https://www.terabox.app/',
        }
        
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=300.0) as client:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_path = temp_file.name
                
                try:
                    # Stream download
                    async with client.stream('GET', file_url) as response:
                        response.raise_for_status()
                        
                        # Check content length
                        content_length = response.headers.get('content-length')
                        if content_length:
                            total_size = int(content_length)
                            if total_size > MAX_FILE_SIZE:
                                await progress_msg.edit_text(
                                    f"❌ File {current}/{total} is too large:\n"
                                    f"`{file_name}`\n"
                                    f"Size: {format_size(total_size)} (Max: 50 MB)\n\n"
                                    f"Direct link: {file_url}"
                                )
                                os.unlink(temp_path)
                                return
                        
                        # Download in chunks
                        downloaded = 0
                        chunk_size = 1024 * 1024  # 1 MB chunks
                        
                        async for chunk in response.aiter_bytes(chunk_size):
                            temp_file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Check size limit during download
                            if downloaded > MAX_FILE_SIZE:
                                await progress_msg.edit_text(
                                    f"❌ File {current}/{total} exceeded size limit during download:\n"
                                    f"`{file_name}`\n\n"
                                    f"Direct link: {file_url}"
                                )
                                os.unlink(temp_path)
                                return
                    
                    # Update progress
                    await progress_msg.edit_text(
                        f"📤 Uploading file {current}/{total} to Telegram:\n`{file_name}`\n\nPlease wait..."
                    )
                    
                    # Send file to Telegram
                    with open(temp_path, 'rb') as video_file:
                        await update.message.reply_video(
                            video=video_file,
                            filename=file_name,
                            caption=f"✅ File {current}/{total}: {file_name}",
                            supports_streaming=True,
                            read_timeout=300,
                            write_timeout=300,
                            connect_timeout=300,
                            pool_timeout=300
                        )
                    
                    # Delete progress message
                    await progress_msg.delete()
                    
                except httpx.HTTPError as e:
                    await progress_msg.edit_text(
                        f"❌ Failed to download file {current}/{total}:\n"
                        f"`{file_name}`\n"
                        f"Error: {str(e)}\n\n"
                        f"Direct link: {file_url}"
                    )
                except Exception as e:
                    await progress_msg.edit_text(
                        f"❌ Error processing file {current}/{total}:\n"
                        f"`{file_name}`\n"
                        f"Error: {str(e)}"
                    )
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except Exception:
                            pass
    
    except Exception as e:
        await update.message.reply_text(
            f"❌ Unexpected error with file {current}/{total}:\n{str(e)}"
        )


def parse_size_to_bytes(size_str: str) -> int:
    """Convert human-readable size to bytes."""
    try:
        size_str = size_str.strip().upper()
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4,
        }
        
        for unit, multiplier in units.items():
            if unit in size_str:
                number = float(size_str.replace(unit, '').strip())
                return int(number * multiplier)
        
        return 0
    except Exception:
        return 0


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    try:
        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except (ValueError, TypeError):
        return 'Unknown'
