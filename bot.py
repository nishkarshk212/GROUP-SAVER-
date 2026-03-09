import os
import re
import asyncio
import tempfile
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
            "pfp_scan": True,
            "text_scan": True,
            "media_scan": True,
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


def text_has_nsfw(text: str) -> bool:
    if not text:
        return False
    return bool(nsfw_re.search(text))


def profile_has_drug(user: User) -> bool:
    parts = []
    if user.first_name:
        parts.append(user.first_name)
    if user.last_name:
        parts.append(user.last_name)
    parts.append(user.username or "")
    combined = " ".join(parts)
    return bool(drug_re.search(combined))

def profile_has_nsfw(user: User) -> bool:
    parts = []
    if user.first_name:
        parts.append(user.first_name)
    if user.last_name:
        parts.append(user.last_name)
    parts.append(user.username or "")
    combined = " ".join(parts)
    return bool(nsfw_re.search(combined))


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


async def warn_and_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str) -> None:
    msg = update.effective_message
    if not msg:
        return
    user_id = None
    try:
        if msg.from_user:
            user_id = msg.from_user.id
    except Exception:
        user_id = None
    try:
        await msg.delete()
    except Exception:
        pass
    try:
        chat_id = msg.chat.id
        if user_id is not None:
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
        if await user_profile_is_nsfw(user.id, context):
            await warn_and_delete(update, context, "NSFW profile photo detected")
            return
        if profile_has_drug(user) or profile_has_nsfw(user):
            await warn_and_delete(update, context, "User has restricted terms in name/username")
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
    if not settings_dict["pfp_scan"]:
        return

    vcpi = msg.video_chat_participants_invited
    users = getattr(vcpi, "users", []) if vcpi else []
    for user in users:
        if not user or user.is_bot:
            continue
        if await user_profile_is_nsfw(user.id, context):
            await warn_and_delete(update, context, "Invited user has NSFW profile photo")
            return
        if profile_has_drug(user) or profile_has_nsfw(user):
            await warn_and_delete(update, context, "Invited user has restricted terms in name/username")
            return


async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if not msg:
        return
    
    chat_id = msg.chat.id
    settings_dict = get_chat_settings(chat_id)
    
    # Check profile
    if settings_dict["pfp_scan"] and msg.from_user and not msg.from_user.is_bot:
        if await user_profile_is_nsfw(msg.from_user.id, context):
            await warn_and_delete(update, context, "NSFW profile photo detected")
            return
            
    if not settings_dict["text_scan"] and not settings_dict["media_scan"]:
        return

    if profile_has_drug(msg.from_user) or profile_has_nsfw(msg.from_user):
        await warn_and_delete(update, context, "User has restricted terms in name/username")
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
๏ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴩ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇs ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs."""
    
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
            await update.message.reply_text(welcome_text, parse_mode="HTML")
    except Exception as e:
        print(f"Error sending start message: {e}")
        # Fallback to text-only message
        await update.message.reply_text(welcome_text, parse_mode="HTML")


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
        [InlineKeyboardButton(f"{'✅' if settings_dict['text_scan'] else '❌'} Text Content Scan", callback_data="toggle_text_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['media_scan'] else '❌'} Media Scan", callback_data="toggle_media_scan")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙ **NSFW Detector Settings**\nToggle settings below:", reply_markup=reply_markup, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    
    # Check if user is the creator (owner)
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status != 'creator' and query.message.chat.type in ['group', 'supergroup']:
            await query.answer("❌ Only the group owner can change settings.", show_alert=True)
            return
    except Exception:
        if query.message.chat.type != 'private':
            return

    settings_dict = get_chat_settings(chat_id)
    data = query.data
    
    if data == "toggle_pfp_scan":
        settings_dict["pfp_scan"] = not settings_dict["pfp_scan"]
    elif data == "toggle_text_scan":
        settings_dict["text_scan"] = not settings_dict["text_scan"]
    elif data == "toggle_media_scan":
        settings_dict["media_scan"] = not settings_dict["media_scan"]

    keyboard = [
        [InlineKeyboardButton(f"{'✅' if settings_dict['pfp_scan'] else '❌'} Profile Photo Scan", callback_data="toggle_pfp_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['text_scan'] else '❌'} Text Content Scan", callback_data="toggle_text_scan")],
        [InlineKeyboardButton(f"{'✅' if settings_dict['media_scan'] else '❌'} Media Scan", callback_data="toggle_media_scan")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="⚙ **NSFW Detector Settings**\nToggle settings below:", reply_markup=reply_markup, parse_mode="Markdown")


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
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL, handle_any_message))
    
    print("✅ Bot is starting...")
    app.run_polling()
