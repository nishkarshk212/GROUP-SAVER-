import os
import re
import asyncio
import tempfile
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from typing import Dict, Set
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

"""
NSFW Detection Bot
Features:
- Detects NSFW content in messages, usernames, and profile photos
- Automatically deletes inappropriate content
- Logs bot join/leave events to a configured log channel
"""
try:
    from google.cloud import translate_v2 as translate
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False
    print("Google Cloud Translate not available. Install with: pip install google-cloud-translate")
from nudenet import NudeDetector
try:
    from nudenet import NudeClassifier
except Exception:
    NudeClassifier = None

_bad_word_re = None
_bad_phrases = []
_bad_loaded = False
_bad_langs = None
_bad_local_dir = os.path.join(os.path.dirname(__file__), "data", "naughty-words")
_bad_supported_langs = [
    "ar","zh","cs","da","nl","en","eo","fil","fi","fr","fr-CA","de",
    "hi","hu","it","ja","kab","tlh","ko","no","fa","pl","pt","ru",
    "es","sv","th","tr"
]
_profanity_model_loaded = False
_toxic_pipeline = None

def _load_bad_words() -> None:
    global _bad_word_re, _bad_phrases, _bad_loaded, _bad_langs
    if _bad_loaded:
        return
    langs_env = os.environ.get("NSFW_WORD_LANGS", "en,ru").strip()
    if langs_env.lower() == "all":
        langs = list(_bad_supported_langs)
    else:
        langs = langs_env.split(",")
    langs = [l.strip() for l in langs if l.strip()]
    if not langs:
        langs = ["en", "ru"]
    _bad_langs = langs
    words = set()
    phrases = set()
    try:
        os.makedirs(_bad_local_dir, exist_ok=True)
    except Exception:
        pass
    for lang in langs:
        local_path = os.path.join(_bad_local_dir, f"{lang}.json")
        data = None
        try:
            if os.path.isfile(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except Exception:
            data = None
        if data is None:
            url = f"https://cdn.jsdelivr.net/npm/naughty-words/{lang}.json"
            try:
                with urlopen(url, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                try:
                    with open(local_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=0)
                except Exception:
                    pass
            except (URLError, HTTPError, TimeoutError, ValueError):
                data = None
            except Exception:
                data = None
        if not data:
            continue
        for item in data:
            s = str(item).strip().lower()
            if not s:
                continue
            if " " in s or "-" in s or "'" in s:
                phrases.add(s)
            else:
                words.add(s)
    if words:
        escaped = [re.escape(w) for w in sorted(words, key=len, reverse=True)]
        pattern = r"(?i)\b(?:" + "|".join(escaped) + r")\b"
        try:
            _bad_word_re = re.compile(pattern)
        except Exception:
            _bad_word_re = None
    _bad_phrases = sorted(phrases, key=len, reverse=True)
    _bad_loaded = True
drug_re = re.compile(
    r"(?i)\b(?:drug|weed|marijuana|cannabis|cocaine|crack|heroin|mdma|molly|ecstasy|ketamine|xanax|adderall|oxy|oxycodone|opioid|meth|crystal|ice|lsd|acid|shrooms|psilocybin|dmt|fentanyl|tramadol|ritalin|benzos|benzo|pill|pharmacy)\b"
)

# Child exploitation and sexual violence content detection
child_exploitation_patterns = [
    r"детск.*порнограф",
    r"торговл.*дет",
    r"продаж.*дет",
    r"изнасил.*ребен",
    r"насил.*дет",
    r"жесток.*дет",
    r"дет.*насил",
    r"секс.*дет",
    r"sex.*child",
    r"child.*sex",
    r"child.*porn",
    r"child.*exploit",
    r"child.*traffick",
    r"child.*abuse",
    r"child.*rape",
    r"pedo.*phil",
    r"child.*prostitut",
    r"sex.*slave",
    r"sex.*traffick",
    r"human.*traffick",
    r"violence.*child",
    r"abuse.*child",
    r"abusive.*content",
    r"non.*consensual",
    r"underage.*content",
    r"minor.*content",
    r"underage.*sex",
    r"minor.*sex",
    r"underage.*nudity",
    r"minor.*nudity",
]

child_exploitation_re = re.compile('|'.join(child_exploitation_patterns), re.IGNORECASE)

# Global variable for translation client
translate_client = None

alerted_users_per_chat: Dict[int, Set[int]] = {}
_pfp_scan_cache: Dict[int, bool] = {}
# Track chats where bot is active
active_chats: Set[int] = set()
# Log channel for bot join/leave notifications - should be set via environment variable
# To use: set LOG_CHANNEL_ID environment variable to either:
# 1. Channel username like "@your_channel_username" 
# 2. Numeric chat ID like "-1001234567890" (negative for channels/groups)
LOG_CHANNEL_ID = None
_nude_detector = NudeDetector()
_nude_classifier = None


async def send_log_message(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send a log message to the designated log channel."""
    log_channel = os.environ.get("LOG_CHANNEL_ID")
    if not log_channel:
        return  # No log channel configured
        
    # Handle different channel ID formats
    # If it's an invite link like "+xxxxx", we can't use it directly
    # User needs to provide either @username or numeric ID
    if log_channel.startswith('https://t.me/') or log_channel.startswith('+'):
        print("Log channel ID format invalid. Use @channel_username or numeric ID like -1001234567890")
        return
        
    try:
        # Try direct send first (handles @usernames and numeric IDs)
        await context.bot.send_message(chat_id=log_channel, text=message)
    except Exception as e:
        print(f"Failed to send log message: {e}")
        # Try to convert string channel ID if it was passed as a string representation of a number
        try:
            if log_channel.lstrip('-').isdigit():
                log_channel_numeric = int(log_channel)
                await context.bot.send_message(chat_id=log_channel_numeric, text=message)
        except Exception as e2:
            print(f"Failed to send log message with numeric conversion: {e2}")


def get_translate_client():
    global translate_client
    if translate_client is None and TRANSLATE_AVAILABLE:
        try:
            translate_client = translate.Client()
        except Exception as e:
            print(f"Could not initialize Google Translate client: {e}")
            return None
    return translate_client


def translate_text(text: str) -> str:
    if not TRANSLATE_AVAILABLE:
        return text  # Return original text if translation is not available
    
    client = get_translate_client()
    if client is None:
        return text  # Return original text if client couldn't be initialized
    
    try:
        # Detect language and translate to English
        result = client.translate(text, target_language="en")
        return result.get("translatedText", text)
    except Exception as e:
        print(f"Translation failed: {e}")
        return text  # Return original text if translation fails

def _ml_profanity(text: str) -> bool:
    use_pc = os.environ.get("USE_PROFANITY_CHECK", "1").strip() != "0"
    use_toxic = os.environ.get("USE_TOXIC_BERT", "1").strip() != "0"
    if not (use_pc or use_toxic):
        return False
    found = False
    global _profanity_model_loaded
    if use_pc:
        try:
            if not _profanity_model_loaded:
                from profanity_check import predict
                _profanity_model_loaded = True
            else:
                from profanity_check import predict
            v = predict([text])[0]
            if int(v) == 1:
                found = True
        except Exception:
            pass
    if found:
        return True
    global _toxic_pipeline
    if use_toxic:
        try:
            if _toxic_pipeline is None:
                from transformers import pipeline
                _toxic_pipeline = pipeline("text-classification", model="unitary/toxic-bert", device=-1)
            res = _toxic_pipeline(text, truncation=True)
            thr = float(os.environ.get("TOXIC_BERT_THRESHOLD", "0.5"))
            if isinstance(res, list) and res:
                r = res[0]
                label = str(r.get("label", "")).lower()
                score = float(r.get("score", 0.0))
                if label == "toxic" and score >= thr:
                    found = True
        except Exception:
            pass
    return found


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
    if not _bad_loaded:
        _load_bad_words()
    
    # Check original text
    t = text.lower()
    if _bad_word_re and _bad_word_re.search(t):
        return True
    for p in _bad_phrases:
        if p in t:
            return True
    
    # Also check translated text for non-English content
    translated_text = translate_text(text)
    if translated_text and translated_text != text:
        t_translated = translated_text.lower()
        if _bad_word_re and _bad_word_re.search(t_translated):
            return True
        for p in _bad_phrases:
            if p in t_translated:
                return True
    
    if _ml_profanity(text):
        return True
    # Check for child exploitation and sexual violence content
    if child_exploitation_re.search(text):
        return True
    if child_exploitation_re.search(translated_text):
        return True
    return False


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
    return text_has_nsfw(combined)


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
    try:
        chat = msg.chat
        chat_id = chat.id
        offender = msg.from_user
        if offender:
            s = alerted_users_per_chat.get(chat_id)
            if s is None:
                s = set()
                alerted_users_per_chat[chat_id] = s
            if offender.id in s:
                return
        admins = await context.bot.get_chat_administrators(chat_id)
        owner_user = None
        for a in admins or []:
            try:
                if getattr(a, "status", "") == "creator":
                    owner_user = a.user
                    break
            except Exception:
                continue
        if not owner_user and admins:
            try:
                owner_user = admins[0].user
            except Exception:
                owner_user = None
        if owner_user:
            parts = []
            parts.append(f"Group: {getattr(chat, 'title', '') or 'N/A'} (id={chat_id})")
            if offender:
                uname = f"@{offender.username}" if offender.username else "N/A"
                fullname = " ".join([p for p in [offender.first_name, offender.last_name] if p]) or "N/A"
                parts.append(f"Offender: id={offender.id}, username={uname}, name={fullname}")
            parts.append(f"Action: Message deleted")
            parts.append(f"Reason: {reason}")
            snippet = None
            try:
                texts = []
                if msg.text:
                    texts.append(msg.text)
                if msg.caption:
                    texts.append(msg.caption)
                snippet = " ".join(texts).strip()
            except Exception:
                snippet = None
            if snippet:
                if len(snippet) > 300:
                    snippet = snippet[:297] + "..."
                parts.append(f"Snippet: {snippet}")
            text = "\n".join(parts)
            try:
                await context.bot.send_message(chat_id=owner_user.id, text=text)
                if offender:
                    alerted_users_per_chat[chat_id].add(offender.id)
            except Exception:
                pass
    except Exception:
        pass


async def user_profile_is_nsfw(user_id: int, context: ContextTypes.DEFAULT_TYPE, threshold: float = 0.7) -> bool:
    try:
        enabled = os.environ.get("PFP_NSFWD_ENABLED", os.environ.get("ENABLE_PFP_NSFWD", "1")).strip()
        if enabled in ("0", "false", "False", "no", "No"):
            return False
    except Exception:
        pass
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
            nsfw_detected = False
            try:
                thr_cls = float(os.environ.get("NSFW_PFP_CLS_THRESHOLD", "0.85"))
            except Exception:
                thr_cls = 0.85
            try:
                thr_det = float(os.environ.get("NSFW_PFP_THRESHOLD", str(threshold)))
            except Exception:
                thr_det = threshold
            if NudeClassifier is not None:
                global _nude_classifier
                if _nude_classifier is None:
                    _nude_classifier = NudeClassifier()
                try:
                    cls_res = _nude_classifier.classify(tmp_path)
                    pred = None
                    conf = 0.0
                    if isinstance(cls_res, dict):
                        v = cls_res.get(tmp_path)
                        if v is None and cls_res:
                            v = next(iter(cls_res.values()))
                        if isinstance(v, dict):
                            if "unsafe" in v and isinstance(v["unsafe"], (int, float)):
                                conf = float(v.get("unsafe", 0.0))
                                pred = "unsafe"
                            elif "NSFW" in v and isinstance(v["NSFW"], (int, float)):
                                conf = float(v.get("NSFW", 0.0))
                                pred = "nsfw"
                            elif "confidence" in v and "prediction" in v:
                                conf = float(v.get("confidence", 0.0))
                                pred = str(v.get("prediction", "")).lower()
                    elif isinstance(cls_res, list) and cls_res:
                        v = cls_res[0]
                        if isinstance(v, dict):
                            conf = float(v.get("confidence", 0.0))
                            pred = str(v.get("prediction", "")).lower()
                    if pred in ("unsafe", "nsfw") and conf >= thr_cls:
                        nsfw_detected = True
                except Exception:
                    pass
            if not nsfw_detected:
                det_res = _nude_detector.detect(tmp_path) or []
                for d in det_res:
                    try:
                        sc = float(d.get("score", 0.0))
                    except Exception:
                        sc = 0.0
                    if sc >= thr_det:
                        nsfw_detected = True
                        break
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
    
    # Check if the bot itself joined the chat
    bot = await context.bot.get_me()
    for user in msg.new_chat_members or []:
        if user and user.id == bot.id:
            # Bot joined a new chat - log this event
            chat = update.effective_chat
            if chat:
                chat_title = getattr(chat, 'title', 'Unknown')
                chat_id = chat.id
                chat_type = getattr(chat, 'type', 'Unknown')
                log_msg = f"🤖 Bot joined chat:\n- Title: {chat_title}\n- ID: {chat_id}\n- Type: {chat_type}"
                await send_log_message(context, log_msg)
            break  # Only need to check once
    
    # Track active chat
    chat = update.effective_chat
    if chat:
        active_chats.add(chat.id)
    
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
    
    # Check if the bot itself left the chat
    bot = await context.bot.get_me()
    user = msg.left_chat_member
    if user and user.id == bot.id:
        # Bot left the chat - log this event
        chat = update.effective_chat
        if chat:
            chat_title = getattr(chat, 'title', 'Unknown')
            chat_id = chat.id
            chat_type = getattr(chat, 'type', 'Unknown')
            log_msg = f"🤖 Bot left chat:\n- Title: {chat_title}\n- ID: {chat_id}\n- Type: {chat_type}"
            await send_log_message(context, log_msg)
    
    # Track active chat
    chat = update.effective_chat
    if chat:
        active_chats.add(chat.id)
    
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
    
    # Track active chat
    chat = update.effective_chat
    if chat:
        active_chats.add(chat.id)
    
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
    
    # Track active chat
    chat = update.effective_chat
    if chat:
        active_chats.add(chat.id)
    
    # Check profile
    if msg.from_user and not msg.from_user.is_bot:
        if await user_profile_is_nsfw(msg.from_user.id, context):
            await warn_and_delete(update, context, "NSFW profile photo detected")
            return
        if profile_has_drug(msg.from_user) or profile_has_nsfw(msg.from_user):
            await warn_and_delete(update, context, "User has restricted terms in name/username")
            return
            
    # Collect all text content
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    
    # Track active chat
    active_chats.add(chat.id)
    
    # Get user's name
    user_name = user.first_name or "User"
    
    # Custom message with bold formatting
    text = f"""𝐇𝐞𝐥𝐥𝐨 {user_name}👋
𝐈 𝐚𝐦 𝐍𝐒𝐅𝐖 𝐃𝐄𝐓𝐄𝐂𝐓𝐎𝐑 𝐁𝐎𝐓 🤖
𝐈 𝐩𝐫𝐨𝐭𝐞𝐜𝐭 𝐲𝐨𝐮𝐫 𝐓𝐞𝐥𝐞𝐠𝐫𝐚𝐦 𝐠𝐫𝐨𝐮𝐩 𝐛𝐲 𝐝𝐞𝐭𝐞𝐜𝐭𝐢𝐧𝐠 𝐢𝐧𝐚𝐩𝐩𝐫𝐨𝐩𝐫𝐢𝐚𝐭𝐞 𝐮𝐬𝐞𝐫𝐧𝐚𝐦𝐞𝐬, 𝐝𝐢𝐬𝐩𝐥𝐚𝐲 𝐧𝐚𝐦𝐞𝐬, 𝐚𝐧𝐝 𝐦𝐞𝐬𝐬𝐚𝐠𝐞𝐬.

🔍 𝐀𝐮𝐭𝐨 𝐍𝐒𝐅𝐖 𝐃𝐞𝐭𝐞𝐜𝐭𝐢𝐨𝐧
🗑️ 𝐈𝐧𝐬𝐭𝐚𝐧𝐭 𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐃𝐞𝐥𝐞𝐭𝐢𝐨𝐧
🛡️ 𝐊𝐞𝐞𝐩𝐬 𝐘𝐨𝐮𝐫 𝐂𝐨𝐦𝐦𝐮𝐧𝐢𝐭𝐲 𝐂𝐥𝐞𝐚𝐧 & 𝐒𝐚𝐟𝐞
📊 𝐋𝐨𝐠𝐬 𝐛𝐨𝐭 𝐣𝐨𝐢𝐧/𝐥𝐞𝐚𝐯𝐞 𝐞𝐯𝐞𝐧𝐭𝐬

👑 𝐌𝐚𝐤𝐞 𝐦𝐞 𝐀𝐝𝐦𝐢𝐧
⚙️ 𝐄𝐧𝐣𝐨𝐲 𝐚𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐜 𝐩𝐫𝐨𝐭𝐞𝐜𝐭𝐢𝐨𝐧"""
    
    me = await context.bot.get_me()
    url = f"https://t.me/{me.username}?startgroup=true" if me.username else "https://t.me"
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("Add to Group", url=url)]])
    
    try:
        photos = await context.bot.get_user_profile_photos(user_id=me.id, limit=1)
        if photos and photos.total_count and photos.photos and photos.photos[0]:
            fid = photos.photos[0][-1].file_id
            await context.bot.send_photo(chat_id=chat.id, photo=fid, caption=text, has_spoiler=True, reply_markup=markup)
            return
    except Exception:
        pass
    await context.bot.send_message(chat_id=chat.id, text=text, reply_markup=markup)


async def cmd_checkpfp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return
    nsfw = await user_profile_is_nsfw(user.id, context)
    await send_temp(context, chat.id, ("⚠️ Your profile photo appears NSFW." if nsfw else "✅ Your profile photo looks safe."), 10)

async def cmd_checkbotpfp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat:
        return
    me = await context.bot.get_me()
    nsfw = await user_profile_is_nsfw(me.id, context)
    await send_temp(context, chat.id, ("⚠️ Bot profile photo appears NSFW." if nsfw else "✅ Bot profile photo looks safe."), 10)

async def cmd_whereami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command for bot owner to check where the bot is running in groups"""
    user = update.effective_user
    if not user:
        return
    
    # Check if the user is the bot owner (@Jayden_212)
    # Note: You may need to find the actual user ID for the bot owner
    # For now, we'll check username only, but for production you should use user ID
    if user.username != "Jayden_212":
        await send_temp(context, update.effective_chat.id, "❌ This command is only available to the bot owner.", 10)
        return
    
    try:
        # Get the bot's info
        me = await context.bot.get_me()
        
        # Get information about where the bot is active
        chat = update.effective_chat
        if chat:
            # Build bot info message
            bot_info = f"🤖 NSFW Detection Bot Status Report\n\n"
            bot_info += f"Bot Name: {me.first_name}\n"
            bot_info += f"Bot Username: @{me.username}\n\n"
            
            # Current chat info
            bot_info += f"📍 Current Chat:\n"
            bot_info += f"  Type: {chat.type}\n"
            bot_info += f"  ID: {chat.id}\n"
            if hasattr(chat, 'title') and chat.title:
                bot_info += f"  Title: {chat.title}\n\n"
            else:
                bot_info += "\n"
            
            # Active chats info (based on tracked activity)
            if active_chats:
                bot_info += f"📊 Active Chats ({len(active_chats)}):\n"
                for i, chat_id in enumerate(list(active_chats)[:10]):  # Limit to first 10 for readability
                    try:
                        chat_obj = await context.bot.get_chat(chat_id)
                        chat_title = getattr(chat_obj, 'title', getattr(chat_obj, 'first_name', 'Unknown'))
                        chat_type = getattr(chat_obj, 'type', 'unknown')
                        bot_info += f"  {i+1}. {chat_type}: {chat_title} (ID: {chat_id})\n"
                    except Exception:
                        bot_info += f"  {i+1}. Unknown chat (ID: {chat_id})\n"
                
                if len(active_chats) > 10:
                    bot_info += f"  ... and {len(active_chats) - 10} more chats\n\n"
            else:
                bot_info += "📊 No active chats recorded yet.\n\n"
            
            bot_info += f"💡 Tip: Bot actively monitors for NSFW content in all joined groups."
            
            await context.bot.send_message(chat_id=chat.id, text=bot_info)
    except Exception as e:
        await send_temp(context, update.effective_chat.id, f"Error getting bot info: {str(e)}", 10)


def main() -> None:
    load_env_from_file()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN environment variable.")
    app = ApplicationBuilder().token(token).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("checkpfp", cmd_checkpfp))
    app.add_handler(CommandHandler("checkbotpfp", cmd_checkbotpfp))
    app.add_handler(CommandHandler("whereami", cmd_whereami))
    
    # Service messages
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_members))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_PARTICIPANTS_INVITED, handle_voice_invite))
    
    # Catch-all for ANY other message (text, media, polls, documents, etc.)
    # We use group=1 or just standard handler but filters.ALL (excluding service updates handled above)
    # Actually filters.ALL includes everything. We can just put this last.
    # But wait, if we want to catch commands too, we should be careful.
    # CommandHandler handles commands and stops propagation if we don't use group.
    # But we want to check NSFW in commands too?
    # If so, we should add a TypeHandler(Update, global_check) or similar.
    # But sticking to MessageHandler(filters.ALL, ...) works if placed after specific commands
    # OR we can just use it for everything.
    
    # Let's use a broad filter that excludes status updates we already handled?
    # Actually, simpler: just use filters.ALL and let it run.
    # But if we use filters.ALL, it will catch commands too if they are not stopped.
    # CommandHandler stops propagation by default.
    # So valid commands /start and /me will run.
    # Invalid commands or other text will fall through? No, CommandHandler only matches specific commands.
    # We want to catch EVERYTHING else.
    
    app.add_handler(MessageHandler(filters.ALL & (~filters.StatusUpdate.ALL), handle_any_message))

    app.run_polling()


if __name__ == "__main__":
    main()
