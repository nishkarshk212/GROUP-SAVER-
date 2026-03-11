"""
Unified Settings Command for Pyrogram Bot
All settings accessible via single /settings command with inline buttons
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import NSFW_THRESHOLD


# In-memory chat settings storage
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


def create_settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Create inline keyboard for settings"""
    settings = get_chat_settings(chat_id)
    
    # Status icons
    on = "✅"
    off = "❌"
    
    keyboard = [
        # Header
        [InlineKeyboardButton("⚙️ NSFW Moderation Settings", callback_data="header")],
        
        # Media Scanning Settings
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
        
        # Advanced Settings
        [
            InlineKeyboardButton(f"{on if settings['text_scan'] else off} Text Scan", callback_data="toggle_text"),
            InlineKeyboardButton(f"{on if settings['log_to_channel'] else off} Log Channel", callback_data="toggle_log")
        ],
        
        # Threshold & Sampling
        [
            InlineKeyboardButton(f"🎯 Threshold: {settings['nsfw_threshold']}", callback_data="set_threshold"),
            InlineKeyboardButton(f"📊 Sample: Every {settings['frame_sample_rate']} frames", callback_data="set_sample")
        ],
        
        # Quick Actions
        [
            InlineKeyboardButton("🔄 Enable All", callback_data="enable_all"),
            InlineKeyboardButton("⏹️ Disable All", callback_data="disable_all")
        ],
        
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
        new_keyboard = create_settings_keyboard(chat_id)
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
    new_keyboard = create_settings_keyboard(chat_id)
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
    new_keyboard = create_settings_keyboard(chat_id)
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
