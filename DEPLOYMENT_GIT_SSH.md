# 🚀 Deployment Guide - Git & SSH Setup

## Overview

This guide shows you how to setup automated deployment of your Telegram bot to your server using Git and SSH with passphrase-protected keys.

---

## 📋 Prerequisites

- ✅ Server IP: `140.245.240.202`
- ✅ SSH Port: `22`
- ✅ SSH User: `root`
- ✅ Bot directory on server: `/opt/nsfw-bot`
- ✅ Git repository configured

---

## 🔐 Method 1: Automated SSH Key Setup (Recommended)

### Step 1: Run SSH Key Setup Script

```bash
cd /Users/nishkarshkr/Desktop/bot-app
./setup_ssh_key.sh
```

**What it does:**
- Checks for existing SSH keys
- Generates new key if needed
- Displays your public key
- Optionally copies it to server automatically

### Step 2: Follow On-Screen Instructions

The script will guide you through:
1. Copying your public key
2. Setting up `authorized_keys` on server
3. Testing the connection

### Step 3: Test Passwordless SSH

```bash
ssh root@140.245.240.202 -p 22
```

If you connect without password, you're ready! ✅

---

## 🔐 Method 2: Manual SSH Key Setup

### Step 1: Generate SSH Key (if you don't have one)

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

- Press Enter to accept default location (`~/.ssh/id_ed25519`)
- Enter a passphrase (recommended) or press Enter for no passphrase

### Step 2: Display Your Public Key

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the entire output (starts with `ssh-ed25519` or `ssh-rsa`)

### Step 3: SSH into Server Manually

```bash
ssh root@140.245.240.202 -p 22
```

Enter your server password when prompted.

### Step 4: Setup Authorized Keys on Server

On the server, run:

```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
```

Paste your public key (from Step 2) into the file.

Save and exit:
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

### Step 5: Set Correct Permissions

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
exit
```

### Step 6: Test Connection

```bash
ssh root@140.245.240.202 -p 22
```

If you connect without password, success! ✅

---

## 🚀 Automated Deployment

### Option A: Full Auto-Deploy (Recommended)

Once SSH key is setup, deploy with one command:

```bash
cd /Users/nishkarshkr/Desktop/bot-app
./deploy_auto.sh
```

**What it does:**
1. ✅ Commits your local changes to Git
2. ✅ Pushes to GitHub
3. ✅ SSH into server
4. ✅ Pull latest code from Git
5. ✅ Update Python dependencies
6. ✅ Restart bot service
7. ✅ Verify deployment
8. ✅ Show logs

**You'll be prompted for:**
- SSH key passphrase (if you set one)
- That's it!

### Option B: Manual Deployment Steps

If you prefer manual control:

#### 1. Commit and Push to Git

```bash
cd /Users/nishkarshkr/Desktop/bot-app
git add -A
git commit -m "Your commit message here"
git push origin main
```

#### 2. SSH into Server

```bash
ssh root@140.245.240.202 -p 22
```

#### 3. Deploy on Server

```bash
cd /opt/nsfw-bot
git pull origin main
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
systemctl daemon-reload
systemctl restart nsfw-bot
journalctl -u nsfw-bot -n 30 --no-pager
```

---

## 🔧 Troubleshooting

### SSH Key Issues

#### Problem: "Permission denied (publickey)"

**Solution:**
```bash
# Check if SSH agent is running
eval "$(ssh-agent -s)"

# Add your key to agent
ssh-add ~/.ssh/id_ed25519

# Test again
ssh root@140.245.240.202 -p 22
```

#### Problem: "Passphrase prompt every time"

**Solution:** Add key to SSH agent permanently

On macOS:
```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

On Linux:
```bash
ssh-add ~/.ssh/id_ed25519
# Add to ~/.bashrc or ~/.zshrc to persist
```

### Deployment Issues

#### Problem: "Git pull failed"

**Solution:**
```bash
# On server, navigate to bot directory
cd /opt/nsfw-bot

# Check git status
git status

# Force reset if needed (careful!)
git fetch --all
git reset --hard origin/main
```

