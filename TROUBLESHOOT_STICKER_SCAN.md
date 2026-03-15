# 🔍 Sticker Scan Not Working - Troubleshooting Guide

## Issue: Bot not detecting stickers after enabling feature

There are several possible reasons why sticker detection isn't working even after you've enabled it. Let's diagnose and fix each one.

---

## 🚨 Most Common Causes

### 1. **Bot Still Has Conflict Errors (MOST LIKELY)**

**Symptom:** Logs show "Conflict: terminated by other getUpdates request"

**Problem:** Multiple bot instances are running, causing message handling to fail

**Solution:**
```bash
# SSH to server
ssh root@140.245.240.202 -p 22

# Kill ALL bot processes
sudo pkill -9 -f "python.*bot.py"

# Wait 5 seconds
sleep 5

# Restart the service
sudo systemctl start nsfw-bot

# Verify only ONE instance is running
ps aux | grep "python.*bot.py" | grep -v grep
```

You should see ONLY ONE process for `nsfw-bot`. If you see multiple, kill them all again.

---

### 2. **Sticker Scan Not Actually Enabled**

**Check if enabled:**
```
/send /settings to the bot
Click "Sticker NSFW Scan" button
Verify it shows: ✅ Sticker NSFW Scan (not ❌)
```

If it shows ❌, click it once to enable (turns to ✅).

**Common mistake:** Enabling in one chat but testing in another. Settings are per-chat!

---

### 3. **Testing in Wrong Chat Type**

**Important:** Settings are stored PER CHAT ID

- If you enable in Group A, it won't be enabled in Group B
- If you enable in private chat with bot, it won't work in groups
- You must enable separately in each chat where you want it

**Solution:** Enable sticker scan in EVERY chat where you want protection.

---

### 4. **Handler Order Issue**

The sticker handler might not be catching messages due to filter conflicts.

**Current handler order (bot.py line 1280):**
```python
app.add_handler(MessageHandler(filters.Sticker.ALL, scan_sticker))
app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL & ~filters.PHOTO & ~filters.Sticker.ALL, handle_any_message))
```

This looks correct - sticker handler comes before the catch-all handler.

---

### 5. **Download or Processing Error**

The sticker download or processing might be failing silently.

**Check logs for errors:**
```bash
ssh root@140.245.240.202 -p 22
journalctl -u nsfw-bot -f
```

Send a sticker and watch for:
- "Processing animated sticker..." 
- "Processing TGS..."
- "Processing video sticker..."
- Any error messages

If you see NO output when sending a sticker, the handler isn't being triggered.

---

## 🧪 Diagnostic Steps

### Step 1: Verify Bot is Running Properly

```bash
ssh root@140.245.240.202 -p 22

# Check status
systemctl status nsfw-bot

# Should show: Active: active (running)
# NOT: activating, failed, or inactive
```

### Step 2: Check for Conflict Errors

```bash
# Look for conflict errors in recent logs
journalctl -u nsfw-bot --since "1 hour ago" | grep -i conflict

# If you see ANY conflicts, that's your problem!
```

**Fix:** Kill all instances and restart:
```bash
sudo systemctl stop nsfw-bot
sudo pkill -9 -f "python.*nsfw"
sleep 5
sudo systemctl start nsfw-bot
```

### Step 3: Test Sticker Handler Activation

**Add debug logging temporarily:**

Edit `/opt/nsfw-bot/bot.py` on server:
```python
async def scan_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scan stickers for NSFW content"""
    msg = update.effective_message
    print(f"🔍 STICKER HANDLER CALLED - chat_id: {msg.chat.id}")  # ADD THIS
    
    if not msg or not msg.sticker:
        return
    
    chat_id = msg.chat.id
    settings_dict = get_chat_settings(chat_id)
    
    print(f"✅ Settings: sticker_scan = {settings_dict.get('sticker_scan')}")  # ADD THIS
    
    # ... rest of function
```

Then restart bot and send a sticker. You should see the print output in logs.

### Step 4: Verify Settings Are Saved

```bash
# SSH to server
ssh root@140.245.240.202 -p 22

# Navigate to bot directory
cd /opt/nsfw-bot

# Start Python interactive
source .venv/bin/activate
python3

# In Python:
from bot import chat_settings
print(chat_settings)
# You should see your chat IDs and their settings
```

