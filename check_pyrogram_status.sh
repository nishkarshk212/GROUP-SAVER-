#!/bin/bash
# Quick Status Check for Pyrogram Bot

echo "=============================================="
echo "Pyrogram Bot - Quick Status Check"
echo "=============================================="
echo ""

# Check services
echo "1. Bot Service:"
if systemctl is-active pyrogram-nsfw-bot > /dev/null 2>&1; then
    echo "   ✅ ACTIVE (running)"
else
    echo "   ❌ INACTIVE or FAILED"
fi

echo ""
echo "2. Worker Service:"
if systemctl is-active pyrogram-nsfw-worker > /dev/null 2>&1; then
    echo "   ✅ ACTIVE (running)"
else
    echo "   ⚠️  INACTIVE (normal if no tasks queued)"
fi

echo ""
echo "3. Redis:"
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ PONG (responding)"
else
    echo "   ❌ NOT RESPONDING"
fi

echo ""
echo "4. Config:"
cd /opt/nsfw-bot/pyrogram_bot
if python -c "from config import API_ID, BOT_TOKEN" 2>/dev/null; then
    echo "   ✅ LOADED OK"
else
    echo "   ❌ CONFIG ERROR"
fi

echo ""
echo "5. Session Files:"
if ls *.session* > /dev/null 2>&1; then
    echo "   ⚠️  Found (may be locked)"
    ls -lh *.session* 2>/dev/null | head -3
else
    echo "   ✅ No session files (clean)"
fi

echo ""
echo "6. Bot Processes:"
PROC_COUNT=$(ps aux | grep "python.*bot.py" | grep -v grep | wc -l)
if [ $PROC_COUNT -eq 1 ]; then
    echo "   ✅ Exactly 1 process running"
elif [ $PROC_COUNT -gt 1 ]; then
    echo "   ⚠️  WARNING: $PROC_COUNT processes (should be 1)"
else
    echo "   ❌ No bot process found"
fi

echo ""
echo "=============================================="
echo "Quick Commands:"
echo "=============================================="
echo ""
echo "Restart bot:"
echo "  systemctl restart pyrogram-nsfw-bot"
echo ""
echo "Clear sessions:"
echo "  cd /opt/nsfw-bot/pyrogram_bot && rm -f *.session*"
echo ""
echo "View logs:"
echo "  journalctl -u pyrogram-nsfw-bot -f"
echo ""
echo "Test manually:"
echo "  cd /opt/nsfw-bot/pyrogram_bot && source .venv/bin/activate && python bot.py"
echo ""
echo "=============================================="
