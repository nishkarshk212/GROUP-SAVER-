# 🔧 Pyrogram + Redis Settings Not Working - Troubleshooting Guide

## Problem Identified

Your Pyrogram bot services are **running** but not responding to commands. This is typically caused by:

1. **Session file locked** from previous run
2. **Bot not properly initialized** with Telegram servers
3. **Redis queue not configured** for worker

---

## ✅ Quick Fix (Do This First)

### Step 1: SSH to Server
```bash
ssh root@140.245.240.202 -p 22
# Password: Akshay343402355468
```

### Step 2: Stop Services & Clear Session
```bash
cd /opt/nsfw-bot/pyrogram_bot

# Stop services
systemctl stop pyrogram-nsfw-bot pyrogram-nsfw-worker

# Clear locked session files
rm -f *.session* 2>/dev/null || true

# Kill any stuck processes
pkill -9 -f "python.*bot.py" || true
pkill -9 -f "python.*worker.py" || true

sleep 5
```

### Step 3: Test Bot Manually
```bash
source /opt/nsfw-bot/.venv/bin/activate

# Test config loads
python -c "from config import API_ID, API_HASH, BOT_TOKEN; print('Config OK')"

# Test bot starts (press Ctrl+C after seeing 'Started')
python bot.py
```

Expected output:
```
🚀 Starting NSFW Moderation Bot...
   Temp directory: temp
   Max file size: 50MB
Started.
```

If you see **"Started."** → Bot is working! Press `Ctrl+C` to stop.

### Step 4: Restart Services
```bash
# Start bot service
systemctl start pyrogram-nsfw-bot

# Don't start worker yet (not needed for basic functionality)

# Check status
systemctl status pyrogram-nsfw-bot --no-pager -n 10
```

### Step 5: Test on Telegram
1. Open Telegram
2. Find your bot
3. Send `/start`
4. Should respond with welcome message

---

## 🐛 Common Issues & Fixes

### Issue 1: "database is locked" Error

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Fix:**
```bash
cd /opt/nsfw-bot/pyrogram_bot
rm -f *.session* nsfw-moderator.session*
systemctl restart pyrogram-nsfw-bot
```

---

### Issue 2: Bot Starts But Doesn't Respond

**Possible Causes:**
- Bot token invalid
- Network connectivity issue
- Bot already running elsewhere

**Check:**
```bash
# Verify bot token in config
cat config.py | grep BOT_TOKEN

# Check logs
journalctl -u pyrogram-nsfw-bot -f
```

**Fix:**
1. Get new token from @BotFather
2. Update config.py: `BOT_TOKEN = "new_token"`
3. Restart: `systemctl restart pyrogram-nsfw-bot`

---

### Issue 3: Worker Service Fails with "INVALIDARGUMENT"

**Cause:** Worker expects Redis queue tasks, but none exist yet.

**This is NORMAL!** The worker will fail until the first task is queued.

**Fix:** Just ignore worker errors until bot is working. Focus on getting bot to respond first.

---

### Issue 4: Settings Menu Not Showing

**Symptom:** `/settings` command doesn't show buttons

**Possible Causes:**
- Bot handler not registered
- Callback query handler missing
- Inline keyboard markup error

**Check bot.py has these handlers:**
```python
@app.on_message(filters.command("settings"))
async def settings_command(...)

@app.on_callback_query(filters.regex(r"^toggle_(.*)"))
async def toggle_callback(...)
```

**Fix:**
```bash
# Check bot.py exists and has handlers
grep -n "settings_command\|toggle_callback" bot.py

# If missing, file may be corrupted - restore from Git
git checkout HEAD -- bot.py
systemctl restart pyrogram-nsfw-bot
```

---

### Issue 5: Bot Responds to /start But Not /settings

**Cause:** Settings handler may not be loaded or has error.

**Check Logs:**
```bash
journalctl -u pyrogram-nsfw-bot -f
# Send /settings and watch for errors
```

**Common Fixes:**
1. Restart bot: `systemctl restart pyrogram-nsfw-bot`
2. Check for Python syntax errors: `python -m py_compile bot.py`
3. Verify imports work: `python -c "import bot"`

---

## 🔍 Diagnostic Commands

### Quick Health Check
```bash
ssh root@140.245.240.202 -p 22 << 'EOF'
echo "=== Services ===" && \
systemctl is-active pyrogram-nsfw-bot && \
systemctl is-active pyrogram-nsfw-worker && \
echo "=== Redis ===" && \
redis-cli ping && \
echo "=== Config ===" && \
cd /opt/nsfw-bot/pyrogram_bot && \
python -c "from config import API_ID, BOT_TOKEN; print('Config OK')" && \
echo "=== Processes ===" && \
ps aux | grep "python.*bot" | grep -v grep
EOF
```

Expected output:
```
=== Services ===
active
active
=== Redis ===
PONG
=== Config ===
Config OK
=== Processes ===
root 129734 ... python bot.py
```

---

### Check Bot Responsiveness
```bash
# Watch logs in real-time
journalctl -u pyrogram-nsfw-bot -f

# Then send /start to bot on Telegram
# You should see:
# - Incoming update
# - Handler called
# - Response sent
```

---

