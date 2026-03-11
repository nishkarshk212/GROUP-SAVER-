# 🚀 Manual Deployment Guide - Pyrogram + Redis Bot

## Quick Deployment Commands

Follow these steps IN ORDER to deploy your new Pyrogram bot to the server.

---

## Step 1: SSH to Server

Open a **NEW terminal** and connect:

```bash
ssh root@140.245.240.202 -p 22
# Password: Akshay343402355468
```

Type `yes` when asked about host authenticity, then enter password.

---

## Step 2: Install Redis (Required)

Once connected to server:

```bash
# Update package list
apt update

# Install Redis
apt install redis-server -y

# Start Redis
systemctl start redis

# Enable Redis on boot
systemctl enable redis

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

---

## Step 3: Stop Old Bot (CRITICAL!)

```bash
# Stop systemd service
systemctl stop nsfw-bot

# Disable auto-start
systemctl disable nsfw-bot

# Kill ALL bot processes
pkill -9 -f "python.*bot"

# Wait for cleanup
sleep 10

# Verify zero instances
ps aux | grep "python.*bot" | grep -v grep
# Should show ZERO results (or only unrelated bots)
```

---

## Step 4: Copy New Bot Files

**On your LOCAL machine** (not SSH), run:

```bash
cd /Users/nishkarshkr/Desktop/bot-app

