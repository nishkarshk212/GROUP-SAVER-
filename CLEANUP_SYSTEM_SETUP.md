# Auto-Cleanup System Setup Guide

## Overview
Your NSFW Bot now has an **automatic daily cleanup system** that:
- ✅ Cleans old logs (older than 1 day)
- ✅ Removes temporary files
- ✅ Clears Python cache
- ✅ Rotates log files
- ✅ Runs automatically at 3:00 AM daily

## Files Created

### On Your Local Machine (Git Repository)
```
bot-app/
├── scripts/
│   ├── cleanup_daily.sh              # Main cleanup script
│   └── install_cleanup_service.sh    # One-time installer
├── systemd/
│   ├── nsfw-bot-cleanup.service      # Systemd service definition
│   └── nsfw-bot-cleanup.timer        # Daily timer configuration
├── logrotate.conf                     # Log rotation config
└── deploy_server.sh                   # Updated deployment script
```

### Will Be Installed On Server
```
/opt/nsfw-bot/
├── scripts/cleanup_daily.sh
├── systemd/nsfw-bot-cleanup.service
└── systemd/nsfw-bot-cleanup.timer

/etc/systemd/system/
├── nsfw-bot-cleanup.service
└── nsfw-bot-cleanup.timer

/etc/logrotate.d/
└── nsfw-bot
```

## Installation Instructions

### Option 1: Automatic (Recommended)
After your next deployment, SSH into your server and run:

```bash
ssh root@140.245.240.202
cd /opt/nsfw-bot
bash scripts/install_cleanup_service.sh
```

This one-time script will:
1. Install the cleanup service
2. Enable the daily timer
3. Configure logrotate
4. Test the cleanup script
5. Verify everything is working

### Option 2: Manual Steps
If you prefer to do it manually:

```bash
# SSH into server
ssh root@140.245.240.202

# Navigate to bot directory
cd /opt/nsfw-bot

# Make cleanup script executable
chmod +x scripts/cleanup_daily.sh

# Copy systemd files
cp systemd/nsfw-bot-cleanup.service /etc/systemd/system/
cp systemd/nsfw-bot-cleanup.timer /etc/systemd/system/

# Copy logrotate config
cp logrotate.conf /etc/logrotate.d/nsfw-bot

# Reload systemd and enable timer
systemctl daemon-reload
systemctl enable nsfw-bot-cleanup.timer
systemctl start nsfw-bot-cleanup.timer

# Verify it's running
systemctl list-timers | grep nsfw-bot
```

## What Gets Cleaned

### Daily Cleanup (3:00 AM)
- **Systemd Journal Logs**: Keeps only last 24 hours
- **Log Files**: Removes `.log` files older than 1 day from `/var/log/nsfw-bot/`
- **Temporary Files**: Deletes files in `/tmp/nsfw-bot/` older than 1 day
- **Python Cache**: Removes `__pycache__` directories and `.pyc` files
- **Naughty Words Cache**: Reports size but doesn't delete (needed for bot)

### Log Rotation
- Log files are rotated daily
- Kept for 1 day before compression
- Compressed logs kept for additional rotation cycle
- Maximum log file size: 10MB

## Monitoring & Management

### Check Timer Status
```bash
# See when next cleanup will run
systemctl list-timers | grep nsfw-bot

# View timer details
systemctl status nsfw-bot-cleanup.timer
```

### Run Cleanup Manually
```bash
# Execute cleanup immediately
bash /opt/nsfw-bot/scripts/cleanup_daily.sh
```

### View Cleanup Logs
```bash
# See cleanup service logs
journalctl -u nsfw-bot-cleanup -f

# Check last cleanup run
journalctl -u nsfw-bot-cleanup --since today
```

### Check Disk Usage
```bash
# Before and after cleanup comparison
du -sh /opt/nsfw-bot
du -sh /var/log/nsfw-bot
du -sh /tmp/nsfw-bot
```

## Customization

### Change Cleanup Time
Edit `/etc/systemd/system/nsfw-bot-cleanup.timer`:
```ini
[Trigger]
# Change to your preferred time (HH:MM format)
OnCalendar=*-*-* 03:00:00  # 3 AM
```
Then reload:
```bash
systemctl daemon-reload
systemctl restart nsfw-bot-cleanup.timer
```

### Change Retention Period
Edit `/opt/nsfw-bot/scripts/cleanup_daily.sh`:
```bash
MAX_LOG_AGE_DAYS=1      # Change to 7 for week, etc.
MAX_TEMP_AGE_DAYS=1     # Change as needed
```

### Disable Service Restart After Cleanup
The cleanup script doesn't restart the bot by default (safer). To enable:
Edit `scripts/cleanup_daily.sh` and uncomment:
```bash
# systemctl restart nsfw-bot
```

## Troubleshooting

### Timer Not Running
```bash
# Check if timer is active
systemctl is-active nsfw-bot-cleanup.timer

# Check for errors
systemctl status nsfw-bot-cleanup.timer
journalctl -u nsfw-bot-cleanup.timer
```

### Cleanup Script Fails
```bash
# Run manually to see errors
bash -x /opt/nsfw-bot/scripts/cleanup_daily.sh

# Check permissions
ls -la /opt/nsfw-bot/scripts/cleanup_daily.sh
chmod +x /opt/nsfw-bot/scripts/cleanup_daily.sh
```

### Logs Not Being Cleaned
```bash
# Check logrotate status
cat /var/lib/logrotate/status

# Force logrotate
logrotate -f /etc/logrotate.d/nsfw-bot
```

## Benefits

✅ **Disk Space Savings**: Automatically removes old logs and temp files  
✅ **Performance**: Cleaner system runs better  
✅ **Maintenance-Free**: Set it and forget it  
✅ **Logging**: All cleanup actions are logged  
✅ **Safe**: Doesn't restart bot unless you enable it  
✅ **Configurable**: Easy to adjust retention periods  

## Next Steps

1. **Deploy** the latest code to your server
2. **SSH** into your server: `ssh root@140.245.240.202`
3. **Run installer**: `bash /opt/nsfw-bot/scripts/install_cleanup_service.sh`
4. **Verify**: `systemctl list-timers | grep nsfw-bot`
5. **Done!** Cleanup will run automatically every day at 3 AM

---

**Created:** March 5, 2026  
**Version:** 1.0  
**Bot:** NSFW Detection Bot v2.0
