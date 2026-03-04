# 🚀 Deploy Bot to Your Server - Complete Guide

## ✅ What's Been Done

I've prepared everything you need to deploy the bot to your server at **140.245.240.202**:

### Files Added to Your Git Repository:
- ✅ `DEPLOYMENT.md` - Comprehensive deployment guide
- ✅ `QUICK_START.md` - Quick reference guide  
- ✅ `DEPLOY_SUMMARY.md` - Complete summary with commands
- ✅ `scripts/deploy_to_server.sh` - Automated deployment script
- ✅ `systemd/nsfw-bot.service` - Systemd service configuration
- ✅ `.gitignore` - Prevents committing sensitive files

**All changes committed and pushed to your Git repository!**

---

## 📋 Step-by-Step Deployment Instructions

### Step 1: Connect to Your Server

Open a terminal on your local machine and run:

```bash
ssh root@140.245.240.202 -p 22
```

When prompted, enter the password:
```
Akshay343402355468
```

### Step 2: Update System Packages

Once logged in to your server:

```bash
apt update && apt upgrade -y
```

This may take a few minutes. Wait for it to complete.

### Step 3: Install Git

```bash
apt install -y git
```

### Step 4: Clone Your Repository

```bash
cd /opt
git clone https://github.com/nishkarshk212/GROUP-SAVER-.git nsfw-bot
cd nsfw-bot
```

### Step 5: Run the Automated Deployment Script

```bash
chmod +x scripts/deploy_to_server.sh
./scripts/deploy_to_server.sh
```

The script will automatically:
1. Install Python and all required dependencies
2. Set up a virtual environment
3. Install bot dependencies from requirements.txt
4. Create the systemd service
5. Enable and start the bot service

### Step 6: Configure Your Bot Token

After the script completes, edit the `.env` file:

```bash
nano .env
```

Find this line:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

Replace `your_bot_token_here` with your actual bot token from @BotFather.

Your token should look like: `8587720230:AAEHakInRNby8me1WtxsoQ_JUbhTJAVJL6s`

**Save and exit:**
- Press `Ctrl + X`
- Press `Y` to confirm save
- Press `Enter`

### Step 7: Restart the Bot

```bash
systemctl restart nsfw-bot
```

### Step 8: Verify the Bot is Running

Check the status:

```bash
systemctl status nsfw-bot
```

You should see "active (running)" in green.

View real-time logs:

```bash
journalctl -u nsfw-bot -f
```

Press `Ctrl + C` to exit the log view.

### Step 9: Test the Bot

1. Open Telegram
2. Find your bot using the token you configured
3. Send `/start` command
4. The bot should respond!

---

## 🔧 Useful Commands After Deployment

### View Logs (Real-time)
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

### Check Status
```bash
systemctl status nsfw-bot
```

### Check if Running
```bash
systemctl is-active nsfw-bot
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

### 1. Set Up SSH Keys (Highly Recommended)

On your **local machine** (not the server):

```bash
ssh-keygen -t ed25519
# Press Enter to accept default location
# Optionally set a passphrase for extra security
```

Copy the key to your server:

```bash
ssh-copy-id root@140.245.240.202 -p 22
# Enter password: Akshay343402355468
```

Test it:

```bash
ssh root@140.245.240.202 -p 22
# Should connect without asking for password
```

### 2. Configure Firewall

On your server:

```bash
apt install -y ufw
ufw allow 22/tcp
ufw enable
ufw status
```

### 3. Regular Updates

Keep your server updated:

```bash
apt update && apt upgrade -y
```

---

## 🐛 Troubleshooting

### Bot Won't Start

1. Check the logs:
   ```bash
   journalctl -u nsfw-bot -n 100
   ```

2. Common issues:
   - Invalid bot token: Check `.env` file
   - Missing dependencies: Run `pip install -r requirements.txt`
   - Port conflict: Make sure only one instance is running

### High Memory Usage

Edit the `.env` file:

```bash
nano /opt/nsfw-bot/.env
```

Set:
```
PFP_NSFWD_ENABLED=0
```

Then restart:
```bash
systemctl restart nsfw-bot
```

### Service Issues

Reload systemd configuration:

```bash
systemctl daemon-reload
systemctl restart nsfw-bot
```

---

## 📊 Installation Details

- **Installation Directory**: `/opt/nsfw-bot`
- **Service Name**: `nsfw-bot`
- **Python Version**: 3.x (installed via apt)
- **Virtual Environment**: `/opt/nsfw-bot/.venv`
- **Logs Location**: `/var/log/journal/` (view with journalctl)

---

## ✅ Post-Deployment Checklist

- [ ] Connected to server via SSH
- [ ] Updated system packages
- [ ] Cloned Git repository
- [ ] Ran deployment script successfully
- [ ] Added bot token to `.env` file
- [ ] Restarted the bot service
- [ ] Verified bot is running (`systemctl status nsfw-bot`)
- [ ] Tested bot in Telegram (sent `/start`)
- [ ] Checked logs (`journalctl -u nsfw-bot -f`)
- [ ] Set up SSH keys (recommended)
- [ ] Configured firewall (recommended)

---

## 📞 Additional Resources

Documentation files in your repository:

- **README.md** - General bot information and features
- **DEPLOYMENT.md** - Detailed deployment guide with all options
- **QUICK_START.md** - Quick reference with common commands
- **DEPLOY_SUMMARY.md** - Complete summary with troubleshooting
- **SETUP_LOG_CHANNEL.md** - How to set up log channel notifications

---

## 🎯 What's Next?

After successful deployment:

1. ✅ Test the bot by adding it to a Telegram group
2. ✅ Make it an admin in your group for full functionality
3. ✅ Configure the log channel for join/leave notifications
4. ✅ Monitor performance regularly
5. ✅ Keep the bot updated by pulling from Git

---

## 📝 Server Information Summary

| Item | Value |
|------|-------|
| **IP Address** | 140.245.240.202 |
| **Username** | root |
| **Password** | Akshay343402355468 |
| **Port** | 22 |
| **Installation Path** | /opt/nsfw-bot |
| **Service Name** | nsfw-bot |
| **Git Repository** | https://github.com/nishkarshk212/GROUP-SAVER-.git |

---

## 🎉 Success Indicators

You'll know the deployment was successful when:

- ✅ `systemctl status nsfw-bot` shows "active (running)"
- ✅ Bot responds to `/start` command in Telegram
- ✅ No errors in `journalctl -u nsfw-bot -f`
- ✅ Bot can join groups and detect NSFW content

---

**Good luck with your deployment! 🚀**

If you encounter any issues, check the logs first:
```bash
journalctl -u nsfw-bot -n 100 --no-pager
```

Most issues are related to:
- Incorrect bot token in `.env`
- Missing Python dependencies
- Network connectivity issues