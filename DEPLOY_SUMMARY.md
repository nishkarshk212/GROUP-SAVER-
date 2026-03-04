# Server Deployment Summary

## 🚀 Quick Deploy to Your Server

### Server Details
- **IP**: 140.245.240.202
- **Username**: root
- **Password**: Akshay343402355468
- **Port**: 22

---

## 📋 Step-by-Step Instructions

### Option A: Automated Deployment (Easiest)

1. **Connect to your server:**
   ```bash
   ssh root@140.245.240.202 -p 22
   # Enter password when prompted: Akshay343402355468
   ```

2. **Update system packages:**
   ```bash
   apt update && apt upgrade -y
   ```

3. **Install Git:**
   ```bash
   apt install -y git
   ```

4. **Clone your repository:**
   ```bash
   cd /opt
   git clone <YOUR_GIT_REPO_URL> nsfw-bot
   cd nsfw-bot
   ```

5. **Run the automated deployment script:**
   ```bash
   chmod +x scripts/deploy_to_server.sh
   ./scripts/deploy_to_server.sh
   ```

6. **Configure your bot token:**
   ```bash
   nano .env
   ```
   Replace `your_bot_token_here` with your actual bot token from @BotFather
   - Press Ctrl+X to exit
   - Press Y to save
   - Press Enter to confirm

7. **Restart the bot:**
   ```bash
   systemctl restart nsfw-bot
   ```

8. **Verify it's running:**
   ```bash
   systemctl status nsfw-bot
   ```

---

### Option B: Manual Deployment

If you prefer full control, follow these manual steps:

1. **SSH into server:**
   ```bash
   ssh root@140.245.240.202 -p 22
   ```

2. **Install dependencies:**
   ```bash
   apt update
   apt install -y python3 python3-pip python3-venv git libgl1 libglib2.0-0
   ```

3. **Clone repository:**
   ```bash
   cd /opt
   mkdir -p nsfw-bot
   cd nsfw-bot
   git clone <YOUR_GIT_REPO_URL> .
   ```

4. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Create .env file:**
   ```bash
   cat > .env << EOF
   TELEGRAM_BOT_TOKEN=your_actual_bot_token
   LOG_CHANNEL_ID=your_log_channel_id
   PFP_NSFWD_ENABLED=1
   NSFW_WORD_LANGS=en,ru,zh,es,fr,de,ja,ko,ar,hi,it,pt,pl,cs,nl,sv,tr,th,fa,fil
   EOF
   ```

6. **Install systemd service:**
   ```bash
   cp systemd/nsfw-bot.service /etc/systemd/system/nsfw-bot.service
   ```

7. **Enable and start service:**
   ```bash
   systemctl daemon-reload
   systemctl enable nsfw-bot
   systemctl start nsfw-bot
   ```

8. **Check status:**
   ```bash
   systemctl status nsfw-bot
   ```

---

## 🔧 Useful Commands

### Monitor Logs (Real-time)
```bash
journalctl -u nsfw-bot -f
```

### View Last 50 Log Lines
```bash
journalctl -u nsfw-bot -n 50
```

### Restart Bot
```bash
systemctl restart nsfw-bot
```

### Stop Bot
```bash
systemctl stop nsfw-bot
```

### Start Bot
```bash
systemctl start nsfw-bot
```

### Check if Running
```bash
systemctl is-active nsfw-bot
```

### Check Service Status
```bash
systemctl status nsfw-bot
```

---

## 🔄 Updating the Bot

When you push new code to your Git repository:

```bash
cd /opt/nsfw-bot
git pull origin main
systemctl restart nsfw-bot
```

---

## 🛡️ Security Recommendations

### 1. Set Up SSH Keys (Recommended)
On your local machine:
```bash
ssh-keygen -t ed25519
ssh-copy-id root@140.245.240.202 -p 22
```

Test connection:
```bash
ssh root@140.245.240.202 -p 22
```

### 2. Configure Firewall
```bash
apt install -y ufw
ufw allow 22/tcp
ufw enable
ufw status
```

### 3. Regular System Updates
```bash
apt update && apt upgrade -y
```

### 4. Monitor Resources
```bash
apt install -y htop
htop
```

---

## 📊 Files Created for Deployment

1. **DEPLOYMENT.md** - Comprehensive deployment guide
2. **QUICK_START.md** - Quick reference guide
3. **scripts/deploy_to_server.sh** - Automated deployment script
4. **systemd/nsfw-bot.service** - Systemd service configuration
5. **.gitignore** - Git ignore rules (prevents committing sensitive files)

---

## ✅ Post-Deployment Checklist

- [ ] Bot token added to `.env` file
- [ ] Service restarted: `systemctl restart nsfw-bot`
- [ ] Bot responding in Telegram
- [ ] Logs checked: `journalctl -u nsfw-bot -f`
- [ ] Log channel configured (optional)
- [ ] SSH keys set up (recommended)
- [ ] Firewall configured (recommended)

---

## 🐛 Troubleshooting

### Bot Won't Start
1. Check logs: `journalctl -u nsfw-bot -n 100`
2. Verify bot token in `.env`
3. Reinstall dependencies:
   ```bash
   cd /opt/nsfw-bot
   source .venv/bin/activate
   pip install -r requirements.txt
   systemctl restart nsfw-bot
   ```

### High Memory Usage
Edit `/opt/nsfw-bot/.env`:
```
PFP_NSFWD_ENABLED=0
```
Then restart: `systemctl restart nsfw-bot`

### Service Not Starting
Reload systemd configuration:
```bash
systemctl daemon-reload
systemctl restart nsfw-bot
```

### Connection Issues
Verify network connectivity:
```bash
ping google.com
curl https://api.telegram.org
```

---

## 📞 Support

For detailed documentation, see:
- **README.md** - General bot information
- **DEPLOYMENT.md** - Detailed deployment instructions
- **SETUP_LOG_CHANNEL.md** - Log channel configuration
- **QUICK_START.md** - Quick start guide

---

## 🎯 Next Steps After Deployment

1. Test the bot by adding it to a Telegram group
2. Make it an admin in your group
3. Configure log channel (see SETUP_LOG_CHANNEL.md)
4. Monitor performance with `htop` or `journalctl`
5. Set up automatic updates or定期 pull from Git

---

**Deployment Date**: $(date +%Y-%m-%d)  
**Server**: 140.245.240.202:22  
**Service Name**: nsfw-bot  
**Installation Directory**: /opt/nsfw-bot