#### Problem: "Service failed to start"

**Solution:**
```bash
# Check service status
systemctl status nsfw-bot

# View detailed logs
journalctl -u nsfw-bot -f

# Check .env configuration
cat /opt/nsfw-bot/.env

# Verify bot token exists
grep TELEGRAM_BOT_TOKEN /opt/nsfw-bot/.env
```

#### Problem: "Python dependencies error"

**Solution:**
```bash
cd /opt/nsfw-bot
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

## 📊 Deployment Verification

### Quick Status Check

From your local machine:
```bash
ssh root@140.245.240.202 -p 22 'systemctl is-active nsfw-bot && echo "✅ RUNNING" || echo "❌ NOT RUNNING"'
```

### View Live Logs

```bash
ssh root@140.245.240.202 -p 22 'journalctl -u nsfw-bot -f'
```

### Check Bot Response

Send `/start` to your bot on Telegram - it should respond immediately.

---

## 🔒 Security Best Practices

### 1. Use SSH Key Passphrase

Always protect your private key with a passphrase:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Enter strong passphrase when prompted
```

### 2. Add Key to SSH Agent

Avoid entering passphrase repeatedly:
```bash
# macOS
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# Linux
ssh-add ~/.ssh/id_ed25519
```

### 3. Restrict SSH Key Access (Optional)

Edit `~/.ssh/authorized_keys` on server and add options:
```
from="YOUR_LOCAL_IP",command="/bin/bash" ssh-ed25519 AAAA...
```

### 4. Regular Updates

Keep your bot updated:
```bash
./deploy_auto.sh
```

---

## 📝 Quick Reference Commands

### Local Commands (on your Mac)

```bash
# Deploy to server
./deploy_auto.sh

# Check server status
ssh root@140.245.240.202 -p 22 'systemctl status nsfw-bot'

# View server logs
ssh root@140.245.240.202 -p 22 'journalctl -u nsfw-bot -f'

# Restart bot remotely
ssh root@140.245.240.202 -p 22 'systemctl restart nsfw-bot'
```

### Server Commands (after SSH)

```bash
cd /opt/nsfw-bot

# Check status
systemctl status nsfw-bot

# View logs
journalctl -u nsfw-bot -f

# Restart
systemctl restart nsfw-bot

# Stop
systemctl stop nsfw-bot

# Start
systemctl start nsfw-bot

# Update from Git
git pull origin main

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt --no-cache-dir
```

---

## 🎯 Deployment Workflow

Here's the recommended workflow:

1. **Develop locally**
   - Make changes to `bot.py`
   - Test with `python bot.py`

2. **Commit changes**
   ```bash
   git add -A
   git commit -m "Description of changes"
   ```

3. **Deploy to server**
   ```bash
   ./deploy_auto.sh
   # Enter SSH passphrase if prompted
   # Wait for deployment to complete
   ```

4. **Verify**
   - Check logs in terminal
   - Test bot on Telegram

5. **Monitor**
   - Watch for errors in logs
   - Check bot functionality

---

## 🆘 Emergency Rollback

If deployment fails and you need to rollback:

### On Server:

```bash
cd /opt/nsfw-bot

# Find last good commit
git log --oneline -10

# Reset to that commit
git reset --hard <commit-hash>

# Restart bot
systemctl restart nsfw-bot
```

---

## 📞 Support

**Issues or Questions:**
- Developer: @Jayden_212
- Updates: @Tele_212_bots

**Documentation Files:**
- Deployment: `DEPLOYMENT_GUIDE.md`
- Sticker Scan: `STICKER_SCAN_FEATURE.md`
- Quick Start: `QUICK_START.md`

---

## ✅ Checklist for First Deployment

- [ ] SSH key generated
- [ ] Public key copied to server
- [ ] Passwordless SSH working
- [ ] Git repository configured
- [ ] `.env` file on server has correct bot token
- [ ] Bot has admin rights in Telegram group
- [ ] Deployment scripts are executable (`chmod +x`)
- [ ] Server firewall allows SSH (port 22)

---

**Last Updated**: March 2026  
**Version**: 1.0.0
