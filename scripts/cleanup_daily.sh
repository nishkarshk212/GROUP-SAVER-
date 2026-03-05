#!/bin/bash
#
# Daily Cleanup Script for NSFW Bot
# Cleans up old logs, temporary files, and unused data
# Run this script daily via cron or systemd timer
#

set -e

echo "=========================================="
echo "NSFW Bot - Daily Cleanup"
echo "=========================================="
echo "Started at: $(date)"
echo ""

BOT_DIR="/opt/nsfw-bot"
LOG_DIR="/var/log/nsfw-bot"
TEMP_DIR="/tmp/nsfw-bot"
MAX_LOG_AGE_DAYS=1
MAX_TEMP_AGE_DAYS=1

echo "=== Step 1: Clean old systemd journal logs ==="
# Keep only last 1 day of logs for the bot service
journalctl --vacuum-time=1d
echo "✅ Journal logs cleaned (keeping last 1 day)"
echo ""

echo "=== Step 2: Clean old log files ==="
# Find and remove log files older than 1 day
if [ -d "$LOG_DIR" ]; then
    find "$LOG_DIR" -type f -name "*.log" -mtime +$MAX_LOG_AGE_DAYS -delete
    echo "✅ Old log files removed from $LOG_DIR"
else
    echo "⚠️  Log directory $LOG_DIR does not exist"
fi
echo ""

echo "=== Step 3: Clean temporary files ==="
# Clean temporary files created by the bot
if [ -d "$TEMP_DIR" ]; then
    find "$TEMP_DIR" -type f -mtime +$MAX_TEMP_AGE_DAYS -delete
    echo "✅ Temporary files older than 1 day removed"
else
    echo "ℹ️  Temp directory $TEMP_DIR does not exist (nothing to clean)"
fi
echo ""

echo "=== Step 4: Clean Python cache ==="
# Remove Python bytecode cache
find "$BOT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BOT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Python cache cleaned"
echo ""

echo "=== Step 5: Clean old naughty-words cache (optional) ==="
# Keep naughty words JSON files but you can clean if needed
NAUGHTY_WORDS_DIR="$BOT_DIR/data/naughty-words"
if [ -d "$NAUGHTY_WORDS_DIR" ]; then
    # Don't delete these as they're needed for profanity detection
    # Just report size
    SIZE=$(du -sh "$NAUGHTY_WORDS_DIR" 2>/dev/null | cut -f1)
    COUNT=$(find "$NAUGHTY_WORDS_DIR" -type f -name "*.json" | wc -l)
    echo "ℹ️  Naughty words cache: $COUNT files, $SIZE"
fi
echo ""

echo "=== Step 6: Restart bot service (optional) ==="
# Uncomment the line below if you want to restart the bot after cleanup
# systemctl restart nsfw-bot
echo "ℹ️  Service restart skipped (uncomment in script to enable)"
echo ""

echo "=== Step 7: Show disk usage ==="
echo "Current bot directory size:"
du -sh "$BOT_DIR" 2>/dev/null || echo "Cannot access $BOT_DIR"
echo ""

echo "=========================================="
echo "✅ Cleanup Complete!"
echo "=========================================="
echo "Finished at: $(date)"
echo ""
echo "Summary:"
echo "  - Journal logs: Kept last 1 day"
echo "  - Log files: Removed files older than 1 day"
echo "  - Temp files: Removed files older than 1 day"
echo "  - Python cache: Cleaned"
echo ""
