# Server Deployment Guide for NSFW Detection Bot

## Prerequisites
- Server with SSH access (Ubuntu/Debian recommended)
- Python 3.8+ installed on server
- Git installed on server
- Telegram Bot Token

## Server Information
- **IP**: 140.245.240.202
- **Username**: root
- **Port**: 22

## Deployment Steps

### 1. Connect to Your Server
```bash
ssh root@140.245.240.202 -p 22
```

### 2. Update System Packages
```bash
apt update && apt upgrade -y
```

### 3. Install Required Dependencies
```bash
apt install -y python3 python3-pip python3-venv git curl wget
```

### 4. Clone Your Git Repository
```bash
cd /opt
git clone <YOUR_GIT_REPO_URL> nsfw-bot
cd nsfw-bot
```

### 5. Set Up Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Configure Environment Variables
Create a `.env` file with your bot token:
```bash
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
LOG_CHANNEL_ID=your_log_channel_id_or_username
PFP_NSFWD_ENABLED=1
NSFW_WORD_LANGS=en,ru,zh,es,fr,de,ja,ko,ar,hi,it,pt,pl,cs,nl,sv,tr,th,fa,fil
EOF
```

**Important**: Replace `your_bot_token_here` with your actual bot token from @BotFather

### 7. Test the Bot
Run the bot manually to ensure it works:
```bash
source .venv/bin/activate
python bot.py
```

You should see output indicating the bot has started successfully.

### 8. Set Up as a System Service (systemd)

Create a systemd service file:
```bash
cat > /etc/systemd/system/nsfw-bot.service << EOF
[Unit]
Description=Telegram NSFW Detection Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nsfw-bot
Environment="PATH=/opt/nsfw-bot/.venv/bin"
ExecStart=/opt/nsfw-bot/.venv/bin/python bot.py
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nsfw-bot

[Install]
WantedBy=multi-user.target
EOF
```

### 9. Enable and Start the Service
```bash
systemctl daemon-reload
systemctl enable nsfw-bot
systemctl start nsfw-bot
```

### 10. Check Service Status
```bash
systemctl status nsfw-bot
```

### 11. View Logs
```bash
# Real-time logs
journalctl -u nsfw-bot -f

# Last 50 lines
journalctl -u nsfw-bot -n 50
```

## Managing the Bot

### Restart the Bot
```bash
systemctl restart nsfw-bot
```

### Stop the Bot
```bash
systemctl stop nsfw-bot
```

### Start the Bot
```bash
systemctl start nsfw-bot
```

### Check if Bot is Running
```bash
systemctl is-active nsfw-bot
```

## Updating the Bot

When you push new code to your Git repository:

```bash
cd /opt/nsfw-bot
git pull origin main  # or your default branch
systemctl restart nsfw-bot
```

## Security Considerations

1. **Firewall**: Ensure only necessary ports are open
   ```bash
   ufw allow 22/tcp  # SSH
   ufw enable
   ```

2. **SSH Keys**: Consider using SSH keys instead of passwords
   ```bash
   ssh-keygen -t ed25519
   ssh-copy-id root@140.245.240.202
   ```

3. **Environment Variables**: Keep sensitive data in `.env` file (not in Git)

4. **Regular Updates**: Keep your system updated
   ```bash
   apt update && apt upgrade -y
   ```

## Troubleshooting

### Bot Won't Start
Check the logs:
```bash
journalctl -u nsfw-bot -n 100 --no-pager
```

Common issues:
- Missing dependencies: `pip install -r requirements.txt`
- Invalid bot token: Verify TELEGRAM_BOT_TOKEN in .env
- Port conflicts: Ensure no other bot instances running

### High Memory Usage
If the bot uses too much memory:
- Reduce the number of enabled languages in NSFW_WORD_LANGS
- Disable profile photo scanning: PFP_NSFWD_ENABLED=0

### Service Fails to Start
Check if the service file is correct:
```bash
cat /etc/systemd/system/nsfw-bot.service
systemctl daemon-reload
```

## Docker Deployment (Alternative)

If you prefer Docker:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f nsfw-bot
```

## Monitoring

Set up monitoring for your bot:
```bash
# Install htop for resource monitoring
apt install -y htop

# Monitor bot process
htop
```

## Backup

Backup your configuration:
```bash
tar -czf nsfw-bot-backup-$(date +%Y%m%d).tar.gz /opt/nsfw-bot/.env
```

## Support

For issues or questions:
- Check bot logs: `journalctl -u nsfw-bot -f`
- Review documentation: README.md, SETUP_LOG_CHANNEL.md