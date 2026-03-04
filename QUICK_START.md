# Quick Start Guide - Deploy to Your Server

## Server Information
- **IP Address**: 140.245.240.202
- **Username**: root
- **Port**: 22
- **Password**: Akshay343402355468

## Method 1: Automated Deployment (Recommended)

### Step 1: Connect to Your Server
```bash
ssh root@140.245.240.202 -p 22
# Password: Akshay343402355468
```

### Step 2: Update System
Once connected, update your server:
```bash
apt update && apt upgrade -y
```

### Step 3: Install Git (if not installed)
```bash
apt install -y git
```

### Step 4: Clone Your Repository
```bash
cd /opt
git clone <YOUR_GIT_REPO_URL> nsfw-bot
cd nsfw-bot
```

### Step 5: Run the Deployment Script
```bash
chmod +x scripts/deploy_to_server.sh
./scripts/deploy_to_server.sh
```

The script will:
- Install Python and required dependencies
- Set up a virtual environment
- Install all bot dependencies
- Create a systemd service
- Start the bot automatically

### Step 6: Configure Bot Token
After the script completes:
```bash
nano .env
```

Replace `your_bot_token_here` with your actual bot token from @BotFather

Save and exit (Ctrl+X, then Y, then Enter)

### Step 7: Restart the Bot
```bash
systemctl restart nsfw-bot
```

### Step 8: Verify It's Running
```bash
systemctl status nsfw-bot
journalctl -u nsfw-bot -f
```

## Method 2: Manual Deployment

If you prefer manual control, follow these steps:

### 1. Connect to Server
```bash
ssh root@140.245.240.202 -p 22
```

### 2. Install Dependencies
```bash
apt update
apt install -y python3 python3-pip python3-venv git libgl1 libglib2.0-0
```

### 3. Clone Repository
```bash
cd /opt
git clone <YOUR_GIT_REPO_URL> nsfw-bot
cd nsfw-bot
```

### 4. Set Up Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment
```bash
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_actual_bot_token
LOG_CHANNEL_ID=your_log_channel_id
PFP_NSFWD_ENABLED=1
NSFW_WORD_LANGS=en,ru,zh,es,fr,de,ja,ko,ar,hi,it,pt,pl,cs,nl,sv,tr,th,fa,fil
EOF
```

### 6. Copy Service File
```bash
cp systemd/nsfw-bot.service /etc/systemd/system/nsfw-bot.service
```

### 7. Enable and Start Service
```bash
systemctl daemon-reload
systemctl enable nsfw-bot
systemctl start nsfw-bot
```

### 8. Check Status
```bash
systemctl status nsfw-bot
```

## Updating the Bot

When you push new code to Git:

```bash
cd /opt/nsfw-bot
git pull origin main
systemctl restart nsfw-bot
```

## Monitoring Commands

### View Logs (Real-time)
```bash
journalctl -u nsfw-bot -f
```

### View Last 50 Lines
```bash
journalctl -u nsfw-bot -n 50
```

### Check if Running
```bash
systemctl is-active nsfw-bot
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

## Troubleshooting

### Bot Won't Start
1. Check logs: `journalctl -u nsfw-bot -n 100`
2. Verify token in `.env` file
3. Reinstall dependencies: `pip install -r requirements.txt`

### High Memory Usage
Edit `.env` and set:
```
PFP_NSFWD_ENABLED=0
```
Then restart: `systemctl restart nsfw-bot`

### Service Issues
Reload systemd configuration:
```bash
systemctl daemon-reload
```

## Security Recommendations

### 1. Change SSH Password to Key-Based Authentication
On your local machine:
```bash
ssh-keygen -t ed25519
ssh-copy-id root@140.245.240.202 -p 22
```

Then disable password authentication on the server:
```bash
nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
systemctl restart sshd
```

### 2. Set Up Firewall
```bash
apt install -y ufw
ufw allow 22/tcp
ufw enable
```

### 3. Regular Updates
```bash
apt update && apt upgrade -y
```

### 4. Monitor Resources
Install htop:
```bash
apt install -y htop
htop
```

## Backup Configuration

Backup your settings:
```bash
tar -czf nsfw-bot-backup-$(date +%Y%m%d).tar.gz /opt/nsfw-bot/.env
```

## Next Steps After Deployment

1. ✅ Add your bot token to `.env`
2. ✅ Restart the service: `systemctl restart nsfw-bot`
3. ✅ Test the bot in Telegram
4. ✅ Set up log channel (see SETUP_LOG_CHANNEL.md)
5. ✅ Monitor logs: `journalctl -u nsfw-bot -f`

## Support Files

- `DEPLOYMENT.md` - Detailed deployment guide
- `README.md` - General bot documentation
- `SETUP_LOG_CHANNEL.md` - Log channel setup instructions

---

**Your Server**: 140.245.240.202:22  
**SSH User**: root  
**SSH Password**: Akshay343402355468