import os
import re
import asyncio
import tempfile
import unicodedata
from typing import Dict, Set
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)
from nudenet import NudeDetector
import torch
from PIL import Image

# Try to load YOLOv5 for weapon/drug detection
try:
    weapon_drug_model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, verbose=False)
    WEAPON_DETECTION_ENABLED = True
except Exception:
    WEAPON_DETECTION_ENABLED = False
    weapon_drug_model = None

# Leetspeak conversion map
LEET_MAP = {
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    "@": "a", "$": "s", "!": "i", "+": "t"
}

# NSFW emojis to detect
NSFW_EMOJIS = ["🍑", "🍆", "💦", "🔞", "😈", "👅", "🌭"]

# Extended NSFW word list
NSFW_WORDS = [
    "sex", "porn", "nude", "nudes", "xxx", "hentai", "blowjob", "anal",
    "fetish", "cum", "sperm", "cock", "pussy", "tits", "boobs", "lingerie",
    "erotic", "camgirl", "onlyfans", "fap", "naked", "hot", "milf", "teen",
    "dick", "ass", "butt", "thot", "slut", "whore", "bitch"
]

# Drug-related words
DRUG_WORDS = [
    "drug", "weed", "marijuana", "cannabis", "cocaine", "crack", "heroin",
    "mdma", "molly", "ecstasy", "ketamine", "xanax", "adderall", "oxy",
    "oxycodone", "opioid", "meth", "crystal", "ice", "lsd", "acid", "shrooms",
    "psilocybin", "dmt", "fentanyl", "tramadol", "ritalin", "benzos", "benzo",
    "pill", "pharmacy", "420", "high", "stoned"
]

# Abuse/hate words (common examples)
ABUSE_WORDS = [
    "stupid", "idiot", "dumb", "moron", "retard", "loser", "failure",
    "worthless", "pathetic", "disgusting", "hate", "kill", "die", "suicide"
]

# Weapon detection objects
WEAPON_OBJECTS = ["knife", "gun", "pistol", "rifle", "sword", "weapon", "firearm"]

# Drug objects for image detection
DRUG_OBJECTS = ["syringe", "pill", "drug", "powder", "capsule", "tablet"]

nsfw_re = re.compile(
    r"(?i)\b(?:porn|xxx|nude|nudity|sex|hentai|blowjob|anal|fetish|cum|sperm|cock|pussy|tits|boobs|lingerie|erotic|camgirl|onlyfans|fap|nudes)\b"
)
drug_re = re.compile(
    r"(?i)\b(?:drug|weed|marijuana|cannabis|cocaine|crack|heroin|mdma|molly|ecstasy|ketamine|xanax|adderall|oxy|oxycodone|opioid|meth|crystal|ice|lsd|acid|shrooms|psilocybin|dmt|fentanyl|tramadol|ritalin|benzos|benzo|pill|pharmacy)\b"
)

alerted_users_per_chat: Dict[int, Set[int]] = {}
_pfp_scan_cache: Dict[int, bool] = {}
_nude_detector = NudeDetector()

# Global settings for each chat
chat_settings: Dict[int, Dict[str, bool]] = {}


def get_chat_settings(chat_id: int) -> Dict[str, bool]:
   if chat_id not in chat_settings:
       chat_settings[chat_id] = {
            # Image Scanning Features
            "pfp_scan": True,           # Profile photo NSFW scan
            "image_scan": True,          # General image NSFW scan
            "weapon_scan": True,         # Weapon detection in images
            "drug_scan": True,           # Drug detection in images
            
            # Text Scanning Features
            "text_scan": True,           # Text content NSFW/drug/abuse scan
            "media_scan": True,          # Media file names and captions
            
            # User Detection Features (Silent)
            "username_detect": True,     # Track usernames (silent)
            "name_detect": True,         # Track names (silent)
            
            # Protection Features
            "voice_invite_scan": True,   # Voice chat invite screening
        }
   return chat_settings[chat_id]


