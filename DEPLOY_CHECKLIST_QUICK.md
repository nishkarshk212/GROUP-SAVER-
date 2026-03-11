# ✅ Pyrogram Bot Deployment Checklist

## Quick Reference - Copy & Paste Commands

---

### 🔹 Step 1: SSH to Server
```bash
ssh root@140.245.240.202 -p 22
# Password: Akshay343402355468
```

---

### 🔹 Step 2: Install Redis (5 minutes)
```bash
apt update && apt install redis-server -y
systemctl start redis
systemctl enable redis
redis-cli ping  # Should return: PONG
```

---

### 🔹 Step 3: Stop Old Bot (CRITICAL - 2 minutes)
```bash
systemctl stop nsfw-bot
systemctl disable nsfw-bot
pkill -9 -f "python.*bot"
sleep 10
ps aux | grep "python.*bot" | grep -v grep  # Should show ZERO
```

---

### 🔹 Step 4: Copy Files (From LOCAL machine, not SSH)
```bash
# Run this on YOUR Mac (not in SSH session)
cd /Users/nishkarshkr/Desktop/bot-app
scp -P 22 -r pyrogram_bot/* root@140.245.240.202:/opt/nsfw-bot/
# Type 'yes' when asked, then password: Akshay343402355468
```

---

### 🔹 Step 5: Configure Bot (On Server)
```bash
cd /opt/nsfw-bot
nano config.py
```

**Edit these 3 values:**
```python
API_ID = 123456  # From my.telegram.org
API_HASH = "your_hash_here"  # From my.telegram.org  
BOT_TOKEN = "your_token_here"  # From @BotFather
```

Save: `Ctrl+X` → `Y` → `Enter`

---

### 🔹 Step 6: Install Dependencies (3 minutes)
```bash
cd /opt/nsfw-bot
source .venv/bin/activate
pip install --upgrade pip
pip install pyrogram tgcrypto redis rq opencv-python lottie deepface imagehash --no-cache-dir
```

---

### 🔹 Step 7: Create Directories
```bash
mkdir -p temp logs
chmod 777 temp
```

---

### 🔹 Step 8: Setup Systemd Services
```bash
# Bot service
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

# Worker service
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

### 🔹 Step 9: Start Services
```bash
systemctl daemon-reload
systemctl enable pyrogram-nsfw-bot pyrogram-nsfw-worker
systemctl start pyrogram-nsfw-bot
systemctl start pyrogram-nsfw-worker
sleep 5
```

---

### 🔹 Step 10: Verify Everything
```bash
# Check services
systemctl status pyrogram-nsfw-bot --no-pager -n 5
systemctl status pyrogram-nsfw-worker --no-pager -n 5
systemctl status redis --no-pager -n 5

# Check processes
ps aux | grep bot.py | grep -v grep  # Should show 1
ps aux | grep worker.py | grep -v grep  # Should show 1

# Check for conflicts
journalctl -u pyrogram-nsfw-bot --since "2 minutes ago" | grep -i conflict
# Should return NOTHING
```

---

### 🔹 Step 11: Test Bot on Telegram
1. Open Telegram
2. Find your bot
3. Send `/start`
4. Expected: Welcome message
5. Send `/settings`
6. Expected: Interactive menu with buttons

---

### 🔹 Step 12: Enable Sticker Scan
1. Send `/settings` to bot
2. Click "🏷️ Stickers" until ✅
3. Send animated sticker
4. Bot should scan and respond

---

## 🎯 Quick Verification Commands

```bash
# All-in-one status check
echo "=== Redis Status ===" && systemctl is-active redis && \
echo "=== Bot Status ===" && systemctl is-active pyrogram-nsfw-bot && \
echo "=== Worker Status ===" && systemctl is-active pyrogram-nsfw-worker && \
echo "=== Process Count ===" && ps aux | grep "python.*bot" | grep -v grep | wc -l && \
echo "=== Conflicts ===" && journalctl -u pyrogram-nsfw-bot --since "5 minutes ago" | grep -i conflict | wc -l
```

Expected output:
```
=== Redis Status ===
active
=== Bot Status ===
active
=== Worker Status ===
active
=== Process Count ===
1
=== Conflicts ===
0
```

---

## 🐛 Emergency Fixes

### If Bot Not Starting:
```bash
# Kill all bots
pkill -9 -f "python.*bot"
sleep 5

# Clear cache
cd /opt/nsfw-bot && rm -rf __pycache__

# Restart
systemctl start pyrogram-nsfw-bot
```

### If Redis Issues:
```bash
systemctl restart redis
redis-cli ping
```

### If Workers Stuck:
```bash
systemctl restart pyrogram-nsfw-worker
```

---

## 📊 Monitoring

```bash
# Real-time logs
journalctl -u pyrogram-nsfw-bot -f

# Queue size
redis-cli LLEN nsfw_detection_queue

# Watch queue
watch -n 1 'redis-cli LLEN nsfw_detection_queue'
```

---

## ⏱️ Estimated Time

| Step | Time |
|------|------|
| SSH + Redis install | 5 min |
| Stop old bot | 2 min |
| Copy files | 3 min |
| Configure | 5 min |
| Install dependencies | 3 min |
| Setup systemd | 2 min |
| Start + verify | 3 min |
| **TOTAL** | **~23 minutes** |

---

## ✅ Success Criteria

- [ ] Redis running (`redis-cli ping` returns PONG)
- [ ] Bot service active (no conflict errors)
- [ ] Worker service active
- [ ] Only 1 bot instance running
- [ ] Only 1 worker instance running
- [ ] Bot responds to `/start`
- [ ] Bot responds to `/settings`
- [ ] Interactive menu shows toggle buttons
- [ ] No errors in recent logs

---

## 📞 Need Help?

Check detailed guide: `MANUAL_DEPLOYMENT_PYROGRAM.md`

Or run diagnostic:
```bash
cd /opt/nsfw-bot
python -c "import config; print('Config OK')"
python -c "from detector import NSFWDetector; print('Detector OK')"
python -c "from frames import extract_gif_frames; print('Frames OK')"
```

---

**🚀 You're ready to deploy!** Follow the checklist step by step.
