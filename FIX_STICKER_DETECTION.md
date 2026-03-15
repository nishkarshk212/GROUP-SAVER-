# 🛠️ Enhanced Sticker Detection - Fix for Current Bot

## Problem: Sticker scan enabled but not detecting

**Root cause:** Conflict errors preventing message processing

## ✅ Solution: Fix Your Existing Bot

### Step 1: Kill Conflicting Instances (CRITICAL)

```bash
# SSH to server
ssh root@140.245.240.202 -p 22

# Stop service
sudo systemctl stop nsfw-bot

# Kill ALL bot processes
sudo pkill -9 -f "python.*bot"

# Verify nothing running
ps aux | grep "python.*bot" | grep -v grep
# Should show ZERO results

# Wait
sleep 10

# Clear cache
cd /opt/nsfw-bot
rm -rf __pycache__ .venv/__pycache__

# Start fresh
sudo systemctl start nsfw-bot

# Verify ONE instance
systemctl status nsfw-bot
# Should show: Active: active (running)
```

### Step 2: Add Debug Logging (Temporary)

Edit `/opt/nsfw-bot/bot.py` line ~1115:

```python
async def scan_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scan stickers for NSFW content"""
    msg = update.effective_message
    
    # DEBUG LOGGING - ADD THESE LINES
    print(f"\n🔍 STICKER HANDLER TRIGGERED")
    print(f"   Chat ID: {msg.chat.id}")
    print(f"   Sticker: {msg.sticker.file_id}")
    print(f"   Format: {msg.sticker.format}")
    
    if not msg or not msg.sticker:
        print("   ❌ No sticker found")
        return
    
    chat_id = msg.chat.id
    settings_dict = get_chat_settings(chat_id)
    
    print(f"   Settings: {settings_dict.get('sticker_scan')}")
    
    # Check if sticker scanning is enabled
    if not settings_dict.get("sticker_scan", False):
        print("   ❌ Sticker scan disabled for this chat")
        return
    
    print("   ✅ Processing sticker...")
    
    # ... rest of existing code
```

Then restart:
```bash
sudo systemctl restart nsfw-bot
```

Now send a sticker and check logs:
```bash
journalctl -u nsfw-bot -f
```

You should see the debug output!

### Step 3: Verify Settings Are Saved

The issue might be that settings reset. Let's add persistence check.

Edit `/opt/nsfw-bot/bot.py` in the `button_callback` function around line ~788:

```python
elif data == "toggle_sticker_scan":
    settings_dict["sticker_scan"] = not settings_dict["sticker_scan"]
    print(f"✅ Sticker scan toggled to: {settings_dict['sticker_scan']} for chat {chat_id}")
```

This will log every time someone toggles the setting.

---

## 🎯 Alternative: Simplified Detection Logic

If the current complex frame extraction isn't working, let's simplify temporarily.

Add this simpler version as a test (replace entire `scan_sticker` function temporarily):

```python
async def scan_sticker_simple(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simplified sticker scanner for testing"""
    msg = update.effective_message
    if not msg or not msg.sticker:
        return
    
    chat_id = msg.chat.id
    settings_dict = get_chat_settings(chat_id)
    
    if not settings_dict.get("sticker_scan", False):
        return
    
    try:
        print(f"📊 Scanning sticker in chat {chat_id}")
        
        sticker = msg.sticker
        file = await context.bot.get_file(sticker.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            await file.download_to_drive(custom_path=tmp_path)
            print(f"   Downloaded to {tmp_path}")
            
            # Simple classifier approach
            from nudenet import NudeClassifier
            classifier = NudeClassifier()
            result = classifier.classify(tmp_path)
            
            unsafe_score = list(result.values())[0].get("unsafe", 0.0)
            print(f"   Unsafe score: {unsafe_score:.2f}")
            
            if unsafe_score > 0.7:
                await msg.delete()
                await send_temp(context, chat_id, 
                    f"⚠️ NSFW sticker detected! (score: {unsafe_score:.2f})", 10)
                print("   ✅ Deleted NSFW sticker")
            else:
                print("   ✅ Safe sticker")
                
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
```

This simpler version will help isolate if the issue is with:
- Handler not triggering → You won't see any logs
- Download failing → You'll see download error
- Classification failing → You'll see classifier error
- Settings not saved → You'll see it's always disabled

---

## 📊 Expected Debug Output (When Working)

Send a sticker and you should see:

```
🔍 STICKER HANDLER TRIGGERED
   Chat ID: -1001234567890
   Sticker: AgADAgAT...
   Format: 1
   Settings: True
   ✅ Processing sticker...
Processing animated sticker (24 frames)...
Extracted 6 frames from animated sticker
NSFW detected in frame_0.png with score 0.92
   ✅ Deleted NSFW sticker
```

If you see **nothing**, the handler isn't being triggered at all (likely conflict errors).

---

## 🔍 Most Likely Issues & Fixes

### Issue 1: Still Getting Conflict Errors

**Symptom:** Logs still show "Conflict: terminated by other getUpdates"

**Fix:**
```bash
# Find what else is using your bot token
ps aux | grep python

# Look for ANY process with "bot" or "telegram"
# Kill them ALL
sudo pkill -9 -f "python.*telegram"
sudo pkill -9 -f "python.*bot"

# Check screen/tmux sessions
screen -ls
tmux ls

# Kill any sessions running bots
screen -S [session] -X quit
```

### Issue 2: Handler Never Triggered

**Symptom:** No debug output when sending sticker

**Possible causes:**
1. Handler order wrong (other handler catching first)
2. Filter not matching
3. Bot can't read messages in that chat

**Fix:** Move sticker handler EARLIER in the handler list:

Edit `bot.py` line ~1280:
```python
# Put THIS FIRST before other message handlers
app.add_handler(MessageHandler(filters.Sticker.ALL, scan_sticker))
app.add_handler(MessageHandler(filters.PHOTO, scan_photo))
app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL & ~filters.PHOTO & ~filters.Sticker.ALL, handle_any_message))
```

### Issue 3: Settings Always False

**Symptom:** Logs show "Settings: False" even after enabling

**Cause:** Settings stored in memory, lost on restart

**Fix:** Re-enable via `/settings` after EVERY restart

**Future fix:** Add database persistence

---

## ✅ Quick Test Checklist

Run this IN ORDER:

1. **[ ] Kill all instances:**
   ```bash
   sudo pkill -9 -f "python.*bot"
   sleep 5
   ```

2. **[ ] Clear cache:**
   ```bash
   cd /opt/nsfw-bot && rm -rf __pycache__
   ```

3. **[ ] Start bot:**
   ```bash
   systemctl start nsfw-bot
   ```

4. **[ ] Enable feature:**
   - Send `/settings` to bot
   - Click "Sticker NSFW Scan" until ✅

5. **[ ] Send sticker:**
   - Watch logs: `journalctl -u nsfw-bot -f`
   - Should see debug output

6. **[ ] Check for conflicts:**
   ```bash
   journalctl -u nsfw-bot | grep -i conflict
   ```
   Should show NOTHING

---

## 🎯 Bottom Line

**Don't rewrite with Pyrogram!** Your current bot already works. The issue is almost certainly:

1. **Conflict errors** (90% chance) → Kill all instances
2. **Settings not enabled** (5% chance) → Re-enable via /settings  
3. **Handler order** (3% chance) → Move handler earlier
4. **Actual bug** (2% chance) → Debug logs will reveal

Start with killing all conflicting instances!
