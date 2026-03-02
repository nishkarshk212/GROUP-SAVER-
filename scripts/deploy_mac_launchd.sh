#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ] || [ "${2:-}" = "" ] || [ "${3:-}" = "" ]; then
  echo "Usage: $0 <MAC_PUBLIC_IP> <USER> <SSH_KEY_PATH>"
  exit 1
fi

IP="$1"
USER="$2"
KEY="$3"
SRC_DIR="$(cd "$(dirname "$0")/.."; pwd)"
DEST_DIR="~/bot-app"
RSYNC="rsync -az --delete -e \"ssh -i $KEY -o StrictHostKeyChecking=accept-new\""

ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$IP" 'command -v brew >/dev/null 2>&1 || true'
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$IP" 'brew update >/dev/null 2>&1 || true'
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$IP" 'brew list python >/dev/null 2>&1 || brew install -q python || true'

eval $RSYNC "\"$SRC_DIR/\"" "$USER@$IP:$DEST_DIR/"

if [ -f "$SRC_DIR/.env" ]; then
  scp -i "$KEY" -o StrictHostKeyChecking=accept-new "$SRC_DIR/.env" "$USER@$IP:$DEST_DIR/.env"
fi

ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$IP" "bash -lc 'chmod +x $DEST_DIR/scripts/install_launchd.sh $DEST_DIR/scripts/run_bot.sh && $DEST_DIR/scripts/install_launchd.sh'"

ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$IP" "bash -lc 'launchctl list | grep com.telegram.nsfwbot || true'"
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$IP" "bash -lc 'tail -n 40 ~/Library/Logs/telegram-nsfwbot.err.log 2>/dev/null || true'"
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$IP" "bash -lc 'tail -n 40 ~/Library/Logs/telegram-nsfwbot.out.log 2>/dev/null || true'"
