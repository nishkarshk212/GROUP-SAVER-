# 🚀 Pyrogram + Redis NSFW Bot - Complete Architecture

## Overview

This is a **complete rewrite** of your NSFW detection bot using:
- **Pyrogram** - Async Telegram Bot framework (faster, more features)
- **Redis + RQ** - Asynchronous task queue for scalable processing
- **GPU-accelerated workers** - Parallel NSFW detection
- **Modular architecture** - Clean separation of concerns

---

## 📁 Project Structure

```
pyrogram_bot/
├── bot.py              # Main Pyrogram bot with message handlers
├── config.py           # Configuration and settings
├── detector.py         # NSFW detection logic (NudeNet wrapper)
├── frames.py          # Frame extraction from GIFs/videos/TGS
├── worker.py          # Redis Queue worker for async processing
├── queue_manager.py   # Redis queue operations
├── requirements.txt   # Python dependencies
└── temp/             # Temporary file storage (auto-created)
```

---

## 🏗️ Architecture Flow

```
User sends media to Telegram group
        ↓
Pyrogram Bot receives message
        ↓
Downloads media to temp file
        ↓
Creates Redis queue task
        ↓
Redis Queue (nsfw_detection_queue)
        ↓
GPU Worker (polling queue)
        ↓
Processing Pipeline:
  1. Check file type
  2. Extract frames (if animated/video)
  3. Run NudeNet classifier/detector
  4. Calculate max NSFW score
        ↓
Result returned to bot
        ↓
Action taken:
  - Delete message
  - Warn user
  - Log to channel
```

---

## 🔧 Installation

### Step 1: Install Redis Server

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**On macOS:**
```bash
brew install redis
brew services start redis
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

---

### Step 2: Install Python Dependencies

```bash
cd pyrogram_bot
pip install -r requirements.txt
```

---

### Step 3: Configure Environment

Edit `config.py`:

```python
# Get these from https://my.telegram.org
API_ID = 123456
API_HASH = "your_api_hash_here"
BOT_TOKEN = "your_bot_token_from_BotFather"

# Adjust thresholds as needed
NSFW_THRESHOLD = 0.7
MAX_FILE_SIZE_MB = 50
```

---

## 🚀 Running the Bot

### Terminal 1: Start Redis Worker

```bash
cd pyrogram_bot
python worker.py
```

You should see:
```
🚀 Starting NSFW Detection Worker...
   Redis: localhost:6379
   Queue: nsfw_detection
```

---

### Terminal 2: Start Pyrogram Bot

```bash
cd pyrogram_bot
python bot.py
```

You should see:
```
🚀 Starting NSFW Moderation Bot...
   Temp directory: temp
   Max file size: 50MB
```

---

## 🎯 Features

### 1. **Multi-Media Support**

- ✅ **Photos** - Single image NSFW detection
- ✅ **Videos** - Frame extraction + analysis
- ✅ **GIFs/Animations** - Extract frames every 4th frame
- ✅ **Stickers** - Static, Animated WebP, TGS (Lottie), Video stickers

### 2. **Per-Chat Settings**

Each chat can configure:
- Photo scanning (default: ON)
- Video scanning (default: OFF)
- GIF scanning (default: OFF)
- Sticker scanning (default: OFF)
- Text profanity filter (default: ON)
- Auto-delete on detection (default: ON)
- Warn user (default: ON)

### 3. **Async Processing**

- Media downloaded immediately
- Task queued to Redis
- GPU worker processes asynchronously
- Bot continues handling other messages
- No blocking or timeouts!

### 4. **Scalable Workers**

Run multiple workers for parallel processing:

```bash
# Terminal 1: Worker 1
python worker.py

# Terminal 2: Worker 2
python worker.py

# Terminal 3: Worker 3 (GPU optimized)
CUDA_VISIBLE_DEVICES=0 python worker.py
```

---

## 📊 Usage Commands

### `/start` - Bot Introduction

Shows welcome message and capabilities.

### `/settings` - Configure Moderation

Opens interactive settings menu with toggle buttons:

```
⚙️ Moderation Settings

