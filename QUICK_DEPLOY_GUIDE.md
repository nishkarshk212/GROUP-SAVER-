# 🚀 Quick Deployment Guide

## ✅ Easiest Method: Use the Deployment Script

### From Your Local Machine (Mac):

```bash
./deploy_simple.sh
```

That's it! The script will:
1. ✅ Commit your changes locally
2. ✅ Push to GitHub
3. ✅ SSH into server
4. ✅ Pull from GitHub on server
5. ✅ Restart the bot
6. ✅ Show you the status

---

## 📝 Manual Method (Step by Step)

### Step 1: On Your Local Machine (Mac)

```bash
cd /Users/nishkarshkr/Desktop/bot-app

# Make your code changes
# Edit files as needed...

# Commit and push
git add -A
git commit -m "Describe your changes"
git push origin main
```

### Step 2: SSH to Server and Deploy

```bash
# Connect to server
ssh -p 22 root@140.245.240.202
# Password: [your password]

# Navigate to bot directory
cd /opt/nsfw-bot

# Pull latest changes from GitHub
git fetch origin main
git reset --hard origin/main

# Restart the bot
systemctl restart pyrogram-nsfw-bot

# Check status
systemctl status pyrogram-nsfw-bot --no-pager -n 10

# Exit SSH when done
exit
```

---

## 🎯 What Was Confusing Before

Looking at your terminal, I see you tried to run commands like:

```bash
Made changes → Tested locally  # ❌ This is not a valid command
SSH to server                  # ❌ This is not a valid command
git pull origin main ←         # ❌ The arrow symbol caused issues
```

### Correct Commands:

```bash
# Actually make changes in your code editor
# Then test locally if needed

# To SSH to server:
ssh -p 22 root@140.245.240.202

# To pull from git (no special characters):
git pull origin main
```

---

## 📋 Current Server Status

Your bot is currently:
- ✅ **Running** (active since 17:52:21 UTC)
- ✅ **Location:** `/opt/nsfw-bot`
- ✅ **Service:** `pyrogram-nsfw-bot`
- ✅ **Git repo:** Initialized and working

---

## 🔧 Common Commands Reference

### Check Bot Status:
```bash
# On server
systemctl status pyrogram-nsfw-bot
```

### View Bot Logs:
```bash
# On server
journalctl -u pyrogram-nsfw-bot -f
```

### Restart Bot:
```bash
# On server
systemctl restart pyrogram-nsfw-bot
```

### Update from Git:
```bash
# On server
cd /opt/nsfw-bot
git pull origin main
systemctl restart pyrogram-nsfw-bot
```

### Test Bot on Telegram:
```
Send to bot: /start
Expected: Profile picture + welcome message

Send to bot: /settings
Expected: Interactive settings menu
```

---

## ⚡ One-Command Deployment

Just run this from your Mac:

```bash
./deploy_simple.sh
```

The script handles everything automatically!

---

## 🎯 Summary

**Before (Confusing):**
```bash
Made changes → Tested locally  # Not a command
SSH to server                  # Not a command  
git pull origin main ←         # Arrow causes error
```

**After (Correct):**
```bash
# 1. Make changes in code editor
# 2. Run deployment script:
./deploy_simple.sh

# OR manually:
git add && git commit && git push
ssh root@140.245.240.202 -p 22
cd /opt/nsfw-bot
git pull origin main
systemctl restart pyrogram-nsfw-bot
```

---

## ✅ Next Steps

1. **Use the script** for easy deployment:
   ```bash
   ./deploy_simple.sh
   ```

2. **Or follow the manual steps** above if you prefer control

3. **Test your bot** on Telegram after deployment:
   - Send `/start` → Should show profile picture
   - Send `/settings` → Should open settings menu

---

**Your bot is already running and deployed!** 🎉

Any future updates just require:
```bash
./deploy_simple.sh
```

Simple and reliable! ✨
