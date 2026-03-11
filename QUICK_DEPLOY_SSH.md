# ⚡ Quick Deploy - SSH Passphrase Guide

## 🚀 One-Command Deployment

After SSH key is setup, simply run:

```bash
./deploy_auto.sh
```

That's it! The script will:
1. ✅ Commit your changes
2. ✅ Push to Git
3. ✅ Deploy to server
4. ✅ Restart the bot
5. ✅ Show you the logs

**You'll only need to enter:** Your SSH key passphrase (if set)

---

## 🔐 First Time Setup (5 minutes)

### Option 1: Automated Setup

```bash
./setup_ssh_key.sh
```

Follow the prompts - it guides you through everything!

### Option 2: Manual Setup

```bash
# 1. Generate key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. Show public key
cat ~/.ssh/id_ed25519.pub

# 3. Copy the output

# 4. SSH to server
ssh root@140.245.240.202 -p 22

# 5. On server, paste your key
mkdir -p ~/.ssh
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
exit

# 6. Test
ssh root@140.245.240.202 -p 22
# Should connect without password!
```

---

## 📋 Server Details

| Parameter | Value |
|-----------|-------|
| **IP Address** | `140.245.240.202` |
| **SSH Port** | `22` |
| **User** | `root` |
| **Bot Directory** | `/opt/nsfw-bot` |
| **Service Name** | `nsfw-bot` |

---

## 🎯 Common Scenarios

### Scenario 1: Made changes to bot.py

```bash
# Just run deploy script
./deploy_auto.sh
```

### Scenario 2: Want to check if bot is running

```bash
ssh root@140.245.240.202 -p 22 'systemctl status nsfw-bot'
```

### Scenario 3: View live logs

```bash
ssh root@140.245.240.202 -p 22 'journalctl -u nsfw-bot -f'
```

### Scenario 4: Restart bot remotely

```bash
ssh root@140.245.240.202 -p 22 'systemctl restart nsfw-bot'
```

---

## 🔑 SSH Key Management

### Add key to SSH agent (avoid retyping passphrase)

**macOS:**
```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

**Linux:**
```bash
ssh-add ~/.ssh/id_ed25519
```

### Change SSH key passphrase

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
```

### Backup your private key

```bash
cp ~/.ssh/id_ed25519 ~/backup/id_ed25519.backup
# Store in secure location!
```

---

## 🐛 Troubleshooting

### "Permission denied (publickey)"

```bash
# Start SSH agent
eval "$(ssh-agent -s)"

# Add your key
ssh-add ~/.ssh/id_ed25519

# Try again
ssh root@140.245.240.202 -p 22
```

### "Connection refused"

Check if server is reachable:
```bash
ping 140.245.240.202
```

If no response, server might be down or firewall blocking.

### "Git pull failed on server"

SSH to server and fix manually:
```bash
ssh root@140.245.240.202 -p 22
cd /opt/nsfw-bot
git status
git fetch --all
git reset --hard origin/main
systemctl restart nsfw-bot
```

### Bot not responding after deploy

Check logs:
```bash
ssh root@140.245.240.202 -p 22 'journalctl -u nsfw-bot -f'
```

Common issues:
- Missing `.env` file → Check bot token
- Python dependency error → `pip install -r requirements.txt`
- Port already in use → Check if another bot running

---

## 📊 Deployment Checklist

Before deploying:
- [ ] Changes tested locally
- [ ] Git configured
- [ ] SSH key setup
- [ ] Server accessible

After deploying:
- [ ] Logs show "Starting bot..."
- [ ] No error messages
- [ ] Bot responds to `/start` on Telegram
- [ ] Sticker scanning works (if enabled)

---

## 🎨 Pro Tips

### 1. Create alias for quick access

Add to `~/.zshrc`:
```bash
alias bot-deploy='cd /Users/nishkarshkr/Desktop/bot-app && ./deploy_auto.sh'
alias bot-status='ssh root@140.245.240.202 -p 22 "systemctl status nsfw-bot"'
alias bot-logs='ssh root@140.245.240.202 -p 22 "journalctl -u nsfw-bot -f"'
```

Then just run:
```bash
bot-deploy
bot-status
bot-logs
```

### 2. Watch multiple log windows

Terminal 1 (local):
```bash
./deploy_auto.sh
```

Terminal 2 (server logs):
```bash
ssh root@140.245.240.202 -p 22 'journalctl -u nsfw-bot -f'
```

### 3. Auto-restart on failure

Already configured with systemd! Service auto-restarts on crash.

---

## 🆘 Emergency Commands

### Stop bot immediately

```bash
ssh root@140.245.240.202 -p 22 'systemctl stop nsfw-bot'
```

### Rollback to previous version

```bash
ssh root@140.245.240.202 -p 22
cd /opt/nsfw-bot
git log --oneline -5  # Find last good commit
git reset --hard <commit-hash>
systemctl restart nsfw-bot
```

### Check disk space

```bash
ssh root@140.245.240.202 -p 22 'df -h'
```

### Check memory usage

```bash
ssh root@140.245.240.202 -p 22 'free -h'
```

### Check what's using CPU

```bash
ssh root@140.245.240.202 -p 22 'top'
```

---

## 📞 Quick Support

**Developer:** @Jayden_212  
**Updates:** @Tele_212_bots

**Full Documentation:**
- `DEPLOYMENT_GIT_SSH.md` - Complete guide
- `DEPLOYMENT_GUIDE.md` - Server setup
- `QUICK_START.md` - Bot features

---

## ✅ Success Indicators

Your deployment is successful when you see:

```
✅ Code pushed to Git repository
✅ Code updated from Git
✅ Dependencies updated
✅ Bot token verified
✅ Service is RUNNING
```

And in the logs:
```
Loaded NSFW detection: XXX words from XX languages
✅ Bot is starting...
```

---

**Deploy time**: ~30-60 seconds  
**Downtime**: ~5-10 seconds during restart

🎉 Happy deploying!
