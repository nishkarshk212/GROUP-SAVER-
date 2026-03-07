#!/bin/bash
# Quick Deploy to Server - Copy & Paste Commands
# Run this on your LOCAL machine, then SSH to server

echo "=============================================="
echo "NSFW Bot - Server Deployment Commands"
echo "=============================================="
echo ""
echo "SERVER: root@140.245.240.202:22"
echo "DIRECTORY: /opt/nsfw-bot"
echo ""
echo "=============================================="
echo "STEP 1: SSH into your server"
echo "=============================================="
echo ""
echo "Run this command:"
echo "----------------------------------------"
echo "ssh root@140.245.240.202 -p 22"
echo "----------------------------------------"
echo ""
echo "After connecting, copy and run these commands ON THE SERVER:"
echo ""
echo "=============================================="
echo "STEP 2: Update code from Git"
echo "=============================================="
cat << 'EOF'
cd /opt/nsfw-bot
git pull origin main
EOF
echo ""
echo "=============================================="
echo "STEP 3: Update Python dependencies"
echo "=============================================="
cat << 'EOF'
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
deactivate
EOF
echo ""
echo "=============================================="
echo "STEP 4: Restart the bot"
echo "=============================================="
cat << 'EOF'
systemctl restart nsfw-bot
systemctl daemon-reload
EOF
echo ""
echo "=============================================="
echo "STEP 5: Verify deployment"
echo "=============================================="
cat << 'EOF'
systemctl status nsfw-bot
journalctl -u nsfw-bot -n 30 --no-pager
EOF
echo ""
echo "=============================================="
echo "Expected Output"
echo "=============================================="
echo "You should see in the logs:"
echo "✅ Loaded NSFW detection: XXX words, XXX phrases from XX/XX languages"
echo ""
echo "If you see this, the deployment was successful!"
echo ""
echo "=============================================="
echo "Quick Status Check (after deployment)"
echo "=============================================="
cat << 'EOF'
# One-line status check
systemctl is-active nsfw-bot && echo "✅ Bot is RUNNING" || echo "❌ Bot is NOT RUNNING"
journalctl -u nsfw-bot | grep "Loaded NSFW detection" | tail -1
EOF
echo ""
echo "=============================================="
echo ""