### Verify Configuration
```bash
cd /opt/nsfw-bot/pyrogram_bot
cat config.py | grep -E "API_ID|API_HASH|BOT_TOKEN"
```

Should show:
```python
API_ID = 33830507
API_HASH ="54e1e0d86c6c2768b65dc945bb2096c7"
BOT_TOKEN = "8587720230:AAEHakInRNby8me1WtxsoQ_JUbhTJAVJL6s"
```

---

## 🎯 Complete Reset Procedure

If nothing works, do a complete reset:

### 1. Stop Everything
```bash
systemctl stop pyrogram-nsfw-bot pyrogram-nsfw-worker
pkill -9 -f "python.*bot"
pkill -9 -f "python.*worker"
```

### 2. Clear All State
```bash
cd /opt/nsfw-bot/pyrogram_bot
rm -f *.session* __pycache__/*.pyc
rm -rf temp/* logs/*
```

### 3. Verify Files
```bash
ls -la *.py
# Should see: bot.py, config.py, detector.py, frames.py, worker.py, queue_manager.py
```

### 4. Test Locally First
```bash
source /opt/nsfw-bot/.venv/bin/activate

# Test imports
python -c "from config import *; from detector import NSFWDetector; print('All imports OK')"

# Test bot startup
python bot.py  # Press Ctrl+C after seeing "Started"
```

### 5. Start Clean
```bash
# Start bot via systemd
systemctl start pyrogram-nsfw-bot

# Wait 5 seconds
sleep 5

# Check status
systemctl status pyrogram-nsfw-bot --no-pager -n 10

# View logs
journalctl -u pyrogram-nsfw-bot -f
```

### 6. Test on Telegram
- Send `/start` → Should get welcome message
- Send `/settings` → Should show menu with buttons
- Click any button → Should toggle setting

---

## 📊 Expected Behavior

### When Everything Works:

1. **Send /start:**
   ```
   Bot responds immediately with:
   🤖 **NSFW Moderation Bot**
   
   I can detect and moderate NSFW content including:
   • Photos
   • Videos
   • GIFs
   • Stickers (including animated)
   
   Use /settings to configure moderation options.
   ```

2. **Send /settings:**
   ```
   Shows interactive menu with buttons:
   ⚙️ **Moderation Settings**
   
   Chat ID: `-1001234567890`
   
   ✅ Photo Scan: Enabled
   ❌ Video Scan: Disabled
   ...
   
   [Buttons below]
   ```

3. **Click Toggle Button:**
   ```
   Menu refreshes with updated settings:
   ✅ Photo Scan: Disabled (changed from Enabled)
   ```

4. **Logs Show Activity:**
   ```bash
   journalctl -u pyrogram-nsfw-bot -f
   
   # When you send /start:
   Incoming update: {"message": {"text": "/start"}}
   Handler called: start_command
   Response sent successfully
   ```

---

## 🆘 Still Not Working?

### Collect Debug Info:

```bash
# Run this and share the output:
ssh root@140.245.240.202 -p 22 << 'EOF'
echo "=== SERVICE STATUS ==="
systemctl status pyrogram-nsfw-bot --no-pager -n 20
echo ""
echo "=== RECENT ERRORS ==="
journalctl -u pyrogram-nsfw-bot --since "1 hour ago" --no-pager -n 30 | grep -i error
echo ""
echo "=== CONFIG CHECK ==="
cd /opt/nsfw-bot/pyrogram_bot
python -c "from config import API_ID, BOT_TOKEN; print(f'API_ID: {API_ID}, Token set: {bool(BOT_TOKEN)}')"
echo ""
echo "=== IMPORT TEST ==="
python -c "import bot; print('Bot imports OK')" 2>&1 | head -20
echo ""
echo "=== SESSION FILES ==="
ls -la *.session* 2>/dev/null || echo "No session files"
EOF
```

### Manual Test:

Try running bot manually to see detailed errors:

```bash
cd /opt/nsfw-bot/pyrogram_bot
source .venv/bin/activate

# Stop systemd first
systemctl stop pyrogram-nsfw-bot

# Run manually
python bot.py

# Watch for errors, then press Ctrl+C
```

---

## ✅ Success Checklist

After fixing, verify:

- [ ] Bot responds to `/start` within 2 seconds
- [ ] `/settings` shows interactive menu
- [ ] Toggle buttons work (click → menu updates)
- [ ] No "database is locked" errors in logs
- [ ] No "ImportError" in logs
- [ ] Redis responds to `ping` (returns PONG)
- [ ] Only ONE bot process running
- [ ] Bot service is `active (running)`

---

## 🎯 Next Steps After Fix

Once bot responds properly:

1. **Test Photo Detection:**
   - Enable "Photo Scan" via /settings
   - Send a test photo
   - Should analyze and respond

2. **Enable Sticker Scanning:**
   - Click "🏷️ Stickers" in /settings
   - Send animated sticker
   - Should scan frames

3. **Monitor Performance:**
   ```bash
   journalctl -u pyrogram-nsfw-bot -f
   ```

4. **Adjust Settings if Needed:**
   ```bash
   nano /opt/nsfw-bot/pyrogram_bot/config.py
   # Change NSFW_THRESHOLD, etc.
   systemctl restart pyrogram-nsfw-bot
   ```

---

**Ready to troubleshoot?** Start with the "Quick Fix" section above!
