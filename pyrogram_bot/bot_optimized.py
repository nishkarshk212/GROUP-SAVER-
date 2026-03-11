"""
NSFW Moderation Bot - Pyrogram Version
OPTIMIZED with Async Workers and GPU Acceleration
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os
import tempfile

from config import (
    API_ID, API_HASH, BOT_TOKEN, NSFW_THRESHOLD,
    MAX_FILE_SIZE_MB, TEMP_DIR
)
from async_worker import worker_pool


# Initialize bot
app = Client(
    "nsfw-moderator",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Chat settings storage
chat_settings = {}


def get_chat_settings(chat_id: int) -> dict:
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {
            "photo_scan": True,
            "video_scan": False,
            "gif_scan": False,
            "sticker_scan": False,
            "text_scan": True,
            "delete_on_detect": True,
            "warn_user": True
        }
    return chat_settings[chat_id]


async def handle_nsfw_detection(message: Message, result: dict):
    """Handle NSFW detection result"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    is_nsfw = result.get('is_nsfw', False)
    score = result.get('score', 0.0)
    method = result.get('method', 'analysis')
    
    if is_nsfw and settings.get('delete_on_detect', True):
        try:
            await message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")
        
        if settings.get('warn_user', True):
            warning_text = (
                f"🚫 **NSFW Content Detected**\n\n"
                f"User ID: `{message.from_user.id}`\n"
                f"Confidence: {score:.2%}\n"
                f"Method: {method}\n"
                f"Frames Analyzed: {result.get('frames_analyzed', 1)}"
            )
            try:
                sent = await message.reply(warning_text)
                # Auto-delete warning after 10 seconds
                await asyncio.sleep(10)
                await sent.delete()
            except Exception as e:
                print(f"Error sending warning: {e}")


@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    welcome_text = """🤖 **NSFW Moderation Bot** (Optimized)

I can detect and moderate NSFW content including:
• Photos (GPU-accelerated)
• Videos (async frame analysis)
• GIFs (every 3rd frame scan)
• Stickers (static + animated + TGS)

✨ Features:
• GPU acceleration with PyTorch
• Async worker pool for speed
• Smart frame sampling

Use /settings to configure moderation options."""
    
    await message.reply(welcome_text)


@app.on_message(filters.command("settings"))
async def settings_command(client: Client, message: Message):
    """Handle /settings command"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    settings_text = f"""⚙️ **Moderation Settings**

Chat ID: `{chat_id}`

✅ Photo Scan: {'Enabled' if settings['photo_scan'] else 'Disabled'}
{'✅' if settings['video_scan'] else '❌'} Video Scan: {'Enabled' if settings['video_scan'] else 'Disabled'}
{'✅' if settings['gif_scan'] else '❌'} GIF Scan: {'Enabled' if settings['gif_scan'] else 'Disabled'}
{'✅' if settings['sticker_scan'] else '❌'} Sticker Scan: {'Enabled' if settings['sticker_scan'] else 'Disabled'}
{'✅' if settings['delete_on_detect'] else '❌'} Auto-Delete: {'Enabled' if settings['delete_on_detect'] else 'Disabled'}"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Toggle All", callback_data="toggle_all")],
        [
            InlineKeyboardButton("📷 Photos", callback_data="toggle_photo"),
            InlineKeyboardButton("🎥 Videos", callback_data="toggle_video")
        ],
        [
            InlineKeyboardButton("🎬 GIFs", callback_data="toggle_gif"),
            InlineKeyboardButton("🏷️ Stickers", callback_data="toggle_sticker")
        ],
        [InlineKeyboardButton("🗑️ Auto-Delete", callback_data="toggle_delete")]
    ])
    
    await message.reply(settings_text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^toggle_(.*)"))
async def toggle_callback(client: Client, callback_query):
    """Handle settings toggle buttons"""
    chat_id = callback_query.message.chat.id
    setting = callback_query.matches[0].group(1)
    settings = get_chat_settings(chat_id)
    
    if setting == "all":
        new_state = not all([settings[k] for k in settings if k != "chat_id"])
        for key in settings:
            if key != "chat_id":
                settings[key] = new_state
    elif setting in settings:
        settings[setting] = not settings[setting]
    
    await settings_command(client, callback_query.message)
    await callback_query.answer()


@app.on_message(filters.photo)
async def photo_handler(client: Client, message: Message):
    """Handle photo messages with async worker"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('photo_scan', True):
        return
    
    if message.photo.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        
        # Process with async worker
        result = await worker_pool.process_media(tmp_path, 'photo')
        
        await handle_nsfw_detection(message, result)
        
    except Exception as e:
        print(f"Error processing photo: {e}")
        try:
            os.remove(tmp_path)
        except:
            pass


@app.on_message(filters.animation)
async def gif_handler(client: Client, message: Message):
    """Handle animated GIFs with optimized frame scanning"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('gif_scan', False):
        return
    
    if message.animation.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        
        # Process every 3rd frame for speed
        result = await worker_pool.process_media(tmp_path, 'animation')
        
        await handle_nsfw_detection(message, result)
        
    except Exception as e:
        print(f"Error processing GIF: {e}")
        try:
            os.remove(tmp_path)
        except:
            pass


@app.on_message(filters.sticker)
async def sticker_handler(client: Client, message: Message):
    """
    Handle stickers with auto-detection of type
    Supports: Static WebP, Animated WebP, TGS, Video WebM
    """
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('sticker_scan', False):
        return
    
    if message.sticker.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    sticker = message.sticker
    file_ext = ".webp"
    
    # Detect sticker format
    if sticker.format and sticker.format.value == 2:  # TGS (Lottie)
        file_ext = ".tgs"
    elif sticker.format and sticker.format.value == 3:  # Video sticker
        file_ext = ".webm"
    
    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        
        # Determine media type
        if file_ext == ".tgs":
            media_type = "sticker"  # Will auto-detect as TGS
        elif file_ext == ".webm":
            media_type = "sticker"  # Will auto-detect as video sticker
        else:
            # Check if animated WebP
            try:
                from PIL import Image
                img = Image.open(tmp_path)
                if hasattr(img, 'n_frames') and img.n_frames > 1:
                    media_type = "animation"
                else:
                    media_type = "photo"
            except:
                media_type = "photo"
        
        # Process with async worker
        result = await worker_pool.process_media(tmp_path, media_type)
        
        await handle_nsfw_detection(message, result)
        
    except Exception as e:
        print(f"Error processing sticker: {e}")
        try:
            os.remove(tmp_path)
        except:
            pass


@app.on_message(filters.video)
async def video_handler(client: Client, message: Message):
    """Handle video messages with frame extraction"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('video_scan', False):
        return
    
    if message.video.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        
        # Process every 5th frame for videos
        result = await worker_pool.process_media(tmp_path, 'video')
        
        await handle_nsfw_detection(message, result)
        
    except Exception as e:
        print(f"Error processing video: {e}")
        try:
            os.remove(tmp_path)
        except:
            pass


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 NSFW Moderation Bot - OPTIMIZED")
    print("=" * 50)
    print(f"   Temp directory: {TEMP_DIR}")
    print(f"   Max file size: {MAX_FILE_SIZE_MB}MB")
    print(f"   Worker pool: {worker_pool.max_workers} workers")
    print(f"   GPU acceleration: Enabled")
    print("=" * 50)
    
    app.run()
