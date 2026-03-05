#!/bin/bash
#
# Fresh Deployment from Git Repository
# This script will clone or update the bot from GitHub and deploy it
#

set -e

echo "=========================================="
echo "Fresh Git Deployment for NSFW Bot"
echo "=========================================="
echo ""

# Server Configuration
SERVER_IP="140.245.240.202"
SERVER_USER="root"
SERVER_PORT="22"
BOT_DIR="/opt/nsfw-bot"
SERVICE_NAME="nsfw-bot"
GITHUB_REPO="https://github.com/nishkarshk212/GROUP-SAVER-.git"

echo "Server: ${SERVER_USER}@${SERVER_IP}:${SERVER_PORT}"
echo "Bot Directory: ${BOT_DIR}"
echo "GitHub Repo: ${GITHUB_REPO}"
echo ""

# Push latest changes first
echo "[Pre-deployment] Ensuring latest code is pushed to Git..."
git add -A
git commit -m "Auto-commit before server deployment" || echo "No changes to commit"
git push origin main || git push origin master
echo "✅ Latest code pushed to Git repository"
echo ""

echo "[Deployment] Connecting to server and deploying..."
echo ""

ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
#!/bin/bash
set -e

BOT_DIR="/opt/nsfw-bot"
SERVICE_NAME="nsfw-bot"
GITHUB_REPO="https://github.com/nishkarshk212/GROUP-SAVER-.git"

echo "=== Step 1: Stop existing bot service ==="
systemctl stop $SERVICE_NAME 2>/dev/null || true
pkill -f bot.py 2>/dev/null || true
sleep 2
echo "✅ Stopped existing bot processes"
echo ""

echo "=== Step 2: Backup existing installation (if any) ==="
if [ -d "$BOT_DIR" ]; then
    BACKUP_DIR="${BOT_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Backing up to $BACKUP_DIR..."
    cp -r "$BOT_DIR" "$BACKUP_DIR" || true
    echo "✅ Backup created at $BACKUP_DIR"
    
    # Keep only last 3 backups
    ls -dt ${BOT_DIR}.backup.* 2>/dev/null | tail -n +4 | xargs rm -rf 2>/dev/null || true
else
    echo "ℹ️ No existing installation to backup"
fi
echo ""

echo "=== Step 3: Clone or Update from Git ==="
if [ -d "$BOT_DIR/.git" ]; then
    echo "Git repository found, pulling latest changes..."
    cd "$BOT_DIR"
    git fetch --all
    git reset --hard origin/main
    git clean -fd
    echo "✅ Updated from Git"
else
    echo "Cloning repository..."
    if [ -d "$BOT_DIR" ]; then
        rm -rf "$BOT_DIR"
    fi
    git clone $GITHUB_REPO "$BOT_DIR"
    cd "$BOT_DIR"
    echo "✅ Cloned from Git"
fi
echo ""

echo "=== Step 4: Setup Python virtual environment ==="
cd "$BOT_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Created virtual environment"
else
    echo "ℹ️ Virtual environment already exists"
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
echo "✅ Python dependencies installed"
echo ""

echo "=== Step 5: Preserve .env file ==="
if [ ! -f "$BOT_DIR/.env" ]; then
    echo "⚠️ WARNING: .env file not found!"
    echo "Please create .env with TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Check bot token
TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$BOT_DIR/.env" | cut -d'=' -f2)
if [ "$TOKEN" = "your_bot_token_here" ] || [ -z "$TOKEN" ]; then
    echo "❌ ERROR: Please update TELEGRAM_BOT_TOKEN in .env!"
    exit 1
fi
echo "✅ Bot token configured"
echo ""

echo "=== Step 6: Install systemd service ==="
cp "$BOT_DIR/systemd/nsfw-bot.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME
echo "✅ Systemd service installed and enabled"
echo ""

echo "=== Step 7: Install cleanup services ==="
if [ -f "$BOT_DIR/scripts/install_cleanup_service.sh" ]; then
    bash "$BOT_DIR/scripts/install_cleanup_service.sh" || echo "⚠️ Cleanup service installation had warnings"
else
    echo "ℹ️ Cleanup service script not found (optional)"
fi
echo ""

echo "=== Step 8: Start bot service ==="
systemctl start $SERVICE_NAME
sleep 3
echo "✅ Bot service started"
echo ""

echo "=== Step 9: Verify service status ==="
if systemctl is-active $SERVICE_NAME > /dev/null 2>&1; then
    echo "✅ Service is running successfully!"
else
    echo "❌ Service failed to start"
    systemctl status $SERVICE_NAME --no-pager
    exit 1
fi
echo ""

echo "=== Step 10: Show recent logs ==="
echo ""
journalctl -u $SERVICE_NAME -n 15 --no-pager
echo ""

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
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
echo "  Uninstall:     systemctl stop $SERVICE_NAME && systemctl disable $SERVICE_NAME && rm -rf $BOT_DIR"
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
