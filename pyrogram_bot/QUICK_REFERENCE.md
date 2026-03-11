# 🚀 Pyrogram + Redis Bot - Quick Reference Card

## Architecture at a Glance

```
User → Bot (Pyrogram) → Redis Queue → Worker (GPU) → Result
```

---

## File Structure

```
pyrogram_bot/
├── bot.py           # Main bot - message handlers
├── config.py        # Settings & credentials
├── detector.py      # NSFW detection logic
├── frames.py        # Frame extraction utilities
├── worker.py        # Redis queue worker
├── queue_manager.py # Redis operations
├── requirements.txt # Dependencies
└── start.sh         # Quick start script
```

---

## Quick Start (Local Testing)

### 1. Install Redis
```bash
# macOS
brew install redis
redis-server --daemonize yes

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

### 2. Setup Bot
```bash
cd pyrogram_bot
pip install -r requirements.txt
nano config.py  # Add API_ID, API_HASH, BOT_TOKEN
```

### 3. Run Services
```bash
# Terminal 1: Worker
python worker.py &

# Terminal 2: Bot
python bot.py &
```

### 4. Test
```
Telegram → /start → Should respond
Telegram → /settings → Should show menu
```

---

## Server Deployment (Quick Commands)

### 1. SSH to Server
```bash
ssh root@140.245.240.202 -p 22
# Password: Akshay343402355468
```

### 2. Install Redis
```bash
apt install redis-server -y
systemctl start redis
```

### 3. Deploy Code
```bash
cd /opt/nsfw-bot
cp -r ~/pyrogram_bot/* .
source .venv/bin/activate
pip install pyrogram tgcrypto redis rq opencv-python lottie
```

### 4. Configure
```bash
nano config.py
# Add: API_ID, API_HASH, BOT_TOKEN
```

### 5. Stop Old Bot
```bash
systemctl stop nsfw-bot
pkill -9 -f "python.*bot"
```

### 6. Start New Services
```bash
# Option A: Systemd (recommended)
systemctl enable pyrogram-nsfw-bot pyrogram-nsfw-worker
systemctl start pyrogram-nsfw-bot pyrogram-nsfw-worker

# Option B: Manual
python worker.py &
python bot.py &
```

---

## Bot Commands

| Command | Description | Response |
|---------|-------------|----------|
| `/start` | Welcome message | Bot capabilities overview |
| `/settings` | Configure moderation | Interactive menu with toggles |

---

## Settings Menu

Toggle buttons for:
- 📷 **Photos** - Scan photos (default: ✅ ON)
- 🎥 **Videos** - Scan videos (default: ❌ OFF)
- 🎬 **GIFs** - Scan animations (default: ❌ OFF)
- 🏷️ **Stickers** - Scan stickers (default: ❌ OFF)
- 🗑️ **Auto-Delete** - Delete NSFW content (default: ✅ ON)

Click any button to toggle ON/OFF.

---

## Detection Flow

### Photo
```
Download → NudeClassifier → Score > 0.7? → Delete + Warn
```

### Animated GIF/WebP
```
Download → Extract frames (every 4th) → 
Scan each frame → Max score > 0.7? → Delete + Warn
```

### TGS Lottie
```
Download .tgs → Convert to GIF → 
Extract frames → Scan each → Delete if NSFW
```

### Video Sticker
```
Download .webm → Extract frames (every 30) → 
Scan each → Max score > 0.7? → Delete + Warn
```

---

## Monitoring Commands

### Check Redis
```bash
redis-cli ping              # Test connection
redis-cli LLEN queue_name   # Queue size
redis-cli --stat            # Real-time stats
```

### Check Processes
```bash
ps aux | grep worker.py     # Workers running
ps aux | grep bot.py        # Bot instances
# Should see: 1 bot + N workers
```

### View Logs
```bash
# Systemd logs
journalctl -u pyrogram-nsfw-bot -f
journalctl -u pyrogram-nsfw-worker -f

# Manual logs
tail -f logs/bot.log
tail -f logs/worker.log
```

### Check Queue
```bash
# Watch queue size
watch -n 1 'redis-cli LLEN nsfw_detection_queue'

# Clear queue (emergency)
redis-cli DEL nsfw_detection_queue
```

---

## Troubleshooting

### Conflict Errors
```bash
# Kill all bots
pkill -9 -f "python.*bot"
sleep 10

# Start fresh
systemctl start pyrogram-nsfw-bot
```

### Redis Not Running
```bash
systemctl status redis
systemctl start redis
redis-cli ping  # Should return PONG
```

### Workers Stuck
```bash
# Restart worker
systemctl restart pyrogram-nsfw-worker

# Or manually
pkill -f worker.py
cd /opt/nsfw-bot && source .venv/bin/activate
python worker.py &
```

### Bot Not Responding
```bash
# Check if running
ps aux | grep bot.py

# Check logs
journalctl -u pyrogram-nsfw-bot -n 50

# Restart
systemctl restart pyrogram-nsfw-bot
```

---

## Performance Tuning

### Faster Processing (Lower Accuracy)
Edit `config.py`:
```python
GIF_FRAME_SAMPLE = 6      # Was 4 (extract fewer frames)
FRAME_SAMPLE_RATE = 8     # Was 5
NSFW_THRESHOLD = 0.75     # Was 0.7 (stricter)
```

### Slower Processing (Higher Accuracy)
Edit `config.py`:
```python
GIF_FRAME_SAMPLE = 2      # Was 4 (extract more frames)
FRAME_SAMPLE_RATE = 3     # Was 5
NSFW_THRESHOLD = 0.65     # Was 0.7 (more sensitive)
```

### Scale Workers
```bash
# Low traffic (1 worker)
python worker.py &

# Medium traffic (3 workers)
for i in {1..3}; do python worker.py & done

# High traffic (10 workers)
for i in {1..10}; do python worker.py & done
```

---

## Configuration Options

### config.py Key Settings
```python
# Telegram credentials
API_ID = 123456
API_HASH = "your_hash"
BOT_TOKEN = "your_token"

# Detection
NSFW_THRESHOLD = 0.7       # 0.5=strict, 0.85=lenient

# Processing
MAX_FILE_SIZE_MB = 50      # Reject larger files
GIF_FRAME_SAMPLE = 4       # Extract every 4th frame
FRAME_SAMPLE_RATE = 5      # Extract every 5th frame

# Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
```

---

## Dependencies

### Core
- `pyrogram` - Telegram bot framework
- `tgcrypto` - Fast Telegram encryption
- `redis` - Queue backend
- `rq` - Task queue

### NSFW Detection
- `nudenet` - Nude classifier/detector
- `Pillow` - Image processing
- `opencv-python` - Video frame extraction
- `lottie` - TGS conversion

### Optional
- `deepface` - Age/gender detection
- `imagehash` - Perceptual hashing
- `torch` - GPU acceleration

---

## Production Checklist

- [ ] Redis installed and running
- [ ] Dependencies installed
- [ ] config.py configured
- [ ] Old bot stopped
- [ ] New bot started via systemd
- [ ] Worker started via systemd
- [ ] No conflict errors
- [ ] Bot responds to /start
- [ ] /settings works
- [ ] Test photo detection
- [ ] Test sticker detection
- [ ] Logs clean

---

## Scaling Guide

| Traffic Level | Workers | Throughput | Server Requirements |
|---------------|---------|------------|---------------------|
| Small (<1K members) | 1 | ~100/min | 1 CPU, 1GB RAM |
| Medium (1-5K) | 3 | ~300/min | 2 CPU, 2GB RAM |
| Large (5-10K) | 5 | ~500/min | 4 CPU, 4GB RAM |
| XL (>10K) | 10+ | ~1000/min | 8 CPU, 8GB RAM + GPU |

---

## Emergency Procedures

### Stop Everything
```bash
systemctl stop pyrogram-nsfw-bot
systemctl stop pyrogram-nsfw-worker
pkill -9 -f "python.*bot"
redis-cli FLUSHDB  # Clear queue (use carefully!)
```

### Start Everything
```bash
systemctl start redis
systemctl start pyrogram-nsfw-bot
systemctl start pyrogram-nsfw-worker
```

### Clear Stuck Queue
```bash
# Stop worker first
systemctl stop pyrogram-nsfw-worker

# Clear queue
redis-cli DEL nsfw_detection_queue

# Restart worker
systemctl start pyrogram-nsfw-worker
```

---

## Success Indicators

✅ **Bot Running:**
```bash
systemctl status pyrogram-nsfw-bot
# Active: active (running)
```

✅ **Worker Running:**
```bash
ps aux | grep worker.py
# Shows 1+ processes
```

✅ **Redis Running:**
```bash
redis-cli ping
# Returns: PONG
```

✅ **No Conflicts:**
```bash
journalctl -u pyrogram-nsfw-bot | grep -i conflict
# Returns: nothing
```

✅ **Queue Processing:**
```bash
watch -n 1 'redis-cli LLEN nsfw_detection_queue'
# Number stays low or decreases
```

---

## Documentation Files

| File | Purpose |
|------|---------|
| `PYROGRAM_REDIS_ARCHITECTURE.md` | Complete architecture guide (592 lines) |
| `DEPLOY_PYROGRAM_REDIS.md` | Step-by-step deployment (534 lines) |
| `PYROGRAM_REDIS_SUMMARY.md` | Overview and summary (469 lines) |
| `QUICK_REFERENCE.md` | This file - quick commands |

---

## Get Help

1. **Check logs:** `journalctl -u pyrogram-nsfw-bot -f`
2. **View docs:** Open relevant `.md` file
3. **Test locally:** Run `./start.sh` in `pyrogram_bot/`
4. **Debug mode:** Add `print()` statements to code

---

**🚀 You're ready to deploy!** 

Start with local testing, then deploy to server following the deployment guide.
