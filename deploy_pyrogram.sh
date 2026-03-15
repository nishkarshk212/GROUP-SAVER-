#!/bin/bash
# Complete Deployment Script for Pyrogram + Redis Bot
set -e

echo "=============================================="
echo "🚀 Deploying Pyrogram + Redis Bot to Server"
echo "=============================================="
echo ""

SERVER_IP="140.245.240.202"
SERVER_PORT="22"
SERVER_USER="root"
BOT_DIR="/opt/nsfw-bot"

echo "📋 Configuration:"
echo "   Server: ${SERVER_USER}@${SERVER_IP}:${SERVER_PORT}"
echo "   Bot Directory: ${BOT_DIR}"
echo ""

# Step 1: Copy files to server
echo "📦 Copying files to server..."
scp -P $SERVER_PORT -r pyrogram_bot/* ${SERVER_USER}@${SERVER_IP}:${BOT_DIR}/pyrogram_new/
echo "✅ Files copied"
echo ""

# Step 2: SSH and deploy
echo "🔐 Connecting to server for deployment..."
echo ""

ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
#!/bin/bash
set -e

BOT_DIR="/opt/nsfw-bot"
NEW_BOT_DIR="$BOT_DIR/pyrogram_new"

echo "=============================================="
echo "Server-Side Deployment"
echo "=============================================="
echo ""

# Step 1: Install Redis if not installed
echo "📦 Checking Redis..."
if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    apt update
    apt install redis-server -y
fi

systemctl start redis
systemctl enable redis
echo "✅ Redis installed and running"
echo ""

# Step 2: Stop old bot
echo "🛑 Stopping old bot..."
systemctl stop nsfw-bot || true
systemctl disable nsfw-bot || true
pkill -9 -f "python.*bot" || true
sleep 5
echo "✅ Old bot stopped"
echo ""

# Step 3: Clear Python cache
echo "🧹 Clearing cache..."
cd $BOT_DIR
rm -rf __pycache__ .venv/__pycache__ 2>/dev/null || true
echo "✅ Cache cleared"
echo ""

# Step 4: Backup old bot files
echo "💾 Backing up old bot..."
if [ -f "bot.py" ]; then
    mv bot.py bot_old_backup.py
    echo "   Backed up bot.py"
fi
echo ""

# Step 5: Move new bot files
echo "📁 Moving new bot files..."
if [ -d "$NEW_BOT_DIR" ]; then
    cp -r $NEW_BOT_DIR/* .
    rm -rf $NEW_BOT_DIR
    echo "✅ New bot files moved"
else
    echo "❌ New bot directory not found!"
    exit 1
fi
echo ""

# Step 6: Install dependencies
echo "📦 Installing dependencies..."
source $BOT_DIR/.venv/bin/activate
pip install --upgrade pip
pip install pyrogram tgcrypto redis rq opencv-python lottie deepface imagehash --no-cache-dir
echo "✅ Dependencies installed"
echo ""

# Step 7: Create directories
echo "📁 Creating directories..."
mkdir -p temp logs
chmod 777 temp
echo "✅ Directories created"
echo ""

# Step 8: Setup systemd services
echo "⚙️  Setting up systemd services..."

# Bot service
cat > /etc/systemd/system/pyrogram-nsfw-bot.service << EOF
[Unit]
Description=Pyrogram NSFW Detection Bot
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/.venv/bin"
ExecStart=$BOT_DIR/.venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/pyrogram-bot.log
StandardError=append:/var/log/pyrogram-bot.log

[Install]
WantedBy=multi-user.target
EOF

# Worker service
cat > /etc/systemd/system/pyrogram-nsfw-worker.service << EOF
[Unit]
Description=NSFW Detection Worker
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/.venv/bin"
ExecStart=$BOT_DIR/.venv/bin/python worker.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/pyrogram-worker.log
StandardError=append:/var/log/pyrogram-worker.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd services created"
echo ""

# Step 9: Enable and start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable pyrogram-nsfw-bot
systemctl enable pyrogram-nsfw-worker
systemctl start pyrogram-nsfw-bot
systemctl start pyrogram-nsfw-worker
sleep 5
echo "✅ Services started"
echo ""

# Step 10: Verify deployment
echo "🔍 Verifying deployment..."
echo ""

# Check Redis
if systemctl is-active redis > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is NOT running"
fi

# Check bot
if systemctl is-active pyrogram-nsfw-bot > /dev/null 2>&1; then
    echo "✅ Bot is running"
else
    echo "❌ Bot is NOT running"
fi

# Check worker
if systemctl is-active pyrogram-nsfw-worker > /dev/null 2>&1; then
    echo "✅ Worker is running"
else
    echo "❌ Worker is NOT running"
fi

# Check for conflicts
CONFLICTS=$(journalctl -u pyrogram-nsfw-bot --since "2 minutes ago" | grep -i conflict | wc -l)
if [ $CONFLICTS -eq 0 ]; then
    echo "✅ No conflict errors"
else
    echo "⚠️  Found $CONFLICTS conflict errors"
fi

echo ""
echo "=============================================="
echo "Deployment Status"
echo "=============================================="
echo ""

systemctl status pyrogram-nsfw-bot --no-pager -n 10
echo ""
echo "=============================================="
echo ""

ENDSSH

echo ""
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit config.py on server:"
echo "   ssh root@${SERVER_IP} -p ${SERVER_PORT}"
echo "   cd /opt/nsfw-bot"
echo "   nano config.py"
echo "   Add: API_ID, API_HASH, BOT_TOKEN"
echo ""
echo "2. Restart bot after config:"
echo "   systemctl restart pyrogram-nsfw-bot"
echo ""
echo "3. Test bot:"
echo "   Send /start to your bot on Telegram"
echo ""
echo "4. Monitor logs:"
echo "   journalctl -u pyrogram-nsfw-bot -f"
echo ""
echo "=============================================="
