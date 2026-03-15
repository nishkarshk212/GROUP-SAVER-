#!/bin/bash
# Simple Bot Deployment Script
# Usage: ./deploy_simple.sh

echo "========================================"
echo "🚀 Simple Bot Deployment"
echo "========================================"
echo ""

# Step 1: Commit and push from local
echo "📦 Step 1: Pushing to GitHub..."
cd /Users/nishkarshkr/Desktop/bot-app
git add -A
git commit -m "Deploy updates $(date +%Y-%m-%d)"
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Pushed to GitHub successfully!"
else
    echo "❌ Push failed!"
    exit 1
fi

echo ""
echo "📡 Step 2: Deploying to server..."
echo ""

# Step 2: SSH to server and pull
ssh -p 22 root@140.245.240.202 << 'ENDSSH'
cd /opt/nsfw-bot

echo "Pulling latest changes from GitHub..."
git fetch origin main
git reset --hard origin/main

if [ $? -eq 0 ]; then
    echo "✅ Pulled from GitHub successfully!"
else
    echo "❌ Pull failed!"
    exit 1
fi

echo ""
echo "Restarting bot service..."
systemctl restart pyrogram-nsfw-bot

sleep 3

echo ""
echo "Checking bot status..."
systemctl status pyrogram-nsfw-bot --no-pager -n 5

if systemctl is-active --quiet pyrogram-nsfw-bot; then
    echo ""
    echo "✅ DEPLOYMENT SUCCESSFUL!"
    echo ""
    echo "Test your bot on Telegram:"
    echo "  1. Send /start → Profile picture + welcome"
    echo "  2. Send /settings → Unified settings menu"
else
    echo ""
    echo "⚠️ Bot may have issues, check logs:"
    journalctl -u pyrogram-nsfw-bot --since "2 minutes ago" -n 10
fi
ENDSSH

echo ""
echo "========================================"
echo "✅ Deployment Complete!"
echo "========================================"
