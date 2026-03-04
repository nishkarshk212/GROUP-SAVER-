#!/bin/bash
set -e

echo "=========================================="
echo "NSFW Bot Server Deployment Script"
echo "=========================================="

# Configuration
BOT_DIR="/opt/nsfw-bot"
SERVICE_NAME="nsfw-bot"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')

echo ""
echo "Python version: $PYTHON_VERSION"
echo "Bot directory: $BOT_DIR"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use: sudo $0)"
    exit 1
fi

# Step 1: Install dependencies
echo "[1/7] Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv git curl wget libgl1 libglib2.0-0

# Step 2: Create bot directory
echo "[2/7] Creating bot directory..."
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

# Step 3: Clone repository (if not already cloned)
if [ ! -d ".git" ]; then
    echo "[3/7] Cloning Git repository..."
    read -p "Enter your Git repository URL: " GIT_URL
    git clone "$GIT_URL" .
else
    echo "[3/7] Git repository already exists, pulling latest changes..."
    git pull origin main || git pull origin master
fi

# Step 4: Set up virtual environment
echo "[4/7] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Configure environment
echo "[5/7] Configuring environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
LOG_CHANNEL_ID=your_log_channel_id_or_username
PFP_NSFWD_ENABLED=1
NSFW_WORD_LANGS=en,ru,zh,es,fr,de,ja,ko,ar,hi,it,pt,pl,cs,nl,sv,tr,th,fa,fil
EOF
    echo "⚠️  IMPORTANT: Edit .env file and add your Telegram bot token!"
    echo "   Run: nano .env"
else
    echo ".env file already exists."
fi

# Step 6: Install systemd service
echo "[6/7] Installing systemd service..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/systemd/nsfw-bot.service" ]; then
    cp "$SCRIPT_DIR/systemd/nsfw-bot.service" /etc/systemd/system/$SERVICE_NAME.service
else
    # Create service inline if file doesn't exist
    cat > /etc/systemd/system/$SERVICE_NAME.service << 'EOF'
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
fi

systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Step 7: Start the bot
echo "[7/7] Starting the bot service..."
systemctl start $SERVICE_NAME

# Display status
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Service Status:"
systemctl status $SERVICE_NAME --no-pager
echo ""
echo "Useful Commands:"
echo "  Start bot:    systemctl start $SERVICE_NAME"
echo "  Stop bot:     systemctl stop $SERVICE_NAME"
echo "  Restart bot:  systemctl restart $SERVICE_NAME"
echo "  View logs:    journalctl -u $SERVICE_NAME -f"
echo ""
echo "Next Steps:"
echo "1. Edit .env file with your Telegram bot token"
echo "2. Restart the service: systemctl restart $SERVICE_NAME"
echo "3. Monitor logs: journalctl -u $SERVICE_NAME -f"
echo ""
