# 🎯 Unified Settings & One-Time Sticker Check

## ✅ What's Been Implemented

### 1. **All Settings in One Command** (`/settings`)

A single, beautiful inline keyboard with ALL bot settings:

#### Features Accessible via `/settings`:

**📊 Scanning Options:**
- ✅ Photos (toggle on/off)
- ✅ Videos (toggle on/off)
- ✅ GIFs/Animations (toggle on/off)
- ✅ Stickers (toggle on/off)
- ✅ Text Profanity (toggle on/off)

**⚡ Actions:**
- ✅ Auto-Delete NSFW (toggle on/off)
- ✅ Warn Users (toggle on/off)
- ✅ Log to Channel (toggle on/off)

**🎯 Advanced Settings:**
- **NSFW Threshold**: Select from 0.5, 0.6, 0.7, 0.8, 0.9
- **Frame Sampling**: Every 2nd, 3rd, 4th, 5th, or 10th frame

**🔄 Quick Actions:**
- Enable All Features
- Disable All Features

---

### 2. **One-Time Sticker Detection Check** ✨

Each unique sticker is checked **only once** and cached for 7 days!

#### How It Works:

```
User sends sticker
    ↓
Generate SHA256 hash (file_id + content)
    ↓
Check Redis cache
    ├─→ Found? Return cached result (instant!) ⚡
    └─→ Not found? Run detection → Cache result → Return
    ↓
Next time same sticker is sent → Instant response!
```

#### Benefits:

✅ **Same sticker = One-time check**  
✅ **Cached for 7 days** across all chats  
✅ **Instant response** for known stickers  
✅ **Reduces server load** significantly  

---

### 3. **Sticker Pack Analyzer** 🔍

Analyzes entire Telegram sticker packs for testing:

```python
# Analyze pack URL
https://t.me/addstickers/Shiva1234422_by_fStikBot
```

**What it checks:**
- Total stickers in pack
- Each sticker's file size
- Format (static/animated/video)
- Download and test NSFW detection
- Generate detailed report

---

## 📁 Files Created

1. **`unified_settings.py`** - Complete settings management
2. **`sticker_cache.py`** - One-time detection with Redis caching
3. **`sticker_pack_analyzer.py`** - Sticker pack analysis tool

---

## 🎮 Usage Examples

### Open Settings Menu:
```
/send /settings

Shows interactive menu with buttons:
[✅ Photos] [❌ Videos]
[❌ GIFs] [❌ Stickers]
[✅ Auto-Delete] [✅ Warn User]
[🎯 Threshold: 0.70] [📊 Sample: Every 3 frames]
[🔄 Enable All] [⏹️ Disable All]
[❌ Close]
```

### Toggle Any Setting:
```
Click any button → Instantly toggles on/off
Menu refreshes with updated status
```

### Change Threshold:
```
Click "🎯 Threshold: 0.70"
Select: 0.5 (Strict) | 0.6 | 0.7 (Balanced) | 0.8 | 0.9 (Lenient)
```

### Change Frame Sampling:
```
Click "📊 Sample: Every 3 frames"
Select: Every 2nd (Best) | 3rd (Fast) | 4th | 5th | 10th (Fastest)
```

---

## 🧪 Testing the Shiva Sticker Pack

### Method 1: Use Analyzer Script

On your local machine:
```bash
cd /Users/nishkarshkr/Desktop/bot-app/pyrogram_bot
source .venv/bin/activate

# Run pack analyzer
python sticker_pack_analyzer.py
```

This will:
1. Connect to Telegram
2. Fetch the Shiva1234422_by_fStikBot pack
3. List all stickers with details
4. Analyze first 10 stickers for NSFW content
5. Generate report

### Method 2: Test Live in Bot

1. **Enable sticker scanning:**
   ```
   /settings → Click "🏷️ Stickers" until ✅
   ```

2. **Send stickers from that pack:**
   - First time: Runs full detection (~3-5 seconds)
   - Second time: Instant response from cache! ⚡

3. **Monitor logs:**
   ```bash
   ssh root@140.245.240.202 -p 22
   journalctl -u pyrogram-nsfw-bot -f
   ```
   
   You'll see:
   ```
   🔍 Running fresh NSFW detection...
   💾 Cached result: NSFW=FALSE, Score=0.12 (7 days)
   
   Next time:
   ✅ Cache hit for sticker: NSFW=FALSE, Score=0.12
   ```

---

## 📊 Cache Performance

### Expected Behavior:

**First Time Sending Sticker:**
```
🔍 Running fresh NSFW detection...
📊 Processing sticker: /tmp/abc123.webp
✅ Animated frame analysis (8 frames) in 3.2s
💾 Cached result: NSFW=FALSE, Score=0.12 (7 days)
```

**Second Time (Same Sticker):**
```
✅ Cache hit for sticker: NSFW=FALSE, Score=0.12
Response time: <0.1s ⚡
```

### Cache Statistics:

Check cache status anytime:
```python
from sticker_cache import sticker_cache

stats = sticker_cache.get_cache_stats()
print(f"Cached stickers: {stats['total_cached']}")
print(f"Cache duration: {stats['cache_ttl_days']} days")
```

---

## 🚀 Deploy to Server

### Step 1: Upload New Files