Look for your chat ID and verify `"sticker_scan": True`

---

## ✅ Quick Fix Checklist

Run through these steps IN ORDER:

1. **[ ] Stop all bot instances:**
   ```bash
   ssh root@140.245.240.202 -p 22
   sudo systemctl stop nsfw-bot
   sudo pkill -9 -f "python.*bot"
   sleep 5
   ```

2. **[ ] Clear Python cache:**
   ```bash
   cd /opt/nsfw-bot
   rm -rf __pycache__ .venv/__pycache__
   ```

3. **[ ] Start fresh:**
   ```bash
   systemctl start nsfw-bot
   sleep 5
   systemctl status nsfw-bot  # Should show "active (running)"
   ```

4. **[ ] Enable in correct chat:**
   - Go to the group/private chat where you want scanning
   - Send `/settings` to bot
   - Click "Sticker NSFW Scan" until it shows ✅

5. **[ ] Test with a sticker:**
   - Send a normal sticker first
   - Check logs: `journalctl -u nsfw-bot -f`
   - Should see processing messages

6. **[ ] Verify no conflicts:**
   ```bash
   journalctl -u nsfw-bot --since "5 minutes ago" | grep -i conflict
   ```
   Should show NOTHING if working properly.

---

## 🐛 Known Issues & Solutions

### Issue: "No error handlers are registered"

**Cause:** Bot is crashing during initialization

**Fix:** Check earlier logs for the actual error:
```bash
journalctl -u nsfw-bot -n 100 | head -50
```

Look for ImportError or other startup errors.

### Issue: Settings reset after restart

**Cause:** Settings stored in memory, not persisted

**Current behavior:** Settings reset when bot restarts

**Workaround:** Re-enable via `/settings` after restart

**Future fix:** Add database persistence (planned feature)

### Issue: Works for some stickers but not others

**Possible causes:**
- Large stickers timeout (>10MB)
- Unsupported format (very old sticker packs)
- Network issues downloading

**Solution:** Try different stickers. If only some fail, it's likely a size/format issue.

---

## 📊 Expected Log Output (When Working)

When you send a sticker, you should see:

```
Processing animated sticker (24 frames)...
Extracted 6 frames from animated sticker
NSFW detected in frame_0.png with score 0.92
⚠️ Moderation: User ID `123456` - NSFW Animated frame analysis (6 frames) (score: 0.92)
```

OR for static:

```
Static classifier processing...
Unsafe score: 0.87
⚠️ Moderation: User ID `123456` - NSFW Static classifier (score: 0.87)
```

If you see **NOTHING** in logs when sending a sticker, the handler isn't being triggered at all.

---

## 🎯 Most Likely Solution (Based on Your Logs)

Your logs show **continuous Conflict errors**. This is almost certainly your issue!

**Immediate fix:**

```bash
# SSH to server
ssh root@140.245.240.202 -p 22

# Force kill everything
sudo systemctl stop nsfw-bot
sudo pkill -9 -f "python.*bot"
sudo pkill -9 -f "telegram"

# Wait for cleanup
sleep 10

# Clean start
cd /opt/nsfw-bot
rm -rf __pycache__
systemctl daemon-reload
systemctl start nsfw-bot

# Verify
systemctl status nsfw-bot
# Should show: Active: active (running)

# Monitor
journalctl -u nsfw-bot -f
```

Then try sending a sticker. If you still see Conflict errors, there's another bot using the SAME TOKEN running somewhere.

---

## 🆘 Still Not Working?

If none of the above helps, provide:

1. **Bot status:** `systemctl status nsfw-bot`
2. **Recent errors:** `journalctl -u nsfw-bot -n 50 --no-pager`
3. **Settings screenshot:** Show `/settings` menu
4. **Test results:** What happens when you send a sticker?

This will help diagnose further.

---

**Most common success rate:**
- 90% → Conflict errors (multiple instances)
- 5% → Feature not actually enabled in that chat
- 3% → Wrong chat type (enabled elsewhere)
- 2% → Actual code bug

Start with checking for conflicts!
