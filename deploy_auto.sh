#!/bin/bash
# Automated Deployment Script with SSH Passphrase
# This script commits, pushes to Git, and deploys to server using SSH passphrase

set -e

echo "=============================================="
echo "NSFW Bot - Automated Deployment"
echo "=============================================="
echo ""

# Configuration
SERVER_IP="140.245.240.202"
SERVER_USER="root"
SERVER_PORT="22"
BOT_DIR="/opt/nsfw-bot"
SERVICE_NAME="nsfw-bot"
GIT_REPO="origin"

echo "📋 Configuration:"
echo "   Server: ${SERVER_USER}@${SERVER_IP}:${SERVER_PORT}"
echo "   Bot Directory: ${BOT_DIR}"
echo "   Git Remote: ${GIT_REPO}"
echo ""

# Step 1: Commit and push to Git
echo "=============================================="
echo "Step 1: Committing changes to Git"
echo "=============================================="
echo ""

# Add all changes
git add -A

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No local changes to commit"
else
    # Commit with timestamp
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    git commit -m "Auto-deployment: Updates on ${TIMESTAMP}"
    echo "✅ Changes committed"
fi

# Push to Git
echo ""
echo "Pushing to Git repository..."
git push ${GIT_REPO} main || git push ${GIT_REPO} master
echo "✅ Code pushed to Git repository"
echo ""

# Step 2: Deploy to server via SSH
echo "=============================================="
echo "Step 2: Deploying to server via SSH"
echo "=============================================="
echo ""
echo "🔐 You will be prompted for your SSH key passphrase..."
echo ""

# Create SSH command with port
SSH_CMD="ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP}"

# Execute deployment commands on server
$SSH_CMD << 'ENDSSH'
#!/bin/bash
set -e

BOT_DIR="/opt/nsfw-bot"
SERVICE_NAME="nsfw-bot"

echo "=== Step 1: Navigate to bot directory ==="
cd "$BOT_DIR" || {
    echo "❌ ERROR: Bot directory not found!"
    exit 1
}

echo "=== Step 2: Pull latest changes from Git ==="
git pull origin main || git pull origin master || {
    echo "⚠️  Git pull failed, continuing with current code"
}
echo "✅ Code updated from Git"

echo "=== Step 3: Update Python dependencies ==="
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
echo "✅ Dependencies updated"

echo "=== Step 4: Verify configuration ==="
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found!"
    exit 1
fi

# Check bot token
if ! grep -q "^TELEGRAM_BOT_TOKEN=" .env; then
    echo "❌ ERROR: TELEGRAM_BOT_TOKEN not configured!"
    exit 1
fi

TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env | cut -d'=' -f2)
if [ "$TOKEN" = "your_bot_token_here" ] || [ -z "$TOKEN" ]; then
    echo "❌ ERROR: Invalid bot token in .env!"
    exit 1
fi

echo "✅ Bot token verified"

# Check log channel (optional)
if grep -q "^LOG_CHANNEL_ID=" .env; then
    LOG_CHANNEL=$(grep "^LOG_CHANNEL_ID=" .env | cut -d'=' -f2)
    echo "✅ Log channel configured: $LOG_CHANNEL"
fi

echo "=== Step 5: Setup system services ==="

# Install cleanup service files
if [ -f "systemd/nsfw-bot-cleanup.service" ]; then
    cp systemd/nsfw-bot-cleanup.service /etc/systemd/system/
    echo "✅ Cleanup service installed"
fi

if [ -f "systemd/nsfw-bot-cleanup.timer" ]; then
    cp systemd/nsfw-bot-cleanup.timer /etc/systemd/system/
    echo "✅ Cleanup timer installed"
fi

# Install logrotate config
if [ -f "logrotate.conf" ]; then
    cp logrotate.conf /etc/logrotate.d/nsfw-bot
    echo "✅ Logrotate config installed"
fi

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable nsfw-bot-cleanup.timer 2>/dev/null || true
systemctl start nsfw-bot-cleanup.timer 2>/dev/null || true
echo "✅ System services configured"

echo "=== Step 6: Restart bot service ==="
systemctl daemon-reload
systemctl restart $SERVICE_NAME
sleep 3

echo "=== Step 7: Verify service status ==="
if systemctl is-active $SERVICE_NAME > /dev/null 2>&1; then
    echo "✅ Service is RUNNING"
else
    echo "❌ Service FAILED to start"
    systemctl status $SERVICE_NAME --no-pager
    exit 1
fi

echo "=== Step 8: Show recent logs ==="
echo ""
echo "Last 15 log lines:"
journalctl -u $SERVICE_NAME -n 15 --no-pager
echo ""

echo "=== Deployment Complete! ==="
echo ""

ENDSSH

# Step 3: Display summary
echo ""
echo "=============================================="
echo "✅ Deployment Successful!"
echo "=============================================="
echo ""
echo "📊 Deployment Summary:"
echo "   Server: ${SERVER_USER}@${SERVER_IP}:${SERVER_PORT}"
echo "   Service: ${SERVICE_NAME}"
echo "   Directory: ${BOT_DIR}"
echo ""
echo "🔍 Useful Commands:"
echo "   Check status:  ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} 'systemctl status ${SERVICE_NAME}'"
echo "   View logs:     ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} 'journalctl -u ${SERVICE_NAME} -f'"
echo "   Restart:       ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} 'systemctl restart ${SERVICE_NAME}'"
echo ""
echo "🎉 Your bot is now live with the latest updates!"
echo ""
