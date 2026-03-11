"""
NSFW Moderation Bot - Pyrogram Version
Uses Redis Queue for async processing
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os
import tempfile
from datetime import datetime

from config import (
    API_ID, API_HASH, BOT_TOKEN, NSFW_THRESHOLD,
    MAX_FILE_SIZE_MB, TEMP_DIR
)
from frames import convert_tgs_to_gif, cleanup_files
from worker import process_media_task


# Initialize bot
app = Client(
    "nsfw-moderator",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Chat settings storage (in production, use database)
chat_settings = {}


def get_chat_settings(chat_id: int) -> dict:
    """Get settings for a chat"""
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


async def enqueue_for_processing(message: Message, media_type: str, file_path: str):
    """Enqueue media for async NSFW processing"""
    task_data = {
        'file_path': file_path,
        'media_type': media_type,
        'message_id': message.id,
        'chat_id': message.chat.id,
        'user_id': message.from_user.id if message.from_user else None
    }
    
    # Process synchronously for now (later: use Redis queue)
    result = await asyncio.to_thread(process_media_task, task_data)
    
    # Handle result
    if result.get('is_nsfw'):
        await handle_nsfw_detection(message, result)


async def handle_nsfw_detection(message: Message, result: dict):
    """Handle NSFW content detection"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    # Delete message if enabled
    if settings.get('delete_on_detect', True):
        try:
            await message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")
    
    # Warn user if enabled
    if settings.get('warn_user', True):
        score = result.get('score', 0.0)
        method = result.get('method', 'analysis')
        frames = result.get('frames_analyzed', 1)
        
        warning_text = (
            f"🚫 **NSFW Content Detected**\n\n"
            f"User ID: `{message.from_user.id}`\n"
            f"Confidence: {score:.2%}\n"
            f"Method: {method}\n"
            f"Frames Analyzed: {frames}"
        )
        
        try:
            await message.reply(warning_text, delete_after=10)
        except Exception as e:
            print(f"Error sending warning: {e}")


@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    welcome_text = (
        "🤖 **NSFW Moderation Bot**\n\n"
        "I can detect and moderate NSFW content including:\n"
        "• Photos\n"
        "• Videos\n"
        "• GIFs\n"
        "• Stickers (including animated)\n\n"
        "Use /settings to configure moderation options."
    )
    
    await message.reply(welcome_text)


@app.on_message(filters.command("settings"))
async def settings_command(client: Client, message: Message):
    """Handle /settings command"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    settings_text = (
        f"⚙️ **Moderation Settings**\n\n"
        f"Chat ID: `{chat_id}`\n\n"
        f"✅ Photo Scan: {'Enabled' if settings['photo_scan'] else 'Disabled'}\n"
        f"{'✅' if settings['video_scan'] else '❌'} Video Scan: {'Enabled' if settings['video_scan'] else 'Disabled'}\n"
        f"{'✅' if settings['gif_scan'] else '❌'} GIF Scan: {'Enabled' if settings['gif_scan'] else 'Disabled'}\n"
        f"{'✅' if settings['sticker_scan'] else '❌'} Sticker Scan: {'Enabled' if settings['sticker_scan'] else 'Disabled'}\n"
        f"{'✅' if settings['text_scan'] else '❌'} Text Scan: {'Enabled' if settings['text_scan'] else 'Disabled'}\n"
        f"{'✅' if settings['delete_on_detect'] else '❌'} Auto-Delete: {'Enabled' if settings['delete_on_detect'] else 'Disabled'}\n"
        f"{'✅' if settings['warn_user'] else '❌'} Warn User: {'Enabled' if settings['warn_user'] else 'Disabled'}"
    )
    
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
        # Toggle all settings
        new_state = not all(settings.values())
        for key in settings:
            settings[key] = new_state
    elif setting in settings:
        settings[setting] = not settings[setting]
    
    # Update message
    await settings_command(client, callback_query.message)
    await callback_query.answer()


@app.on_message(filters.photo)
async def photo_handler(client: Client, message: Message):
    """Handle photo messages"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('photo_scan', True):
        return
    
    # Check file size
    if message.photo.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    # Download file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        await enqueue_for_processing(message, 'photo', tmp_path)
    except Exception as e:
        print(f"Error processing photo: {e}")
        try:
            os.remove(tmp_path)
        except:
            pass


@app.on_message(filters.animation)
async def gif_handler(client: Client, message: Message):
    """Handle animated GIFs"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('gif_scan', False):
        return
    
    # Check file size
    if message.animation.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    # Download file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        await enqueue_for_processing(message, 'animation', tmp_path)
    except Exception as e:
        print(f"Error processing GIF: {e}")
        try:
            os.remove(tmp_path)
        except:
            pass


@app.on_message(filters.video)
async def video_handler(client: Client, message: Message):
    """Handle video messages"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('video_scan', False):
        return
    
    # Check file size
    if message.video.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    # Download file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        await enqueue_for_processing(message, 'video', tmp_path)
    except Exception as e:
        print(f"Error processing video: {e}")
        try:
            os.remove(tmp_path)
        except:
            pass


@app.on_message(filters.sticker)
async def sticker_handler(client: Client, message: Message):
    """Handle stickers (static, animated, TGS, video)"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('sticker_scan', False):
        return
    
    # Check file size
    if message.sticker.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    # Download file
    sticker = message.sticker
    file_ext = ".webp"
    
    if sticker.format and sticker.format.value == 2:  # TGS
        file_ext = ".tgs"
    elif sticker.format and sticker.format.value == 3:  # Video sticker
        file_ext = ".webm"
    
    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        
        # Convert TGS to GIF if needed
        if file_ext == ".tgs":
            gif_path = convert_tgs_to_gif(tmp_path)
            if gif_path:
                await enqueue_for_processing(message, 'animation', gif_path)
                try:
                    os.remove(tmp_path)
                except:
                    pass
                return
        
        await enqueue_for_processing(message, 'sticker', tmp_path)
    except Exception as e:
        print(f"Error processing sticker: {e}")
        try:
            os.remove(tmp_path)
        except:
            pass


@app.on_message(filters.text)
async def text_handler(client: Client, message: Message):
    """Handle text messages for profanity"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('text_scan', True):
        return
    
    # TODO: Add profanity detection here
    pass


if __name__ == "__main__":
    print("🚀 Starting NSFW Moderation Bot...")
    print(f"   Temp directory: {TEMP_DIR}")
    print(f"   Max file size: {MAX_FILE_SIZE_MB}MB")
    app.run()
