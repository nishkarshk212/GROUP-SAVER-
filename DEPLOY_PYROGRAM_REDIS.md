# 🚀 Deploying Pyrogram + Redis Bot to Server

## Prerequisites

- Your server: `140.245.240.202` (Ubuntu/Debian)
- SSH access: `ssh root@140.245.240.202 -p 22`
- Password: `Akshay343402355468`

---

## Step-by-Step Deployment

### Phase 1: Server Preparation

#### 1. SSH to Server
```bash
ssh root@140.245.240.202 -p 22
# Password: Akshay343402355468
```

#### 2. Install Redis Server
```bash
apt update
apt install redis-server -y
systemctl start redis
systemctl enable redis
```

Verify Redis:
```bash
redis-cli ping
# Should return: PONG
```

#### 3. Install Python Dependencies
```bash
cd /opt/nsfw-bot
source .venv/bin/activate

# Install new dependencies
pip install pyrogram tgcrypto redis rq opencv-python lottie deepface imagehash
```

---

### Phase 2: Deploy New Bot Code

#### Option A: Fresh Installation (Recommended)

```bash
# Navigate to bot directory
cd /opt/nsfw-bot

# Backup old bot
mv bot.py bot_old.py

# Copy new bot files
cp -r /Users/nishkarshkr/Desktop/bot-app/pyrogram_bot/* .

# Verify files
ls -la
# Should see: bot.py, config.py, detector.py, frames.py, worker.py, queue_manager.py
```

#### Option B: Git Deployment

```bash
cd /opt/nsfw-bot

# Add new files to git
git add pyrogram_bot/
git commit -m "Add Pyrogram + Redis architecture"
git push origin main

# Then on server
git pull origin main
```

---

### Phase 3: Configuration

#### 1. Edit config.py

```bash
nano config.py
```

Update these values:
```python
API_ID = 123456  # Get from my.telegram.org
API_HASH = "your_actual_api_hash"
BOT_TOKEN = "your_actual_bot_token"

NSFW_THRESHOLD = 0.7
MAX_FILE_SIZE_MB = 50
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

#### 2. Create Required Directories

```bash
mkdir -p temp logs
chmod 777 temp
```

---

### Phase 4: Start Services

#### 1. Start Redis Worker (Terminal 1)

```bash
cd /opt/nsfw-bot
source .venv/bin/activate

# Start worker in background
nohup python worker.py > logs/worker.log 2>&1 &

# Verify worker is running
ps aux | grep worker.py
```

You should see output like:
```
root 12345  0.5  1.2 123456 78901 ?  Ssl  12:34   0:00 python worker.py
```

#### 2. Start Pyrogram Bot (Terminal 2)

```bash
cd /opt/nsfw-bot
source .venv/bin/activate

# Start bot in background
nohup python bot.py > logs/bot.log 2>&1 &

# Verify bot is running
ps aux | grep bot.py
```

---

### Phase 5: Stop Old Bot

**CRITICAL:** Stop the old bot to prevent conflicts!

```bash
# Stop systemd service
systemctl stop nsfw-bot
systemctl disable nsfw-bot

# Kill any remaining bot processes
pkill -9 -f "python.*bot"

# Verify nothing is running
ps aux | grep "python.*bot" | grep -v grep
# Should show ZERO results (or only your new pyrogram bot)
```

---

### Phase 6: Verification

#### 1. Check All Services

```bash
# Redis status
systemctl status redis
# Should show: active (running)

# Worker process
ps aux | grep worker.py | grep -v grep
# Should show 1+ workers

# Bot process
ps aux | grep bot.py | grep -v grep
# Should show 1 bot instance
```

#### 2. Test Bot

Send `/start` to your bot on Telegram.

Expected response:
```
🤖 NSFW Moderation Bot

I can detect and moderate NSFW content including:
• Photos
• Videos
• GIFs
• Stickers (including animated)

Use /settings to configure moderation options.
```

#### 3. Check Logs

```bash
# Bot logs
tail -f logs/bot.log

# Worker logs
tail -f logs/worker.log

# Redis logs
journalctl -u redis -f
```

---

## 🔧 Systemd Services (Production Setup)

For automatic startup and management, create systemd services:

### 1. Bot Service

Create `/etc/systemd/system/pyrogram-nsfw-bot.service`:

```ini
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
```

### 2. Worker Service

Create `/etc/systemd/system/pyrogram-nsfw-worker.service`:

```ini
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
```

### 3. Enable Services

```bash
# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable pyrogram-nsfw-bot
systemctl enable pyrogram-nsfw-worker

# Start services
systemctl start pyrogram-nsfw-bot
systemctl start pyrogram-nsfw-worker

# Check status
systemctl status pyrogram-nsfw-bot
systemctl status pyrogram-nsfw-worker
```

---

## 📊 Monitoring

### Queue Status

```bash
# Check queue size
redis-cli LLEN nsfw_detection_queue

