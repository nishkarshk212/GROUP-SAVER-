#!/bin/bash
# Diagnostic script for sticker scan issues
# Run this on the SERVER (not local machine)

echo "=============================================="
echo "Sticker Scan Diagnostic Tool"
echo "=============================================="
echo ""

# Check 1: Bot service status
echo "📊 Step 1: Checking bot service status..."
systemctl is-active nsfw-bot > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Bot service is RUNNING"
else
    echo "❌ Bot service is NOT RUNNING"
    echo "   Fix: systemctl start nsfw-bot"
    exit 1
fi
echo ""

# Check 2: Look for conflict errors
echo "🔍 Step 2: Checking for conflict errors..."
CONFLICTS=$(journalctl -u nsfw-bot --since "10 minutes ago" | grep -i "conflict" | wc -l)
if [ $CONFLICTS -gt 0 ]; then
    echo "❌ FOUND $CONFLICTS CONFLICT ERRORS!"
    echo "   This is likely your problem!"
    echo ""
    echo "   Multiple bot instances are running."
    echo "   Fix:"
    echo "   sudo systemctl stop nsfw-bot"
    echo "   sudo pkill -9 -f 'python.*bot'"
    echo "   sleep 5"
    echo "   sudo systemctl start nsfw-bot"
    echo ""
else
    echo "✅ No conflict errors found"
fi
echo ""

# Check 3: Count running instances
echo "🔍 Step 3: Checking running bot instances..."
BOT_PROCS=$(ps aux | grep "python.*bot.py" | grep -v grep | wc -l)
if [ $BOT_PROCS -gt 1 ]; then
    echo "❌ WARNING: $BOT_PROCS bot instances running!"
    echo "   Should only be 1."
    ps aux | grep "python.*bot.py" | grep -v grep
    echo ""
    echo "   Fix: sudo pkill -9 -f 'python.*bot'"
else
    echo "✅ Only one bot instance running"
fi
echo ""

# Check 4: Check if handler exists in code
echo "🔍 Step 4: Verifying sticker handler in code..."
if grep -q "filters.Sticker.ALL" /opt/nsfw-bot/bot.py; then
    echo "✅ Sticker handler found in bot.py"
else
    echo "❌ Sticker handler NOT found in bot.py!"
    echo "   Code may not be updated."
fi
echo ""

# Check 5: Check dependencies
echo "🔍 Step 5: Checking required dependencies..."
source /opt/nsfw-bot/.venv/bin/activate

if python -c "import PIL" 2>/dev/null; then
    echo "✅ Pillow installed"
else
    echo "❌ Pillow not installed"
fi

if python -c "import lottie" 2>/dev/null; then
    echo "✅ Lottie installed"
else
    echo "⚠️  Lottie not installed (optional)"
fi

if python -c "import cv2" 2>/dev/null; then
    echo "✅ OpenCV installed"
else
    echo "⚠️  OpenCV not installed (optional)"
fi
echo ""

# Check 6: Recent error logs
echo "🔍 Step 6: Checking recent errors..."
ERRORS=$(journalctl -u nsfw-bot --since "5 minutes ago" | grep -i "error\|exception" | grep -v "Conflict" | wc -l)
if [ $ERRORS -gt 0 ]; then
    echo "⚠️  Found $ERRORS non-conflict errors"
    echo "   Last 5 errors:"
    journalctl -u nsfw-bot --since "5 minutes ago" | grep -i "error\|exception" | grep -v "Conflict" | tail -5
else
    echo "✅ No unusual errors in last 5 minutes"
fi
echo ""

# Summary
echo "=============================================="
echo "Diagnostic Summary"
echo "=============================================="
echo ""

if [ $CONFLICTS -eq 0 ] && [ $BOT_PROCS -eq 1 ]; then
    echo "✅ Bot appears to be running correctly"
    echo ""
    echo "If stickers still not detected:"
    echo "1. Verify feature is ENABLED via /settings"
    echo "2. Make sure you're testing in the SAME chat"
    echo "3. Check settings are per-chat (enable in each group)"
    echo ""
    echo "To add debug logging, edit bot.py and add:"
    echo "  print(f'Sticker received from chat {msg.chat.id}')"
    echo "in the scan_sticker function"
else
    echo "❌ ISSUES FOUND - Follow fixes above!"
fi
echo ""
echo "=============================================="