```bash
cd /Users/nishkarshkr/Desktop/bot-app

# Upload to server
scp -P 22 pyrogram_bot/unified_settings.py root@140.245.240.202:/opt/nsfw-bot/pyrogram_bot/
scp -P 22 pyrogram_bot/sticker_cache.py root@140.245.240.202:/opt/nsfw-bot/pyrogram_bot/
scp -P 22 pyrogram_bot/sticker_pack_analyzer.py root@140.245.240.202:/opt/nsfw-bot/pyrogram_bot/

# Commit and push
git add pyrogram_bot/*.py
git commit -m "Add unified settings and one-time sticker check"
git push origin main
```

### Step 2: Update Server

```bash
ssh root@140.245.240.202 -p 22

cd /opt/nsfw-bot
git pull origin main

# Restart bot to load new modules
systemctl restart pyrogram-nsfw-bot

# Check status
systemctl status pyrogram-nsfw-bot --no-pager -n 10
```

---

## 🎯 Integration with Main Bot

To integrate these features into `bot_optimized.py`, add these handlers:

### Add to bot_optimized.py:

```python
from unified_settings import (
    get_chat_settings,
    create_settings_keyboard,
    get_settings_text,
    handle_toggle,
    handle_enable_all,
    handle_disable_all,
    handle_threshold_change,
    handle_sample_change
)
from sticker_cache import check_sticker_once, sticker_cache

# Settings command handler
@app.on_message(filters.command("settings"))
async def settings_command(client: Client, message: Message):
    """Unified settings menu"""
    chat_id = message.chat.id
    
    text = get_settings_text(chat_id)
    keyboard = create_settings_keyboard(chat_id)
    
    await message.reply(text, reply_markup=keyboard, parse_mode="markdown")

# Callback query handler for all buttons
@app.on_callback_query(filters.regex(r"^(toggle_|enable_|disable_|threshold_|sample_|back_|close_)"))
async def settings_callback(client: Client, callback_query: CallbackQuery):
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
    
    elif data == "set_sample":
        await handle_sample_change(callback_query)
    
    elif data == "back_to_settings":
        # Return to main settings menu
        chat_id = callback_query.message.chat.id
        text = get_settings_text(chat_id)
        keyboard = create_settings_keyboard(chat_id)
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="markdown")
    
    elif data == "close_settings":
        await callback_query.message.delete()

# Updated sticker handler with caching
@app.on_message(filters.sticker)
async def sticker_handler_cached(client: Client, message: Message):
    """Sticker handler with one-time check"""
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)
    
    if not settings.get('sticker_scan', False):
        return
    
    sticker = message.sticker
    file_id = sticker.file_id
    
    # Download sticker
    with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        await message.download(file_name=tmp_path)
        
        # Use one-time check with caching
        is_nsfw, score, method = await check_sticker_once(
            file_id,
            tmp_path,
            None  # detector_func (not needed, uses default)
        )
        
        # Handle result
        if is_nsfw and method != "cached_result":
            # Only warn on fresh detections
            result = {
                'is_nsfw': is_nsfw,
                'score': score,
                'method': method,
                'frames_analyzed': 1
            }
            await handle_nsfw_detection(message, result)
        
        # Cleanup
        try:
            os.remove(tmp_path)
        except:
            pass
            
    except Exception as e:
        print(f"Error in cached sticker handler: {e}")
```

---

## 📈 Expected Results

### Settings Menu Example:

When user sends `/settings`:

```
⚙️ NSFW Moderation Settings

📊 Current Configuration

Chat ID: `-1001234567890`
NSFW Threshold: 0.70
Frame Sampling: Every 3 frames

🔍 Scanning Options:
  ✅ Photos
  ❌ Videos
  ❌ GIFs/Animations
  ❌ Stickers
  ✅ Text Profanity

⚡ Actions:
  ✅ Auto-Delete NSFW
  ✅ Warn Users
  ❌ Log to Channel

[✅ Photos] [❌ Videos]
[❌ GIFs] [❌ Stickers]
[✅ Auto-Delete] [✅ Warn User]
[✅ Text Scan] [❌ Log Channel]
[🎯 Threshold: 0.70] [📊 Sample: Every 3 frames]
[🔄 Enable All] [⏹️ Disable All]
[❌ Close]
```

### Sticker Cache in Action:

**User sends Shiva pack sticker #1:**
```
Bot: 🔍 Analyzing sticker...
     (3 seconds later)
Bot: ✅ Safe sticker (Score: 0.12)
     💾 Result cached for 7 days
```

**Same user (or different user) sends same sticker:**
```
Bot: ✅ Safe sticker (Score: 0.12)
     ⚡ Response time: <0.1s (from cache)
```

---

## 🎉 Summary

### What You Get:

✅ **One Command** - `/settings` controls everything  
✅ **Interactive Buttons** - Toggle any feature instantly  
✅ **One-Time Check** - Each sticker scanned only once  
✅ **7-Day Cache** - Persistent across all chats  
✅ **Instant Response** - For known stickers  
✅ **Pack Analysis** - Test entire sticker packs  
✅ **Configurable** - Threshold, sampling, all adjustable  

### Files Ready to Deploy:

- `unified_settings.py` - Settings management
- `sticker_cache.py` - One-time detection
- `sticker_pack_analyzer.py` - Pack testing tool

**All set for unified settings and intelligent sticker caching!** 🚀