def load_env_from_file(path: str = ".env") -> None:
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        return
    try:
        with open(path, "r") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if "=" in s:
                    k, v = s.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k and v and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass


def normalize_text(text: str) -> str:
    """
    Advanced text normalization to detect bypass attempts.
    Handles: unicode fonts, leetspeak, spaces, symbols, repeated letters
    """
    # Normalize unicode (convert fancy fonts to ASCII)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace leetspeak characters
    for leet, char in LEET_MAP.items():
        text = text.replace(leet, char)
    
    # Remove all non-alphabetic characters (spaces, symbols, dots, etc.)
    text = re.sub(r'[^a-z]', '', text)
    
    # Reduce repeated letters (e.g., "seeeex" → "sex")
    text = re.sub(r'(.)\1+', r'\1', text)
    
    return text


def detect_nsfw_advanced(text: str) -> bool:
    """
    Advanced NSFW detection with normalization and emoji detection.
    """
    if not text:
        return False
    
    # Check for NSFW emojis first
    for emoji in NSFW_EMOJIS:
        if emoji in text:
            return True
    
    # Normalize and check against word lists
    cleaned = normalize_text(text)
    
    # Check NSFW words
    for word in NSFW_WORDS:
        if word in cleaned:
            return True
    
    # Check drug words
    for word in DRUG_WORDS:
        if word in cleaned:
            return True
    
    # Check abuse words
    for word in ABUSE_WORDS:
        if word in cleaned:
            return True
    
    # Also check with original regex for backward compatibility
    if nsfw_re.search(text) or drug_re.search(text):
        return True
    
    return False


def text_has_nsfw(text: str) -> bool:
    """Legacy function - now uses advanced detection"""
    return detect_nsfw_advanced(text)


def profile_has_drug(user: User) -> bool:
    """Check user profile for drug-related terms"""
    parts = []
    if user.first_name:
        parts.append(user.first_name)
    if user.last_name:
        parts.append(user.last_name)
    parts.append(user.username or "")
    combined = " ".join(parts)
    return bool(drug_re.search(combined)) or detect_nsfw_advanced(combined)


def profile_has_nsfw(user: User) -> bool:
    """Check user profile for NSFW/drug/abuse terms"""
    parts = []
    if user.first_name:
        parts.append(user.first_name)
    if user.last_name:
        parts.append(user.last_name)
    parts.append(user.username or "")
    combined = " ".join(parts)
    return detect_nsfw_advanced(combined)


async def _auto_delete(message, seconds: int) -> None:
    try:
        await asyncio.sleep(seconds)
        await message.delete()
    except Exception:
        pass

async def send_temp(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, seconds: int = 10):
    try:
        m = await context.bot.send_message(chat_id=chat_id, text=text)
        asyncio.create_task(_auto_delete(m, seconds))
        return m
    except Exception:
        return None

def get_user_info(user: User) -> str:
    """Get formatted user info including username and name"""
    parts = []
    if user.first_name:
        parts.append(f"First Name: {user.first_name}")
    if user.last_name:
        parts.append(f"Last Name: {user.last_name}")
    if user.username:
        parts.append(f"Username: @{user.username}")
    if not parts:
        parts.append(f"User ID: {user.id}")
    return " | ".join(parts)

async def warn_and_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str) -> None:
    msg = update.effective_message
    if not msg:
        return
    user_id = None
    user_info_text = ""
    try:
        if msg.from_user:
            user_id = msg.from_user.id
            settings_dict = get_chat_settings(msg.chat.id)
            # Build user info text based on settings
            if settings_dict["username_detect"] or settings_dict["name_detect"]:
                user_info_parts = []
                if settings_dict["name_detect"] and msg.from_user.first_name:
                    user_info_parts.append(f"Name: {msg.from_user.first_name}")
                    if msg.from_user.last_name:
                        user_info_parts[-1] += f" {msg.from_user.last_name}"
                if settings_dict["username_detect"] and msg.from_user.username:
                    user_info_parts.append(f"@{msg.from_user.username}")
                if user_info_parts:
                    user_info_text = " | ".join(user_info_parts)
    except Exception:
        user_id = None
    try:
        await msg.delete()
    except Exception:
        pass
    try:
        chat_id = msg.chat.id
        if user_id is not None:
            if user_info_text:
                await send_temp(context, chat_id, f"Moderation: {user_info_text} (ID={user_id}) content removed ({reason}).", 10)
            else:
                await send_temp(context, chat_id, f"Moderation: user_id={user_id} content removed ({reason}).", 10)
        else:
            await send_temp(context, chat_id, f"Moderation: content removed ({reason}).", 10)
    except Exception:
        pass