# Watch queue in real-time
watch -n 1 'redis-cli LLEN nsfw_detection_queue'
```

### Process Status

```bash
# Count workers
ps aux | grep worker.py | grep -v grep | wc -l

# Count bot instances
ps aux | grep bot.py | grep -v grep | wc -l
# Should be 1
```

### Logs

```bash
# Real-time bot logs
journalctl -u pyrogram-nsfw-bot -f

# Real-time worker logs
journalctl -u pyrogram-nsfw-worker -f

# Redis logs
journalctl -u redis -f
```

---

## 🐛 Troubleshooting

### Issue 1: Conflict Errors (Old Bot Still Running)

**Symptom:** Logs show "Conflict: terminated by other getUpdates"

**Fix:**
```bash
# Stop old service
systemctl stop nsfw-bot

# Kill all bot processes
pkill -9 -f "python.*bot"

# Wait
sleep 10

# Start new bot
systemctl start pyrogram-nsfw-bot
```

### Issue 2: Redis Not Connecting

**Symptom:** `redis.exceptions.ConnectionError`

**Fix:**
```bash
# Check Redis status
systemctl status redis

# Start Redis
systemctl start redis

# Test connection
redis-cli ping
```

### Issue 3: Bot Won't Start

**Symptom:** Bot crashes immediately

**Check logs:**
```bash
journalctl -u pyrogram-nsfw-bot -n 50 --no-pager
```

**Common fixes:**
- Wrong API_ID/API_HASH → Edit config.py
- Invalid BOT_TOKEN → Get new token from @BotFather
- Port already in use → Change port or kill process

### Issue 4: Workers Not Processing

**Symptom:** Queue growing but tasks not processed

**Check:**
```bash
# Is worker running?
ps aux | grep worker.py

# Queue size?
redis-cli LLEN nsfw_detection_queue
```

**Fix:**
```bash
# Restart worker
systemctl restart pyrogram-nsfw-worker

# Or manually
pkill -f worker.py
cd /opt/nsfw-bot && source .venv/bin/activate
python worker.py &
```

---

## 🎯 Performance Tuning

### Multiple Workers (High Traffic)

For groups with 1000+ messages/day:

```bash
# Start 3 workers
for i in {1..3}; do
    systemctl start pyrogram-nsfw-worker-$i
done
```

Or adjust systemd to run multiple instances.

### Frame Sampling Adjustment

For faster processing (lower accuracy):

Edit `config.py`:
```python
GIF_FRAME_SAMPLE = 6  # Was 4
FRAME_SAMPLE_RATE = 8  # Was 5
```

### GPU Acceleration

If you have NVIDIA GPU:

```bash
# Install CUDA support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Run worker with GPU
CUDA_VISIBLE_DEVICES=0 python worker.py
```

---

## ✅ Deployment Checklist

- [ ] Redis installed and running
- [ ] Python dependencies installed
- [ ] config.py updated with API credentials
- [ ] Old bot stopped and disabled
- [ ] New bot started via systemd
- [ ] Worker started via systemd
- [ ] No conflict errors in logs
- [ ] Bot responds to /start command
- [ ] /settings menu works
- [ ] Test photo detection works
- [ ] Test sticker detection works (enable via /settings first)
- [ ] Queue processing correctly
- [ ] Logs clean (no critical errors)

---

## 📈 Scaling Strategy

### Current Architecture:

```
1 Bot Instance + 1 Worker → ~100 images/minute
```

### Scale Horizontally:

```
1 Bot Instance + N Workers → ~N × 100 images/minute
```

### Add Workers:

```bash
# Start additional worker
python worker.py &

# Or via systemd
systemctl start pyrogram-nsfw-worker-2
systemctl start pyrogram-nsfw-worker-3
```

Redis automatically load-balances tasks across workers!

---

## 🎉 Post-Deployment

### 1. Test Basic Functionality

```
/send /start to bot → Should respond
/send /settings → Should show menu
/Send photo → Should detect if NSFW
```

### 2. Enable Sticker Scanning

```
/send /settings
Click "🏷️ Stickers" until ✅
Send animated sticker → Should scan frames
```

### 3. Monitor First 24 Hours

```bash
# Check for errors
journalctl -u pyrogram-nsfw-bot --since "24 hours ago" | grep -i error

# Check queue processing
redis-cli LLEN nsfw_detection_queue

# Check memory usage
free -h
```

---

## 🚀 You're Ready!

Your Pyrogram + Redis bot is now deployed with:
- ✅ Async message processing
- ✅ Scalable worker architecture  
- ✅ Redis task queue
- ✅ Support for photos, videos, GIFs, stickers
- ✅ Per-chat settings
- ✅ Automatic restart via systemd

**Next:** Monitor performance and adjust worker count based on load!