Chat ID: -1001234567890

✅ Photo Scan: Enabled
❌ Video Scan: Disabled
❌ GIF Scan: Disabled
❌ Sticker Scan: Disabled
✅ Text Scan: Enabled
✅ Auto-Delete: Enabled
✅ Warn User: Enabled

[🔄 Toggle All]
[📷 Photos] [🎥 Videos]
[🎬 GIFs] [🏷️ Stickers]
[🗑️ Auto-Delete]
```

Click buttons to toggle features ON/OFF.

---

## 🔍 How Sticker Detection Works

### Static Stickers (.webp)
1. Download sticker
2. Run NudeClassifier
3. If unsafe > 0.7 → Delete + warn

### Animated Stickers (.webp animated)
1. Download sticker
2. Extract frames (every 4th frame)
3. Scan each frame with NudeDetector
4. Track max score across all frames
5. If any frame > 0.7 → Delete + warn

### TGS Lottie Stickers
1. Download .tgs file
2. Convert to GIF using lottie library
3. Extract frames from GIF
4. Scan each frame
5. Cleanup temporary files

### Video Stickers (.webm)
1. Download video sticker
2. Extract frames every 5 frames (~1 second)
3. Scan each frame
4. Return highest confidence score

---

## 📈 Performance Comparison

| Feature | Old Bot | New Pyrogram Bot |
|---------|---------|------------------|
| Framework | python-telegram-bot | Pyrogram (async) |
| Processing | Synchronous | Async (Redis queue) |
| Scalability | Single instance | Multiple workers |
| Memory | Blocks on large files | Non-blocking |
| Speed | ~1-2 sec/image | Parallel processing |
| Queue | None | Redis (unlimited) |
| GPU Support | No | Yes (via workers) |

---

## 🛠️ Advanced Configuration

### 1. **Adjust NSFW Threshold**

Edit `config.py`:
```python
NSFW_THRESHOLD = 0.7  # Lower = stricter, Higher = more lenient
```

Recommended values:
- `0.5` - Very strict (may have false positives)
- `0.7` - Balanced (recommended)
- `0.85` - Lenient (fewer false positives)

---

### 2. **Frame Sampling Rate**

For faster processing (but lower accuracy):

```python
# In config.py
GIF_FRAME_SAMPLE = 6  # Extract every 6th frame (was 4)
FRAME_SAMPLE_RATE = 8  # Extract every 8th frame (was 5)
```

---

### 3. **File Size Limits**

Prevent large file processing:

```python
MAX_FILE_SIZE_MB = 30  # Reject files > 30MB
```

---

### 4. **Multiple Workers**

For high-traffic groups:

```bash
# Start 3 workers
for i in {1..3}; do
    python worker.py &
done
```

---

## 🔧 Redis Management

### Check Queue Status

```bash
redis-cli
> LLEN nsfw_detection_queue
(integer) 5  # 5 tasks waiting
```

### Clear Queue

```bash
redis-cli
> DEL nsfw_detection_queue
(integer) 1
```

### Monitor Queue Size

```bash
watch -n 1 'redis-cli LLEN nsfw_detection_queue'
```

---

## 🐛 Troubleshooting

### Issue 1: Redis Connection Error

**Error:** `redis.exceptions.ConnectionError: Error connecting to localhost:6379`

**Fix:**
```bash
# Check if Redis is running
systemctl status redis

# Start Redis
sudo systemctl start redis
```

---

### Issue 2: Bot Won't Start

**Error:** `pyrogram.errors.Unauthorized: Unauthorized`

**Fix:**
1. Delete `pyrogram_bot/nsfw-moderator.session`
2. Restart bot
3. Pyrogram will re-authenticate

---

### Issue 3: Workers Not Processing

**Symptom:** Queue growing but no processing

**Check:**
```bash
# Is worker running?
ps aux | grep worker.py

