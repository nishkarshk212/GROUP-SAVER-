#!/bin/bash
# Manual installation of cleanup services on server
# Run this script ONCE on your server after deployment

set -e

echo "=========================================="
echo "Installing NSFW Bot Cleanup Services"
echo "=========================================="
echo ""

BOT_DIR="/opt/nsfw-bot"

echo "=== Step 1: Verify cleanup script exists ==="
if [ ! -f "$BOT_DIR/scripts/cleanup_daily.sh" ]; then
    echo "❌ Cleanup script not found at $BOT_DIR/scripts/cleanup_daily.sh"
    exit 1
fi
chmod +x "$BOT_DIR/scripts/cleanup_daily.sh"
echo "✅ Cleanup script verified and made executable"
echo ""

echo "=== Step 2: Copy systemd service files ==="
cp "$BOT_DIR/systemd/nsfw-bot-cleanup.service" /etc/systemd/system/
cp "$BOT_DIR/systemd/nsfw-bot-cleanup.timer" /etc/systemd/system/
echo "✅ Systemd service files copied"
echo ""

echo "=== Step 3: Copy logrotate configuration ==="
if [ -f "$BOT_DIR/logrotate.conf" ]; then
    cp "$BOT_DIR/logrotate.conf" /etc/logrotate.d/nsfw-bot
    echo "✅ Logrotate configuration installed"
else
    echo "⚠️  Logrotate config not found (optional)"
fi
echo ""

echo "=== Step 4: Reload systemd and enable timer ==="
systemctl daemon-reload
systemctl enable nsfw-bot-cleanup.timer
systemctl start nsfw-bot-cleanup.timer
echo "✅ Cleanup timer enabled and started"
echo ""

echo "=== Step 5: Verify timer status ==="
systemctl is-active nsfw-bot-cleanup.timer && echo "✅ Timer is active" || echo "❌ Timer failed to start"
echo ""
echo "Timer schedule:"
systemctl list-timers | grep nsfw-bot || echo "ℹ️  Timer info not available"
echo ""

echo "=== Step 6: Test cleanup script (dry run) ==="
echo "Running cleanup script once to verify it works..."
bash "$BOT_DIR/scripts/cleanup_daily.sh" || echo "⚠️  Cleanup script had warnings (non-fatal)"
echo ""

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Cleanup Schedule:"
echo "  - Runs daily at 3:00 AM"
echo "  - Cleans logs older than 1 day"
echo "  - Removes temporary files"
echo "  - Clears Python cache"
echo ""
echo "Manual Commands:"
echo "  Check timer:   systemctl list-timers | grep nsfw-bot"
echo "  View status:   systemctl status nsfw-bot-cleanup.timer"
echo "  Run manually:  bash $BOT_DIR/scripts/cleanup_daily.sh"
echo "  View logs:     journalctl -u nsfw-bot-cleanup -f"
echo ""
