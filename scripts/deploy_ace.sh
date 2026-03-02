#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ] || [ "${2:-}" = "" ]; then
  echo "Usage: $0 <ACE_PUBLIC_IP> <USER: ubuntu|root> [SSH_KEY_PATH]"
  exit 1
fi

IP="$1"
USER="$2"
KEY="${3:-}"
SRC_DIR="$(cd "$(dirname "$0")/.."; pwd)"
DEST_DIR="~/bot-app"

if [ ! -f "$SRC_DIR/.env" ]; then
  echo "Missing $SRC_DIR/.env with TELEGRAM_BOT_TOKEN. Create it before deploying."
  exit 1
fi

SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ServerAliveCountMax=6"
if [ -n "$KEY" ]; then
  SSH="ssh -i \"$KEY\" $SSH_OPTS"
  SCP="scp -i \"$KEY\" $SSH_OPTS"
  RSYNC="rsync -e \"ssh -i $KEY $SSH_OPTS\""
else
  SSH="ssh $SSH_OPTS"
  SCP="scp $SSH_OPTS"
  RSYNC="rsync -e \"ssh $SSH_OPTS\""
fi

echo "Installing base packages on $USER@$IP ..."
eval $SSH "$USER@$IP" 'sudo apt-get update && sudo apt-get install -y rsync git python3-venv python3-pip libgl1 libglib2.0-0'

echo "Syncing code to $DEST_DIR ..."
eval $RSYNC -az --delete "\"$SRC_DIR/\"" "$USER@$IP:$DEST_DIR/"

echo "Pushing .env ..."
eval $SCP "\"$SRC_DIR/.env\"" "$USER@$IP:$DEST_DIR/.env"

echo "Installing and starting systemd service ..."
eval $SSH "$USER@$IP" "bash -lc 'chmod +x $DEST_DIR/scripts/install_systemd.sh $DEST_DIR/scripts/run_bot.sh && sudo bash $DEST_DIR/scripts/install_systemd.sh'"

echo "Service status:"
eval $SSH "$USER@$IP" 'sudo systemctl status telegram-nsfwbot --no-pager || true'
echo "Recent logs:"
eval $SSH "$USER@$IP" 'journalctl -u telegram-nsfwbot -n 100 --no-pager || true'

echo "Done. Your bot is now running on $IP and will auto-start on reboot."
