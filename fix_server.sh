#!/bin/bash
# Fix script to run on server

echo "=== Fixing NSFW Bot on Server ==="

cd /opt/nsfw-bot

# Check if .env exists and has correct token
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'ENVEOF'
TELEGRAM_BOT_TOKEN=8587720230:AAEHakInRNby8me1WtxsoQ_JUbhTJAVJL6s
LOG_CHANNEL_ID=@log_x_bott
PFP_NSFWD_ENABLED=0
NSFW_WORD_LANGS=en,ru,zh,es,fr,de,ja,ko,ar,hi,it,pt,pl,cs,nl,sv,tr,th,fa,fil
ENVEOF
    echo "✅ .env file created"
else
    echo "Checking .env content..."
    cat .env
    
    # Check if token is correct
    if ! grep -q "8587720230:AAEHakInRNby8me1WtxsoQ_JUbhTJAVJL6s" .env; then
        echo "⚠️  Token appears to be incorrect. Updating..."
        sed -i 's/TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=8587720230:AAEHakInRNby8me1WtxsoQ_JUbhTJAVJL6s/' .env
    else
        echo "✅ Token looks correct"
    fi
fi

echo ""
echo "=== Restarting bot service ==="
systemctl daemon-reload
systemctl restart nsfw-bot

sleep 3

echo ""
echo "=== Checking status ==="
systemctl status nsfw-bot --no-pager | head -15

echo ""
echo "=== Recent logs ==="
journalctl -u nsfw-bot -n 20 --no-pager

echo ""
echo "=== Done! ==="