# Copy files to server
scp -P 22 -r pyrogram_bot/* root@140.245.240.202:/opt/nsfw-bot/
```

When prompted with "Are you sure you want to continue connecting", type `yes`.
Enter password: `Akshay343402355468`

This will copy all bot files to the server.

---

## Step 5: Configure Bot (On Server via SSH)

**Back in your SSH session**, configure the bot:

```bash
cd /opt/nsfw-bot

# Edit config.py
nano config.py
```

Update these values in config.py:

```python
API_ID = 123456  # Get from https://my.telegram.org
API_HASH = "your_actual_api_hash_here"  # Get from https://my.telegram.org
BOT_TOKEN = "your_actual_bot_token_here"  # From @BotFather
```

**How to get credentials:**

1. **API_ID & API_HASH:**
   - Go to https://my.telegram.org
   - Login with your phone number
   - Click "API development tools"
   - Create a new application
   - Copy App api_id and App api_hash

2. **BOT_TOKEN:**
   - Open Telegram
   - Search for @BotFather
   - Send `/newbot` command
   - Follow instructions to create bot
   - Copy the token

Save nano editor:
- Press `Ctrl+X`
- Press `Y` (to confirm save)
- Press `Enter`

---

## Step 6: Install Dependencies (On Server)

```bash
cd /opt/nsfw-bot

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Pyrogram and other dependencies
pip install pyrogram tgcrypto redis rq opencv-python lottie deepface imagehash --no-cache-dir

echo "✅ Dependencies installed"
```

---

## Step 7: Create Directories

```bash
# Create temp and logs directories
mkdir -p temp logs

# Set permissions
chmod 777 temp

echo "✅ Directories created"
```

---

## Step 8: Setup Systemd Services

Create the bot service file:

```bash
cat > /etc/systemd/system/pyrogram-nsfw-bot.service << EOF
[Unit]
Description=Pyrogram NSFW Detection Bot
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nsfw-bot
Environment="PATH=/opt/nsfw-bot/.venv/bin"
ExecStart=/opt/nsfw-bot/.venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/pyrogram-bot.log
StandardError=append:/var/log/pyrogram-bot.log

[Install]
WantedBy=multi-user.target
EOF
```

Create the worker service file:

```bash
cat > /etc/systemd/system/pyrogram-nsfw-worker.service << EOF
[Unit]
Description=NSFW Detection Worker
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nsfw-bot
Environment="PATH=/opt/nsfw-bot/.venv/bin"
ExecStart=/opt/nsfw-bot/.venv/bin/python worker.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/pyrogram-worker.log
StandardError=append:/var/log/pyrogram-worker.log

[Install]
WantedBy=multi-user.target
EOF
```

---

## Step 9: Start Services

```bash
# Reload systemd to recognize new services
systemctl daemon-reload

# Enable services (auto-start on boot)
systemctl enable pyrogram-nsfw-bot
systemctl enable pyrogram-nsfw-worker

# Start services
systemctl start pyrogram-nsfw-bot
systemctl start pyrogram-nsfw-worker

# Wait for startup
sleep 5

echo "✅ Services started"
```

---

## Step 10: Verify Deployment

```bash
# Check Redis
systemctl status redis --no-pager -n 5
# Should show: active (running)

# Check Bot
systemctl status pyrogram-nsfw-bot --no-pager -n 5
# Should show: active (running)

# Check Worker
systemctl status pyrogram-nsfw-worker --no-pager -n 5
# Should show: active (running)

# Check for conflicts
journalctl -u pyrogram-nsfw-bot --since "2 minutes ago" | grep -i conflict
# Should show NOTHING (zero output)

# Count processes
ps aux | grep bot.py | grep -v grep
# Should show exactly 1 instance

ps aux | grep worker.py | grep -v grep
# Should show exactly 1 instance
```

---

## Step 11: Test Bot

**On Telegram:**

1. Find your bot (search for the username you got from @BotFather)
2. Send `/start` command
3. Expected response:

```
🤖 **NSFW Moderation Bot**

I can detect and moderate NSFW content including:
• Photos
• Videos
• GIFs
• Stickers (including animated)

Use /settings to configure moderation options.
```

4. Send `/settings` command
5. You should see an interactive menu with toggle buttons

---

## Step 12: Monitor Logs

Watch bot activity in real-time:

```bash
# Real-time bot logs
journalctl -u pyrogram-nsfw-bot -f

# Real-time worker logs  
journalctl -u pyrogram-nsfw-worker -f

# Exit logs with Ctrl+C
```

---

## ✅ Deployment Complete!

Your Pyrogram + Redis bot is now running with:
- ✅ Async message processing
- ✅ Redis task queue
- ✅ Scalable worker architecture
- ✅ All media types supported (photos, videos, GIFs, stickers)
- ✅ Per-chat settings via /settings
- ✅ Automatic restart via systemd

---

## 🎯 Next Steps

### 1. Enable Sticker Scanning

```
On Telegram:
1. Send /settings to bot
2. Click "🏷️ Stickers" button until it shows ✅
3. Send an animated sticker
4. Bot should scan and detect if NSFW
```

### 2. Monitor Performance

```bash
# Check queue size
redis-cli LLEN nsfw_detection_queue

# Watch queue in real-time
watch -n 1 'redis-cli LLEN nsfw_detection_queue'

# Check memory usage
free -h
```

### 3. Adjust Settings (Optional)

Edit `/opt/nsfw-bot/config.py`:

```python
# Stricter detection (more sensitive)
NSFW_THRESHOLD = 0.65

# More lenient detection
NSFW_THRESHOLD = 0.75  # Recommended balance

# Faster processing (lower accuracy)
GIF_FRAME_SAMPLE = 6  # Extract every 6th frame instead of 4
FRAME_SAMPLE_RATE = 8  # Extract every 8th frame instead of 5
```

After editing, restart:
```bash
systemctl restart pyrogram-nsfw-bot
systemctl restart pyrogram-nsfw-worker
```

---

## 🐛 Troubleshooting

### Issue: Conflict Errors

**Symptom:** Logs show "Conflict: terminated by other getUpdates"

**Fix:**
```bash
# Kill everything
pkill -9 -f "python.*bot"
sleep 10

# Restart bot
systemctl restart pyrogram-nsfw-bot
```

### Issue: Redis Not Running

**Symptom:** `redis.exceptions.ConnectionError`

**Fix:**
```bash
systemctl status redis
systemctl start redis
redis-cli ping  # Should return PONG
```

### Issue: Bot Not Responding

**Check:**
```bash
systemctl status pyrogram-nsfw-bot
journalctl -u pyrogram-nsfw-bot -n 50 --no-pager
```

**Common causes:**
- Wrong API_ID/API_HASH → Edit config.py
- Invalid BOT_TOKEN → Get new token from @BotFather
- Another instance running → Kill all and restart

### Issue: Workers Not Processing

**Check:**
```bash
ps aux | grep worker.py
redis-cli LLEN nsfw_detection_queue
```

If queue is growing but workers not processing:
```bash
systemctl restart pyrogram-nsfw-worker
```

---

## 📊 Monitoring Commands

```bash
# Service status
systemctl status pyrogram-nsfw-bot
systemctl status pyrogram-nsfw-worker
systemctl status redis

# Process count
ps aux | grep bot.py | grep -v grep | wc -l  # Should be 1
ps aux | grep worker.py | grep -v grep | wc -l  # Should be 1+

# Queue status
redis-cli LLEN nsfw_detection_queue

# Real-time logs
journalctl -u pyrogram-nsfw-bot -f
journalctl -u pyrogram-nsfw-worker -f
journalctl -u redis -f
```

---

## 🎉 Success Indicators

✅ **All services running:**
```bash
systemctl status pyrogram-nsfw-bot  # active (running)
systemctl status pyrogram-nsfw-worker  # active (running)
systemctl status redis  # active (running)
```

✅ **No conflicts:**
```bash
journalctl -u pyrogram-nsfw-bot | grep -i conflict  # Returns nothing
```

✅ **Bot responds:**
- `/start` → Welcome message
- `/settings` → Interactive menu

✅ **Processing works:**
- Send photo → Bot analyzes
- Enable sticker scan → Send animated sticker → Bot scans frames

---

**🚀 Your production-ready Pyrogram + Redis bot is live!**
