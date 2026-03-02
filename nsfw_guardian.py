import re
import sqlite3
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from better_profanity import profanity
from detoxify import Detoxify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

API_ID = 123456
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"

bot = Client("nsfw_guardian", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Load AI models
model = Detoxify('original')
# Load the roberta-large Image Prompt Classifier
model_repo = "MichalMlodawski/nsfw-text-detection-large"
tokenizer = AutoTokenizer.from_pretrained(model_repo)
roberta_model = AutoModelForSequenceClassification.from_pretrained(model_repo)

# Database
conn = sqlite3.connect("nsfw.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS warnings(
    user_id INTEGER,
    chat_id INTEGER,
    count INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings(
    chat_id INTEGER PRIMARY KEY,
    warn_limit INTEGER DEFAULT 3,
    action TEXT DEFAULT 'mute'
)
""")

conn.commit()

# --------- TEXT NORMALIZER ----------
def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = text.replace("3", "e").replace("1", "i").replace("0", "o")
    text = re.sub(r'\s+', '', text)
    return text

# --------- REGEX PATTERNS ----------
nsfw_patterns = [
    r"s[e3]x+",
    r"f+u+c+k+",
    r"b+i+t+c+h+",
    r"n+u+d+e+",
]

# --------- WARNING SYSTEM ----------
def add_warning(user_id, chat_id):
    cursor.execute("SELECT count FROM warnings WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    row = cursor.fetchone()

    if row:
        new_count = row[0] + 1
        cursor.execute("UPDATE warnings SET count=? WHERE user_id=? AND chat_id=?", 
                       (new_count, user_id, chat_id))
    else:
        new_count = 1
        cursor.execute("INSERT INTO warnings(user_id, chat_id, count) VALUES(?,?,?)", 
                       (user_id, chat_id, new_count))
    conn.commit()
    return new_count

def get_settings(chat_id):
    cursor.execute("SELECT warn_limit, action FROM settings WHERE chat_id=?", (chat_id,))
    row = cursor.fetchone()
    if row:
        return row
    else:
        cursor.execute("INSERT INTO settings(chat_id) VALUES(?)", (chat_id,))
        conn.commit()
        return (3, "mute")

# --------- NSFW CHECK ----------
def is_nsfw(text):
    if not text:
        return False
        
    clean = normalize(text)

    # 1 Keyword filter
    if profanity.contains_profanity(clean):
        return True

    # 2 Regex check
    for pattern in nsfw_patterns:
        if re.search(pattern, clean):
            return True

    # 3 AI toxicity
    try:
        result = model.predict(text)
        if result["toxicity"] > 0.80 or result["sexual_explicit"] > 0.70:
            return True
    except:
        # If AI model fails, fall back to other checks
        pass

    # 4 Roberta-large Image Prompt Classifier
    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = roberta_model(**inputs)
            logits = outputs.logits
            predicted_class = torch.argmax(logits, dim=1).item()
            # Class 1 is typically NSFW in binary classification
            if predicted_class == 1:
                return True
    except:
        # If Roberta model fails, fall back to other checks
        pass

    return False

def is_username_nsfw(username, first_name, last_name=None):
    """
    Check if user's username, first name, or last name contains NSFW content
    """
    # Check username
    if username and is_nsfw(username):
        return True
    
    # Check first name
    if first_name and is_nsfw(first_name):
        return True
    
    # Check last name if provided
    if last_name and is_nsfw(last_name):
        return True
    
    return False

# --------- MESSAGE HANDLER ----------
@bot.on_message(filters.group & (filters.text | filters.caption))
@bot.on_edited_message(filters.group & (filters.text | filters.caption))
async def nsfw_filter(client, message):
    text = message.text or message.caption
    if not text:
        return

    if is_nsfw(text):
        await message.delete()

        warn_count = add_warning(message.from_user.id, message.chat.id)
        warn_limit, action = get_settings(message.chat.id)

        warning_msg = await message.reply(
            f"⚠️ {message.from_user.mention}, NSFW language detected!\n"
            f"Warning: {warn_count}/{warn_limit}"
        )

        if warn_count >= warn_limit:
            if action == "mute":
                await client.restrict_chat_member(
                    message.chat.id,
                    message.from_user.id,
                    permissions={}
                )
                await message.reply("🔇 User muted due to repeated violations.")
            elif action == "ban":
                await client.ban_chat_member(
                    message.chat.id,
                    message.from_user.id
                )
                await message.reply("🚫 User banned due to repeated violations.")

# --------- NEW MEMBER HANDLER ----------
@bot.on_message(filters.group & filters.new_chat_members)
async def check_new_member(client, message):
    for new_member in message.new_chat_members:
        # Check if new member's name or username is NSFW
        if is_username_nsfw(new_member.username, new_member.first_name, new_member.last_name):
            # Delete the message about the new member joining
            await message.delete()
            
            # Warn the user
            warn_count = add_warning(new_member.id, message.chat.id)
            warn_limit, action = get_settings(message.chat.id)
            
            await message.reply(
                f"⚠️ User {new_member.mention} has NSFW name/username and was restricted!\n"
                f"Warning: {warn_count}/{warn_limit}"
            )
            
            # Apply restriction if limit reached
            if warn_count >= warn_limit:
                if action == "mute":
                    await client.restrict_chat_member(
                        message.chat.id,
                        new_member.id,
                        permissions={}
                    )
                    await message.reply(f"🔇 User {new_member.mention} muted due to NSFW name/username.")
                elif action == "ban":
                    await client.ban_chat_member(
                        message.chat.id,
                        new_member.id
                    )
                    await message.reply(f"🚫 User {new_member.mention} banned due to NSFW name/username.")
            
            # Kick the user with NSFW name/username
            await client.ban_chat_member(message.chat.id, new_member.id)
            await client.unban_chat_member(message.chat.id, new_member.id)  # Unban to just kick

# --------- USERNAME UPDATE HANDLER ----------
@bot.on_message(filters.group & filters.service)
async def check_service_messages(client, message):
    # Check if a member's name changed in the group
    if message.left_chat_member:
        # This is when someone leaves, not name change
        return
    
    # For name changes, we need to monitor user updates differently
    # Pyrogram doesn't have a direct event for name changes, but we can check if
    # a user is modifying their profile by detecting certain service messages
    pass

# --------- SETTINGS PANEL ----------
@bot.on_message(filters.command("settings") & filters.group)
async def settings_panel(client, message):
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ("administrator", "creator"):
        return await message.reply("Only admins can access settings.")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Warn Limit 2", callback_data="limit_2"),
         InlineKeyboardButton("Warn Limit 3", callback_data="limit_3")],
        [InlineKeyboardButton("Action: Mute", callback_data="action_mute"),
         InlineKeyboardButton("Action: Ban", callback_data="action_ban")]
    ])

    await message.reply("⚙️ NSFW Guardian Settings:", reply_markup=keyboard)

@bot.on_callback_query()
async def callback_handler(client, callback_query):
    chat_id = callback_query.message.chat.id

    if "limit_" in callback_query.data:
        limit = int(callback_query.data.split("_")[1])
        cursor.execute("UPDATE settings SET warn_limit=? WHERE chat_id=?", (limit, chat_id))
        conn.commit()
        await callback_query.answer(f"Warn limit set to {limit}")

    if "action_" in callback_query.data:
        action = callback_query.data.split("_")[1]
        cursor.execute("UPDATE settings SET action=? WHERE chat_id=?", (action, chat_id))
        conn.commit()
        await callback_query.answer(f"Action set to {action}")

# --------- START COMMAND ----------
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    welcome_text = """
    🛡️ **NSFW Guardian Bot**
    
    I protect your Telegram groups from inappropriate content!
    
    🔍 I scan all messages for NSFW content
    👤 I check user names and usernames for NSFW content
    ⚠️ I issue warnings to violators
    🚫 I can mute or ban repeat offenders
    
    Add me to your group and make me admin to start protecting!
    """
    await message.reply(welcome_text)

if __name__ == "__main__":
    print("NSFW Guardian Bot is starting...")
    bot.run()