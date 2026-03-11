#!/bin/bash
# Quick Start Script for Pyrogram + Redis Bot

set -e

echo "=============================================="
echo "🚀 Pyrogram NSFW Bot - Quick Setup"
echo "=============================================="
echo ""

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis not found!"
    echo ""
    echo "Install Redis:"
    echo "  Ubuntu/Debian: sudo apt install redis-server"
    echo "  macOS: brew install redis"
    exit 1
fi

echo "✅ Redis found"

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

echo "✅ Redis is running"
echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Create temp directory
mkdir -p temp
mkdir -p logs
echo "✅ Directories created"
echo ""

# Configuration check
echo "🔧 Checking configuration..."
if grep -q "YOUR_API_HASH" config.py || grep -q "YOUR_BOT_TOKEN" config.py; then
    echo "❌ Please edit config.py and add:"
    echo "   - API_ID"
    echo "   - API_HASH"
    echo "   - BOT_TOKEN"
    exit 1
fi

echo "✅ Configuration looks good"
echo ""

echo "=============================================="
echo "✅ Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start Redis Worker (Terminal 1):"
echo "   python worker.py"
echo ""
echo "2. Start Bot (Terminal 2):"
echo "   python bot.py"
echo ""
echo "Or run both in background:"
echo "   nohup python worker.py > logs/worker.log 2>&1 &"
echo "   nohup python bot.py > logs/bot.log 2>&1 &"
echo ""
echo "=============================================="
