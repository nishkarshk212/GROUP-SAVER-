# Server Deployment Guide - NSFW Bot

## ✅ Changes Committed & Pushed
All bug fixes have been successfully committed and pushed to GitHub:
- Commit: `4b1e28a` - "Fix NSFW detection bugs and improve error handling"
- Repository: https://github.com/nishkarshk212/GROUP-SAVER-.git

---

## 📋 Manual Deployment Instructions

### Option 1: Direct SSH Deployment (Recommended)

1. **Connect to your server:**
   ```bash
   ssh root@140.245.240.202 -p 22
   ```

2. **Navigate to bot directory and pull latest changes:**
   ```bash
   cd /opt/nsfw-bot
   git pull origin main
   ```

3. **Activate virtual environment and update dependencies:**
   ```bash
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt --no-cache-dir
   ```

4. **Restart the bot service:**
   ```bash
   systemctl daemon-reload
   systemctl restart nsfw-bot
   ```

5. **Verify the deployment:**
   ```bash
   # Check service status
   systemctl status nsfw-bot
   
   # View recent logs
   journalctl -u nsfw-bot -n 20 --no-pager
   
   # Follow live logs
   journalctl -u nsfw-bot -f
   ```

6. **Expected output in logs:**
   ```
   ✅ Loaded NSFW detection: XXX words, XXX phrases from XX/XX languages
   ```
   (You should see successful word loading with counts)

---

### Option 2: One-Line Remote Command

If you have SSH key-based access configured:

```bash
ssh root@140.245.240.202 -p 22 "cd /opt/nsfw-bot && git pull origin main && source .venv/bin/activate && pip install -r requirements.txt && systemctl restart nsfw-bot && journalctl -u nsfw-bot -n 10"
```

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Git repository updated: `git log -1` shows latest commit
- [ ] Dependencies installed: `pip list | grep -E "python-telegram-bot|nudenet"`
- [ ] Service running: `systemctl is-active nsfw-bot` returns "active"
- [ ] Logs show successful word loading (not "WARNING: No NSFW words loaded")
- [ ] No Python errors in startup logs
- [ ] Bot responds to `/start` command in Telegram

---

## 🐛 Troubleshooting

### If bot fails to start:

1. **Check logs for errors:**
   ```bash
   journalctl -u nsfw-bot -n 50 --no-pager
   ```

2. **Common issues:**

   **"No NSFW words loaded" warning:**
   - Check network connectivity on server
   - Verify language files exist: `ls -la /opt/nsfw-bot/data/naughty-words/`
   - Try manual fetch: `curl https://cdn.jsdelivr.net/npm/naughty-words/en.json`

   **"TELEGRAM_BOT_TOKEN not found":**
   - Check .env file: `cat /opt/nsfw-bot/.env`
   - Ensure token is set correctly
   - Restart service after fixing .env

   **Service won't start:**
   - Check Python path: `which python3`
   - Verify virtual environment: `ls -la /opt/nsfw-bot/.venv/bin/python`
   - Reinstall dependencies: `source .venv/bin/activate && pip install -r requirements.txt`

3. **Manual test run:**
   ```bash
   cd /opt/nsfw-bot
   source .venv/bin/activate
   python bot.py
   ```
   (This will show immediate errors in foreground)

---

## 📊 What Was Fixed

### Critical Bugs Fixed:
1. **False Loading Status** - `_bad_loaded` now only True when words actually loaded
2. **Missing Error Logging** - Added comprehensive error messages for debugging
3. **Regex Pattern Issues** - Now detects obfuscated profanity like `f**k`, `s**t`
4. **Security Issue** - Added environment variable validation for credentials

### Test Results:
✅ Clean messages: Correctly identified as safe  
✅ Basic NSFW words: All detected (porn, fuck, shit, ass, bitch, dick, nude, sex)  
✅ Obfuscated versions: All detected (p0rn, s3x, f**k, s**t, b*tch, p*rn, pr0n)  
✅ Unicode fonts: All detected (𝐟𝐮𝐜𝐤, 𝑝𝑜𝑟𝑛, 𝓯𝓾𝓬𝓴)  

---

## 🚀 Quick Status Commands

```bash
# Check if bot is running
systemctl status nsfw-bot

# View live logs
journalctl -u nsfw-bot -f

# Restart bot
systemctl restart nsfw-bot

# Check cleanup timer
systemctl list-timers | grep nsfw-bot

# View loaded words count
journalctl -u nsfw-bot | grep "Loaded NSFW detection"
```

---

## 📞 Support

If you encounter any issues during deployment:
1. Check the troubleshooting section above
2. Review full logs: `journalctl -u nsfw-bot --since today`
3. Verify .env configuration matches your setup
4. Ensure server has internet access to download word lists

---

**Last Updated:** $(date)  
**Commit:** 4b1e28a  
**Server:** 140.245.240.202:22