async def user_profile_is_nsfw(user_id: int, context: ContextTypes.DEFAULT_TYPE, threshold: float = 0.7) -> bool:
    if user_id in _pfp_scan_cache:
        return _pfp_scan_cache[user_id]
    try:
        photos = await context.bot.get_user_profile_photos(user_id=user_id, limit=1)
        if not photos or not photos.total_count:
            _pfp_scan_cache[user_id] = False
            return False
        first = photos.photos[0] if photos.photos else []
        if not first:
            _pfp_scan_cache[user_id] = False
            return False
        file_id = first[-1].file_id
        tg_file = await context.bot.get_file(file_id)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            await tg_file.download_to_drive(custom_path=tmp_path)
            result = _nude_detector.detect(tmp_path) or []
            nsfw_detected = any(d.get("score", 0.0) >= threshold for d in result)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        _pfp_scan_cache[user_id] = nsfw_detected
        return nsfw_detected
    except Exception:
        _pfp_scan_cache[user_id] = False
        return False


async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg:
        return
    
    settings_dict = get_chat_settings(msg.chat.id)
    if not settings_dict["pfp_scan"]:
        return

    for user in msg.new_chat_members or []:
        if not user or user.is_bot:
            continue
        
        # Check for NSFW/drug terms in username/name FIRST
        if profile_has_nsfw(user) or profile_has_drug(user):
            # Send warning with ONLY User ID (no name/username shown)
            await send_temp(context, msg.chat.id, f"⚠️ Moderation: User ID `{user.id}` - NSFW/inappropriate terms detected. User will be removed.", 10)
            try:
                await context.bot.ban_chat_member(chat_id=msg.chat.id, user_id=user.id)
            except Exception:
                pass
            return
        
        if await user_profile_is_nsfw(user.id, context):
            await warn_and_delete(update, context, "NSFW profile photo detected")
            return

 
async def handle_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.left_chat_member:
        return
    
    settings_dict = get_chat_settings(msg.chat.id)
    if not settings_dict["pfp_scan"]:
        return

    user = msg.left_chat_member
    if user and not user.is_bot:
        if await user_profile_is_nsfw(user.id, context):
            await warn_and_delete(update, context, "NSFW profile photo detected")
            return
        if profile_has_drug(user) or profile_has_nsfw(user):
            await warn_and_delete(update, context, "User has restricted terms in name/username")
 
 
async def handle_voice_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.video_chat_participants_invited:
        return
    
    settings_dict = get_chat_settings(msg.chat.id)
    
    # Check if voice invite scanning is enabled
    if not settings_dict["voice_invite_scan"]:
        return
    
    vcpi = msg.video_chat_participants_invited
    users = getattr(vcpi, "users", []) if vcpi else []
    for user in users:
        if not user or user.is_bot:
            continue
        
        # Check for NSFW/drug terms in username/name FIRST
        if profile_has_nsfw(user) or profile_has_drug(user):
            # Send warning with ONLY User ID (no name/username shown)
            await send_temp(context, msg.chat.id, f"⚠️ Moderation: User ID `{user.id}` - NSFW/inappropriate terms detected. Invitation blocked.", 10)
            return
        
        if await user_profile_is_nsfw(user.id, context):
            await warn_and_delete(update, context, "Invited user has NSFW profile photo")
            return


