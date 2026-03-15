"""
NSFW Moderation Bot - Pyrogram Version
UNIFIED SETTINGS with ALL features in ONE command
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
import os
import tempfile
import time

from config import (
    API_ID, API_HASH, BOT_TOKEN, NSFW_THRESHOLD,
    MAX_FILE_SIZE_MB, TEMP_DIR, FRAME_SAMPLE_RATE, GIF_FRAME_SAMPLE
)
from async_worker import worker_pool
from sticker_cache import check_sticker_once, sticker_cache, get_cache_info_text


# Initialize bot
app = Client(
    "nsfw-moderator",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Chat settings storage (in-memory)
chat_settings = {}


def get_chat_settings(chat_id: int) -> dict:
    """Get or create chat settings"""
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {
            "photo_scan": True,          # Scan photos
            "video_scan": False,         # Scan videos
            "gif_scan": False,           # Scan GIFs/animations
            "sticker_scan": False,       # Scan stickers (static + animated)
            "text_scan": True,           # Scan text for profanity
            "delete_on_detect": True,    # Auto-delete NSFW content
            "warn_user": True,           # Warn user when NSFW detected
            "log_to_channel": False,     # Log detections to channel
            "nsfw_threshold": 0.7,       # Detection threshold
            "frame_sample_rate": 3,      # Check every Nth frame
        }
    return chat_settings[chat_id]


def create_main_settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Create main settings inline keyboard"""
    settings = get_chat_settings(chat_id)
    
    # Status icons
    on = "✅"
    off = "❌"
    
    keyboard = [
        # Header
        [InlineKeyboardButton("⚙️ NSFW Moderation Settings", callback_data="header")],
        
        # Media Scanning Settings (2x2 grid)
        [
            InlineKeyboardButton(f"{on if settings['photo_scan'] else off} Photos", callback_data="toggle_photo"),
            InlineKeyboardButton(f"{on if settings['video_scan'] else off} Videos", callback_data="toggle_video")
        ],
        [
            InlineKeyboardButton(f"{on if settings['gif_scan'] else off} GIFs", callback_data="toggle_gif"),
            InlineKeyboardButton(f"{on if settings['sticker_scan'] else off} Stickers", callback_data="toggle_sticker")
        ],
        
        # Action Settings
        [
            InlineKeyboardButton(f"{on if settings['delete_on_detect'] else off} Auto-Delete", callback_data="toggle_delete"),
            InlineKeyboardButton(f"{on if settings['warn_user'] else off} Warn User", callback_data="toggle_warn")
        ],
        
        # Advanced Settings Row
        [
            InlineKeyboardButton(f"🎯 Threshold: {settings['nsfw_threshold']}", callback_data="set_threshold"),
            InlineKeyboardButton(f"📊 Sample: Every {settings['frame_sample_rate']} frames", callback_data="set_sample")
        ],
        
        # Quick Actions
        [
            InlineKeyboardButton("🔄 Enable All", callback_data="enable_all"),
            InlineKeyboardButton("⏹️ Disable All", callback_data="disable_all")
        ],
        
        # Cache & Stats
        [InlineKeyboardButton("💾 Cache Stats", callback_data="cache_stats")],
        
        # Close button
        [InlineKeyboardButton("❌ Close", callback_data="close_settings")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_settings_text(chat_id: int) -> str:
    """Generate settings summary text"""
    settings = get_chat_settings(chat_id)
    
    status = []
    status.append(f"📊 **Current Configuration**\n")
    status.append(f"**Chat ID:** `{chat_id}`\n")
    status.append(f"**NSFW Threshold:** {settings['nsfw_threshold']:.2f}")
    status.append(f"**Frame Sampling:** Every {settings['frame_sample_rate']} frames\n")
    
    status.append(f"\n🔍 **Scanning Options:**")
    status.append(f"  {'✅' if settings['photo_scan'] else '❌'} Photos")
    status.append(f"  {'✅' if settings['video_scan'] else '❌'} Videos")
    status.append(f"  {'✅' if settings['gif_scan'] else '❌'} GIFs/Animations")
    status.append(f"  {'✅' if settings['sticker_scan'] else '❌'} Stickers")
    status.append(f"  {'✅' if settings['text_scan'] else '❌'} Text Profanity")
    
    status.append(f"\n⚡ **Actions:**")
    status.append(f"  {'✅' if settings['delete_on_detect'] else '❌'} Auto-Delete NSFW")
    status.append(f"  {'✅' if settings['warn_user'] else '❌'} Warn Users")
    status.append(f"  {'✅' if settings['log_to_channel'] else '❌'} Log to Channel")
    
    return "\n".join(status)


async def handle_toggle(callback_query: CallbackQuery, setting_key: str):
    """Handle toggle button press"""
    chat_id = callback_query.message.chat.id
    settings = get_chat_settings(chat_id)
    
    # Toggle the setting
    if setting_key in settings:
        settings[setting_key] = not settings[setting_key]
        
        # Show confirmation
        status = "Enabled" if settings[setting_key] else "Disabled"
        await callback_query.answer(f"{setting_key.replace('_', ' ').title()} {status}", show_alert=False)
        
        # Update message with new keyboard
        new_keyboard = create_main_settings_keyboard(chat_id)
        new_text = get_settings_text(chat_id)
        
        await callback_query.message.edit_text(
            new_text,
            reply_markup=new_keyboard,
            parse_mode="markdown"
        )


async def handle_enable_all(callback_query: CallbackQuery):
    """Enable all scanning features"""
    chat_id = callback_query.message.chat.id
    settings = get_chat_settings(chat_id)
    
    # Enable all scanning options
    settings['photo_scan'] = True
    settings['video_scan'] = True
    settings['gif_scan'] = True
    settings['sticker_scan'] = True
    settings['text_scan'] = True
    
    await callback_query.answer("✅ All features enabled!", show_alert=True)
    
    # Update UI
    new_keyboard = create_main_settings_keyboard(chat_id)
    new_text = get_settings_text(chat_id)
    await callback_query.message.edit_text(new_text, reply_markup=new_keyboard, parse_mode="markdown")


async def handle_disable_all(callback_query: CallbackQuery):
    """Disable all scanning features"""
    chat_id = callback_query.message.chat.id
    settings = get_chat_settings(chat_id)
    
    # Disable all scanning options
    settings['photo_scan'] = False
    settings['video_scan'] = False
    settings['gif_scan'] = False
    settings['sticker_scan'] = False
    settings['text_scan'] = False
    
    await callback_query.answer("⏹️ All features disabled!", show_alert=True)
    
    # Update UI
    new_keyboard = create_main_settings_keyboard(chat_id)
    new_text = get_settings_text(chat_id)
    await callback_query.message.edit_text(new_text, reply_markup=new_keyboard, parse_mode="markdown")


async def handle_threshold_change(callback_query: CallbackQuery):
    """Show threshold selection buttons"""
    chat_id = callback_query.message.chat.id
    settings = get_chat_settings(chat_id)
    
    current = settings['nsfw_threshold']
    
    keyboard = [
        [
            InlineKeyboardButton("0.5 (Strict)", callback_data="threshold_0.5"),
            InlineKeyboardButton("0.6", callback_data="threshold_0.6"),
            InlineKeyboardButton("0.7 (Balanced)", callback_data="threshold_0.7")
        ],
        [
            InlineKeyboardButton("0.8", callback_data="threshold_0.8"),
            InlineKeyboardButton("0.9 (Lenient)", callback_data="threshold_0.9")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_settings")]
    ]
    
    await callback_query.message.edit_text(
        f"🎯 **Set NSFW Detection Threshold**\n\n"
        f"Current: **{current:.2f}**\n\n"
        f"Lower = Stricter (more detections)\n"
        f"Higher = More lenient (fewer false positives)\n\n"
        f"Select a value:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="markdown"
    )


async def handle_sample_change(callback_query: CallbackQuery):
    """Show frame sampling selection buttons"""
    chat_id = callback_query.message.chat.id
    settings = get_chat_settings(chat_id)
    
    current = settings['frame_sample_rate']
    
    keyboard = [
        [
            InlineKeyboardButton("Every 2nd (Best)", callback_data="sample_2"),
            InlineKeyboardButton("Every 3rd (Fast)", callback_data="sample_3")
        ],
        [
            InlineKeyboardButton("Every 4th", callback_data="sample_4"),
            InlineKeyboardButton("Every 5th (Faster)", callback_data="sample_5")
        ],
        [
            InlineKeyboardButton("Every 10th (Fastest)", callback_data="sample_10")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_settings")]
    ]
    
    await callback_query.message.edit_text(
        f"📊 **Set Frame Sampling Rate**\n\n"
        f"Current: Every **{current}** frames\n\n"
        f"Lower number = More accurate but slower\n"
        f"Higher number = Faster but less accurate\n\n"
        f"Select sampling rate:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="markdown"
    )


async def handle_cache_stats(callback_query: CallbackQuery):
    """Show cache statistics"""
    stats = sticker_cache.get_cache_stats()
    
    text = get_cache_info_text()
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Clear Cache", callback_data="clear_cache")],
        [InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")]
    ]
    
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="markdown"
    )


async def handle_clear_cache(callback_query: CallbackQuery):
    """Clear the sticker cache"""
    sticker_cache.clear_cache()
    await callback_query.answer("🗑️ Cache cleared!", show_alert=True)
    
    # Return to settings
    chat_id = callback_query.message.chat.id
    new_keyboard = create_main_settings_keyboard(chat_id)
    new_text = get_settings_text(chat_id)
    await callback_query.message.edit_text(new_text, reply_markup=new_keyboard, parse_mode="markdown")


# Main settings command handler
@app.on_message(filters.command("settings"))
async def settings_command(client: Client, message: Message):
    """Unified settings menu - ALL settings in one command"""
    chat_id = message.chat.id
    
    text = get_settings_text(chat_id)
    keyboard = create_main_settings_keyboard(chat_id)
    
    await message.reply(text, reply_markup=keyboard, parse_mode="markdown")


# Unified callback query handler for ALL settings buttons
@app.on_callback_query(filters.regex(r"^(toggle_|enable_|disable_|threshold_|sample_|back_|close_|cache_|clear_)"))
async def settings_callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle all settings button clicks"""
    data = callback_query.data
    
    if data.startswith("toggle_"):
        setting_key = data.replace("toggle_", "")
        await handle_toggle(callback_query, setting_key)
    
    elif data == "enable_all":
        await handle_enable_all(callback_query)
    
    elif data == "disable_all":
        await handle_disable_all(callback_query)
    
    elif data == "set_threshold":
        await handle_threshold_change(callback_query)
    
    elif data.startswith("threshold_"):
        # User selected a threshold value
        new_threshold = float(data.replace("threshold_", ""))
        chat_id = callback_query.message.chat.id
        settings = get_chat_settings(chat_id)
        settings['nsfw_threshold'] = new_threshold
        
        await callback_query.answer(f"Threshold set to {new_threshold}", show_alert=True)
        
        # Return to main settings
        new_keyboard = create_main_settings_keyboard(chat_id)
        new_text = get_settings_text(chat_id)
        await callback_query.message.edit_text(new_text, reply_markup=new_keyboard, parse_mode="markdown")
    
    elif data.startswith("sample_"):
        # User selected a sample rate
        new_sample = int(data.replace("sample_", ""))
        chat_id = callback_query.message.chat.id
        settings = get_chat_settings(chat_id)
        settings['frame_sample_rate'] = new_sample
        
        await callback_query.answer(f"Sample rate set to every {new_sample} frames", show_alert=True)
        
        # Return to main settings
        new_keyboard = create_main_settings_keyboard(chat_id)
        new_text = get_settings_text(chat_id)
        await callback_query.message.edit_text(new_text, reply_markup=new_keyboard, parse_mode="markdown")
    
    elif data == "back_to_settings":
        # Return to main settings menu
        chat_id = callback_query.message.chat.id
        text = get_settings_text(chat_id)
        keyboard = create_main_settings_keyboard(chat_id)
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="markdown")
    
    elif data == "close_settings":
        await callback_query.message.delete()
    
    elif data == "cache_stats":
        await handle_cache_stats(callback_query)
    
    elif data == "clear_cache":
        await handle_clear_cache(callback_query)


# Rest of the bot handlers remain the same...
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
    """Handle /start command with bot's profile picture"""
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
• One-time sticker check with caching

Use /settings to configure ALL options in one place!"""
    
    try:
        # Get bot's profile photo
        bot_profile = await client.get_chat("me")
        photo_id = bot_profile.photo.big_file_id if bot_profile.photo else None
        
        if photo_id:
            # Send photo with caption
            await client.send_photo(
                chat_id=message.chat.id,
                photo=photo_id,
                caption=welcome_text,
                parse_mode="markdown"
            )
        else:
            # No profile photo, send text only
            await message.reply(welcome_text)
    except Exception as e:
        print(f"Error sending profile photo: {e}")
        # Fallback to text message
        await message.reply(welcome_text)


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
async def sticker_handler_cached(client: Client, message: Message):
    """
    Handle stickers with ONE-TIME check and caching
    Each unique sticker is scanned only once!
    """
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('sticker_scan', False):
        return
    
    if message.sticker.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return
    
    sticker = message.sticker
    file_id = sticker.file_id
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
        
        # Use ONE-TIME check with caching!
        is_nsfw, score, method = await check_sticker_once(
            file_id,
            tmp_path,
            None
        )
        
        result = {
            'is_nsfw': is_nsfw,
            'score': score,
            'method': method,
            'frames_analyzed': 1 if method == "cached_result" else 8
        }
        
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
    print("🚀 NSFW Moderation Bot - UNIFIED SETTINGS")
    print("=" * 50)
    print(f"   Temp directory: {TEMP_DIR}")
    print(f"   Max file size: {MAX_FILE_SIZE_MB}MB")
    print(f"   Worker pool: {worker_pool.max_workers} workers")
    print(f"   GPU acceleration: Enabled")
    print(f"   Sticker caching: Enabled (7 days)")
    print("=" * 50)
    
    app.run()
