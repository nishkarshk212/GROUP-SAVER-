#!/bin/bash
set -e

echo "=========================================="
echo "Deploying NSFW Bot to Server"
echo "=========================================="
echo ""

# Server Configuration
SERVER_IP="140.245.240.202"
SERVER_USER="root"
SERVER_PORT="22"
BOT_DIR="/opt/nsfw-bot"
SERVICE_NAME="nsfw-bot"

echo "Server: ${SERVER_USER}@${SERVER_IP}:${SERVER_PORT}"
echo "Bot Directory: ${BOT_DIR}"
echo ""

# Step 1: Push latest changes to Git
echo "[Pre-deployment] Ensuring latest code is pushed to Git..."
git add -A
git commit -m "Auto-commit before server deployment" || echo "No changes to commit"
git push origin main || git push origin master
echo "✅ Latest code pushed to Git repository"
echo ""

# Step 2: SSH into server and deploy
echo "[Deployment] Connecting to server and deploying..."
echo ""

ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
#!/bin/bash
set -e

BOT_DIR="/opt/nsfw-bot"
SERVICE_NAME="nsfw-bot"

echo "=== Step 1: Navigate to bot directory ==="
cd "$BOT_DIR" || exit 1

echo "=== Step 2: Pull latest changes from Git ==="
git pull origin main || git pull origin master || true

echo "=== Step 3: Update Python dependencies ==="
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

echo "=== Step 4: Verify .env configuration ==="
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found!"
    exit 1
fi

# Check if bot token exists
if ! grep -q "^TELEGRAM_BOT_TOKEN=" .env; then
    echo "❌ ERROR: TELEGRAM_BOT_TOKEN not configured in .env!"
    exit 1
fi

TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env | cut -d'=' -f2)
if [ "$TOKEN" = "your_bot_token_here" ] || [ -z "$TOKEN" ]; then
    echo "❌ ERROR: Please update TELEGRAM_BOT_TOKEN in .env with actual token!"
    exit 1
fi

echo "✅ Bot token configured"

# Check log channel
if grep -q "^LOG_CHANNEL_ID=" .env; then
    LOG_CHANNEL=$(grep "^LOG_CHANNEL_ID=" .env | cut -d'=' -f2)
    echo "✅ Log channel configured: $LOG_CHANNEL"
else
    echo "⚠️  LOG_CHANNEL_ID not set (optional)"
fi

echo "=== Step 5: Setup daily cleanup service ==="
# Copy cleanup script
if [ -f "scripts/cleanup_daily.sh" ]; then
    cp scripts/cleanup_daily.sh $BOT_DIR/scripts/
    chmod +x $BOT_DIR/scripts/cleanup_daily.sh
    echo "✅ Cleanup script installed"
fi

# Copy systemd cleanup service files
if [ -f "systemd/nsfw-bot-cleanup.service" ]; then
    cp systemd/nsfw-bot-cleanup.service /etc/systemd/system/
    echo "✅ Cleanup service file installed"
fi

if [ -f "systemd/nsfw-bot-cleanup.timer" ]; then
    cp systemd/nsfw-bot-cleanup.timer /etc/systemd/system/
    echo "✅ Cleanup timer file installed"
fi

# Enable and start the cleanup timer
systemctl daemon-reload
systemctl enable nsfw-bot-cleanup.timer
systemctl start nsfw-bot-cleanup.timer
echo "✅ Daily cleanup timer enabled and started"
echo ""

echo "=== Step 6: Install logrotate configuration ==="
if [ -f "logrotate.conf" ]; then
    cp logrotate.conf /etc/logrotate.d/nsfw-bot
    echo "✅ Logrotate configuration installed"
fi
echo ""

echo "=== Step 7: Restart systemd service ==="
systemctl daemon-reload
systemctl restart $SERVICE_NAME

echo "=== Step 8: Wait for service to start ==="
sleep 3

echo "=== Step 9: Check service status ==="
systemctl is-active $SERVICE_NAME && echo "✅ Service is running" || {
    echo "❌ Service failed to start"
    systemctl status $SERVICE_NAME --no-pager
    exit 1
}

echo "=== Step 10: Check cleanup timer status ==="
systemctl is-active nsfw-bot-cleanup.timer && echo "✅ Cleanup timer is active" || echo "⚠️  Cleanup timer not active"
systemctl list-timers | grep nsfw-bot || echo "ℹ️  Timer info not available"
echo ""

echo "=== Step 11: Show recent logs ==="
echo ""
echo "Last 10 log lines:"
journalctl -u $SERVICE_NAME -n 10 --no-pager

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Bot Status: $(systemctl is-active $SERVICE_NAME)"
echo "Service: $SERVICE_NAME"
echo "Directory: $BOT_DIR"
echo ""
echo "Useful Commands:"
echo "  View logs:     journalctl -u $SERVICE_NAME -f"
echo "  Restart:       systemctl restart $SERVICE_NAME"
echo "  Stop:          systemctl stop $SERVICE_NAME"
echo "  Status:        systemctl status $SERVICE_NAME"
echo ""

ENDSSH

echo ""
echo "=========================================="
echo "Deployment Finished!"
echo "=========================================="
echo ""
echo "To check the bot status manually:"
echo "  ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP}"
echo "  systemctl status ${SERVICE_NAME}"
echo "  journalctl -u ${SERVICE_NAME} -f"
echo ""