async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if not msg:
        return
    
    chat_id = msg.chat.id
    settings_dict = get_chat_settings(chat_id)
    
    # CRITICAL: Check for NSFW/drug terms in username/name FIRST on EVERY message
    if msg.from_user and not msg.from_user.is_bot:
        # Check if username or name contains NSFW/drug terms
        if profile_has_nsfw(msg.from_user) or profile_has_drug(msg.from_user):
            # Delete the message immediately
            try:
                await msg.delete()
            except Exception:
                pass
            
            # Send warning with ONLY User ID (no name/username shown)
            await send_temp(context, chat_id, f"⚠️ Moderation: User ID `{msg.from_user.id}` - NSFW/inappropriate terms detected. Message deleted.", 10)
            return
    
    # Check profile photo
    if settings_dict["pfp_scan"] and msg.from_user and not msg.from_user.is_bot:
        if await user_profile_is_nsfw(msg.from_user.id, context):
            await warn_and_delete(update, context, "NSFW profile photo detected")
            return
            
    if not settings_dict["text_scan"] and not settings_dict["media_scan"]:
        return
            
    # Collect all text content
    if settings_dict["text_scan"]:
        content_parts = []
        if msg.text:
            content_parts.append(msg.text)
        if msg.caption:
            content_parts.append(msg.caption)
        if msg.poll and msg.poll.question:
            content_parts.append(msg.poll.question)
            for opt in msg.poll.options:
                content_parts.append(opt.text)
        if msg.document and msg.document.file_name:
            content_parts.append(msg.document.file_name)
        if msg.audio:
            if msg.audio.title:
                content_parts.append(msg.audio.title)
            if msg.audio.performer:
                content_parts.append(msg.audio.performer)
        if msg.video and msg.video.file_name:
            content_parts.append(msg.video.file_name)
        
        combined_text = " ".join(content_parts)
        if text_has_nsfw(combined_text):
            await warn_and_delete(update, context, "NSFW terms detected in message content")

    # Add media scan logic if media_scan is enabled
    if settings_dict["media_scan"]:
        # Logic for scanning photos/videos could go here
        # For now, we only have text and profile photo scanning implemented
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    
    user = update.effective_user
    bot = await context.bot.get_me()
    bot_name = bot.first_name or "NSFW Detector"
    
    # Welcome message
    welcome_text = f"""нєу {user.mention_html()}, 🥀

๏ ᴛʜɪs ɪs ❛ {bot_name} ❜ !

➻ ᴀ ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ ʙᴏᴛ ᴡɪᴛʜ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs.

──────────────────
๏ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇs ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs."""
    
    # Inline keyboard with buttons
    keyboard = [
        [InlineKeyboardButton(text="𝗔𝗱𝗱 𝗺𝗲", url=f"https://t.me/{bot.username}?startgroup=new")],
        [InlineKeyboardButton(text="𝗛𝗲𝗹𝗽", callback_data="help_callback"),
         InlineKeyboardButton(text="𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀", callback_data="settings_callback")],
        [InlineKeyboardButton(text="𝗢𝘄𝗻𝗲𝗿 ♛", url="https://t.me/Jayden_212"),
         InlineKeyboardButton(text="𝐔𝐩𝐝𝐚𝐭𝐞𝐬", url="https://t.me/Tele_212_bots")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get bot's profile photo
    try:
        photos = await context.bot.get_user_profile_photos(bot.id, limit=1)
        if photos and photos.total_count > 0:
            # Get the highest quality photo
            file_id = photos.photos[0][-1].file_id
            photo_file = await context.bot.get_file(file_id)
            
            # Download and send as spoiler
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                await photo_file.download_to_drive(custom_path=tmp_path)
                
                # Send photo with spoiler effect and welcome message
                await update.message.reply_photo(
                    photo=open(tmp_path, 'rb'),
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                    has_spoiler=True
                )
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        else:
            # No profile photo, send text only
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error sending start message: {e}")
        # Fallback to text-only message
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    # Check if user is the creator (owner)
    try:
        member = await context.bot.get_chat_member(chat_id=chat.id, user_id=user.id)
        if member.status != 'creator' and chat.type in ['group', 'supergroup']:
            await update.message.reply_text("❌ Only the group owner can manage settings.")
            return
    except Exception:
        # Fallback for private chats (user is owner of their own private chat)
        if chat.type != 'private':
            return

    settings_dict = get_chat_settings(chat.id)
    keyboard = [
        [InlineKeyboardButton(f"{'✅' if settings_dict['pfp_scan'] else '❌'} Profile Photo Scan", callback_data="toggle_pfp_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['image_scan'] else '❌'} Image Scan (NSFW)", callback_data="toggle_image_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['weapon_scan'] else '❌'} Weapon Detection", callback_data="toggle_weapon_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['drug_scan'] else '❌'} Drug Detection", callback_data="toggle_drug_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['text_scan'] else '❌'} Text Content Scan", callback_data="toggle_text_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['media_scan'] else '❌'} Media Scan", callback_data="toggle_media_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['voice_invite_scan'] else '❌'} Voice Invite Scan", callback_data="toggle_voice_invite_scan")],
        [InlineKeyboardButton(text="« BACK »", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙ **NSFW Detector Settings**\n\nToggle any feature below:", reply_markup=reply_markup, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    data = query.data
    
    # Handle Help button
    if data == "help_callback":
        help_text = (
            "𝗛𝗘𝗟𝗣 - 𝗕𝗢𝗧 𝗙𝗘𝗔𝗧𝗨𝗥𝗘𝗦\n\n"
            "๏ 𝗖𝗼𝗻𝘁𝗲𝗻𝘁 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗶𝗼𝗻:\n"
            "├ NSFW Image Detection (AI-powered)\n"
            "├ NSFW Text Filtering\n"
            "├ Drug-related Content Detection\n"
            "└ Profile Photo Scanning\n\n"
            "๏ 𝗩𝗼𝗶𝗰𝗲 𝗖𝗵𝗮𝘁 𝗣𝗿𝗼𝘁𝗲𝗰𝘁𝗶𝗼𝗻:\n"
            "├ Screen voice chat invites\n"
            "├ Detect inappropriate usernames\n"
            "├ Block suspicious users\n"
            "└ Toggle on/off in settings\n\n"
            "๏ 𝗔𝘂𝘁𝗼-𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗶𝗼𝗻:\n"
            "├ Auto-delete violating content\n"
            "├ New member screening\n"
            "└ Warning messages\n\n"
            "๏ 𝗖𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗮𝘁𝗶𝗼𝗻:\n"
            "├ Per-chat settings\n"
            "├ Toggle features on/off\n"
            "└ Owner-only controls\n\n"
            "๏ 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:\n"
            "├ /start - Welcome message\n"
            "├ /settings - Manage bot settings\n"
            "└ Add me to your group!\n\n"
            "𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗯𝘆 @Jayden_212"
        )
        button_back = InlineKeyboardButton(text="« BACK »", callback_data="back_to_start")
        keyboard = [[button_back]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode="HTML")
        return
    
    # Handle Settings from start menu
    if data == "settings_callback":
        # Check if user is the creator (owner)
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status != 'creator' and query.message.chat.type in ['group', 'supergroup']:
                await query.answer("❌ Only the group owner can manage settings.", show_alert=True)
                return
        except Exception:
            if query.message.chat.type != 'private':
                return
        
        settings_dict = get_chat_settings(chat_id)
        keyboard = [
            [InlineKeyboardButton(f"{'✅' if settings_dict['pfp_scan'] else '❌'} Profile Photo Scan", callback_data="toggle_pfp_scan")],
            [InlineKeyboardButton(f"{'✅' if settings_dict['image_scan'] else '❌'} Image Scan (NSFW)", callback_data="toggle_image_scan")],
            [InlineKeyboardButton(f"{'✅' if settings_dict['weapon_scan'] else '❌'} Weapon Detection", callback_data="toggle_weapon_scan")],
            [InlineKeyboardButton(f"{'✅' if settings_dict['drug_scan'] else '❌'} Drug Detection", callback_data="toggle_drug_scan")],
            [InlineKeyboardButton(f"{'✅' if settings_dict['text_scan'] else '❌'} Text Content Scan", callback_data="toggle_text_scan")],
            [InlineKeyboardButton(f"{'✅' if settings_dict['media_scan'] else '❌'} Media Scan", callback_data="toggle_media_scan")],
            [InlineKeyboardButton(f"{'✅' if settings_dict['voice_invite_scan'] else '❌'} Voice Invite Scan", callback_data="toggle_voice_invite_scan")],
            [InlineKeyboardButton(text="« BACK »", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚙ **𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦**\n\nToggle features below:\n\n**Note:** Only group owner can change settings.", reply_markup=reply_markup, parse_mode="Markdown")
        return
    
    # Check if user is the creator (owner) for other callbacks
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status != 'creator' and query.message.chat.type in ['group', 'supergroup']:
            await query.answer("❌ Only the group owner can change settings.", show_alert=True)
            return
    except Exception:
        if query.message.chat.type != 'private':
            return
    
    settings_dict = get_chat_settings(chat_id)
    
    if data == "toggle_pfp_scan":
        settings_dict["pfp_scan"] = not settings_dict["pfp_scan"]
    elif data == "toggle_image_scan":
        settings_dict["image_scan"] = not settings_dict["image_scan"]
    elif data == "toggle_weapon_scan":
        settings_dict["weapon_scan"] = not settings_dict["weapon_scan"]
    elif data == "toggle_drug_scan":
        settings_dict["drug_scan"] = not settings_dict["drug_scan"]
    elif data == "toggle_text_scan":
        settings_dict["text_scan"] = not settings_dict["text_scan"]
    elif data == "toggle_media_scan":
        settings_dict["media_scan"] = not settings_dict["media_scan"]
    elif data == "toggle_voice_invite_scan":
        settings_dict["voice_invite_scan"] = not settings_dict["voice_invite_scan"]
    elif data == "toggle_username_detect":
        settings_dict["username_detect"] = not settings_dict["username_detect"]
    elif data == "toggle_name_detect":
        settings_dict["name_detect"] = not settings_dict["name_detect"]
    elif data == "back_to_start":
        # Go back to start message
        await start_from_callback(update, context)
        return

    keyboard = [
        [InlineKeyboardButton(f"{'✅' if settings_dict['pfp_scan'] else '❌'} Profile Photo Scan", callback_data="toggle_pfp_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['image_scan'] else '❌'} Image Scan (NSFW)", callback_data="toggle_image_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['weapon_scan'] else '❌'} Weapon Detection", callback_data="toggle_weapon_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['drug_scan'] else '❌'} Drug Detection", callback_data="toggle_drug_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['text_scan'] else '❌'} Text Content Scan", callback_data="toggle_text_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['media_scan'] else '❌'} Media Scan", callback_data="toggle_media_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['voice_invite_scan'] else '❌'} Voice Invite Scan", callback_data="toggle_voice_invite_scan")],
        [InlineKeyboardButton(text="« BACK »", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="⚙ **𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦**\n\nToggle features below:\n\n**Note:** Only group owner can change settings.", reply_markup=reply_markup, parse_mode="Markdown")


async def start_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Helper function to regenerate start message from callback"""
    query = update.callback_query
    if not query:
        return
    
    user = query.from_user
    bot = await context.bot.get_me()
    bot_name = bot.first_name or "NSFW Detector"
    
    welcome_text = f"""нєу {user.mention_html()}, 🥀

๏ ᴛʜɪs ɪs ❛ {bot_name} ❜ !

➻ ᴀ ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ ʙᴏᴛ ᴡɪᴛʜ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs.

──────────────────
๏ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇs ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs."""
    
    keyboard = [
        [InlineKeyboardButton("𝗔𝗱𝗱 𝗺𝗲", url=f"https://t.me/{bot.username}?startgroup=new")],
        [InlineKeyboardButton("𝗛𝗲𝗹𝗽", callback_data="help_callback"),
         InlineKeyboardButton("𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀", callback_data="settings_callback")],
        [InlineKeyboardButton("𝗢𝘄𝗻𝗲𝗿 ♛", url="https://t.me/Jayden_212"),
         InlineKeyboardButton("𝐔𝐩𝐝𝐚𝐭𝐞𝐬", url="https://t.me/Tele_212_bots")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error editing message: {e}")


async def detect_nude(image_path: str) -> bool:
    """Detect NSFW/porn content in images using NudeNet"""
    try:
        result = _nude_detector.detect(image_path) or []
        # Check if any category has score > 0.7
        nsfw_detected = any(d.get("score", 0.0) >= 0.7 for d in result)
        return nsfw_detected
    except Exception:
        return False


async def detect_weapon(image_path: str) -> bool:
    """Detect weapons in images using YOLOv5"""
    if not WEAPON_DETECTION_ENABLED or weapon_drug_model is None:
        return False
    
    try:
        results = weapon_drug_model(image_path)
        labels = results.pandas().xyxy[0]["name"].tolist()
        
        for item in labels:
            if item.lower() in WEAPON_OBJECTS:
                return True
        return False
    except Exception:
        return False


async def detect_drugs_image(image_path: str) -> bool:
    """Detect drug objects in images using YOLOv5"""
    if not WEAPON_DETECTION_ENABLED or weapon_drug_model is None:
        return False
    
    try:
        results = weapon_drug_model(image_path)
        labels = results.pandas().xyxy[0]["name"].tolist()
        
        for obj in labels:
            if obj.lower() in DRUG_OBJECTS:
                return True
        return False
    except Exception:
        return False


async def scan_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scan photos for NSFW, weapons, and drugs"""
    msg = update.effective_message
    if not msg:
        return
    
    chat_id = msg.chat.id
    settings_dict = get_chat_settings(chat_id)
    
    # Check if image scanning is enabled
    if not settings_dict["image_scan"]:
        return
    
    # Get the highest quality photo
    photo = msg.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    # Download to temporary file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await file.download_to_drive(custom_path=tmp_path)
        
        # Scan for nudity
        if settings_dict.get("pfp_scan", True) and await detect_nude(tmp_path):
            try:
                await msg.delete()
            except Exception:
                pass
            await send_temp(context, chat_id, f"⚠️ Moderation: User ID `{msg.from_user.id}` - NSFW image detected. Message deleted.", 10)
            return
        
        # Scan for weapons
        if settings_dict.get("weapon_scan", True) and await detect_weapon(tmp_path):
            try:
                await msg.delete()
            except Exception:
                pass
            await send_temp(context, chat_id, f"⚠️ Moderation: User ID `{msg.from_user.id}` - Weapon detected. Message deleted.", 10)
            return
        
        # Scan for drugs
        if settings_dict.get("drug_scan", True) and await detect_drugs_image(tmp_path):
            try:
                await msg.delete()
            except Exception:
                pass
            await send_temp(context, chat_id, f"⚠️ Moderation: User ID `{msg.from_user.id}` - Drug-related content detected. Message deleted.", 10)
            return
            
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


if __name__ == "__main__":
    # Load environment variables from .env file
    load_env_from_file()
    
    # Get bot token from environment
    BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not found. Please configure your .env file!")
        exit(1)
    
    print(f"✅ Starting bot with token: {BOT_TOKEN[:20]}...")
    
    # Build application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_members))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_PARTICIPANTS_INVITED, handle_voice_invite))
    app.add_handler(MessageHandler(filters.PHOTO, scan_photo))
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL & ~filters.PHOTO, handle_any_message))
    
    print("✅ Bot is starting...")
    app.run_polling()