# Queue size?
redis-cli LLEN nsfw_detection_queue
```

**Fix:** Restart worker:
```bash
pkill -f worker.py
python worker.py
```

---

### Issue 4: Stickers Not Detected

**Possible causes:**
1. Feature not enabled via /settings
2. File size exceeds limit
3. Unsupported format

**Debug:**
Add logging to `bot.py`:
```python
@app.on_message(filters.sticker)
async def sticker_handler(client: Client, message: Message):
    print(f"🔍 Sticker received: {message.sticker.file_id}")
    # ... rest of code
```

---

## 📊 Monitoring

### Bot Logs

Watch bot activity:
```bash
tail -f logs/bot.log
```

### Worker Logs

Monitor processing:
```bash
tail -f logs/worker.log
```

### Redis Stats

```bash
redis-cli INFO stats
```

---

## 🎯 Migration from Old Bot

### What Changes:

1. ✅ **Framework:** Pyrogram instead of python-telegram-bot
2. ✅ **Architecture:** Async queue-based instead of synchronous
3. ✅ **Scalability:** Multiple workers supported
4. ✅ **Performance:** Non-blocking operations

### What Stays Same:

1. ✅ NSFW detection logic (NudeNet)
2. ✅ Frame extraction methods
3. ✅ Settings structure
4. ✅ Telegram API usage

### Migration Steps:

1. Stop old bot:
   ```bash
   sudo systemctl stop nsfw-bot
   ```

2. Deploy new bot:
   ```bash
   cd pyrogram_bot
   pip install -r requirements.txt
   ```

3. Copy `.env` values to `config.py`

4. Start Redis:
   ```bash
   sudo systemctl start redis
   ```

5. Start worker:
   ```bash
   python worker.py &
   ```

6. Start bot:
   ```bash
   python bot.py &
   ```

---

## 🚀 Production Deployment

### Systemd Service for Bot

Create `/etc/systemd/system/pyrogram-nsfw-bot.service`:

```ini
[Unit]
Description=Pyrogram NSFW Detection Bot
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nsfw-bot/pyrogram_bot
ExecStart=/opt/nsfw-bot/.venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Systemd Service for Worker

Create `/etc/systemd/system/pyrogram-nsfw-worker.service`:

```ini
[Unit]
Description=NSFW Detection Worker
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nsfw-bot/pyrogram_bot
ExecStart=/opt/nsfw-bot/.venv/bin/python worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Enable Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable pyrogram-nsfw-bot
sudo systemctl enable pyrogram-nsfw-worker
sudo systemctl start pyrogram-nsfw-bot
sudo systemctl start pyrogram-nsfw-worker
```

---

## ✅ Advantages Over Old Bot

| Aspect | Old Bot | New Pyrogram Bot |
|--------|---------|------------------|
| **Blocking** | Yes (blocks on large files) | No (async queue) |
| **Scalability** | Single process | Multiple workers |
| **Memory** | High (loads all in memory) | Low (streaming) |
| **Speed** | Sequential | Parallel |
| **Queue** | None | Redis (persistent) |
| **GPU** | No | Yes |
| **Recovery** | Manual restart | Auto-retry from queue |

---

## 🎉 Next Steps

1. **Test locally first:**
   ```bash
   python bot.py
   ```

2. **Enable Redis:**
   ```bash
   sudo systemctl start redis
   ```

3. **Start worker:**
   ```bash
   python worker.py
   ```

4. **Deploy to server:**
   ```bash
   scp -r pyrogram_bot root@140.245.240.202:/opt/nsfw-bot/
   ```

5. **Setup systemd services** (see above)

6. **Monitor performance:**
   - Watch queue size
   - Check worker CPU/GPU usage
   - Adjust frame sampling if needed

---

## 📚 Resources

- **Pyrogram Docs:** https://docs.pyrogram.org/
- **Redis Docs:** https://redis.io/documentation
- **RQ Docs:** https://python-rq.org/docs/
- **NudeNet:** https://github.com/notAI-tech/NudeNet

---

**Ready to deploy!** 🚀
