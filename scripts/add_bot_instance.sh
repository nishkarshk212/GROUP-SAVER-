#!/usr/bin/env bash
set -euo pipefail
if [ "${1:-}" = "" ] || [ "${2:-}" = "" ] || [ "${3:-}" = "" ] || [ "${4:-}" = "" ]; then
  echo "Usage: $0 <ACE_IP> <SERVICE_NAME> <TELEGRAM_BOT_TOKEN> <SSH_KEY_PATH>"
  exit 1
fi
IP="$1"
NAME="$2"
TOKEN="$3"
KEY="$4"
SRC_DIR="$(cd "$(dirname "$0")/.."; pwd)"
DEST_DIR="~/bot-app-${NAME}"
SSH_OPTS="-o StrictHostKeyChecking=accept-new"
ssh -i "$KEY" $SSH_OPTS ubuntu@"$IP" 'sudo apt-get update && sudo apt-get install -y rsync python3-venv python3-pip libgl1 libglib2.0-0'
rsync -az --delete --exclude ".venv" -e "ssh -i $KEY $SSH_OPTS" "$SRC_DIR/" ubuntu@"$IP":"$DEST_DIR"/
ssh -i "$KEY" $SSH_OPTS ubuntu@"$IP" "bash -lc 'printf \"TELEGRAM_BOT_TOKEN=%s\n\" \"$TOKEN\" > $DEST_DIR/.env && chmod 600 $DEST_DIR/.env'"
ssh -i "$KEY" $SSH_OPTS ubuntu@"$IP" "bash -lc 'UNIT=/etc/systemd/system/${NAME}.service; printf \"%s\" \"[Unit]
Description=Telegram Bot ${NAME}
After=network.target
[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bot-app-${NAME}
ExecStart=/bin/bash /home/ubuntu/bot-app-${NAME}/scripts/run_bot.sh
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
\" | sudo tee \$UNIT >/dev/null && sudo chmod 644 \$UNIT && sudo systemctl daemon-reload && sudo systemctl enable --now ${NAME} && sudo systemctl status ${NAME} --no-pager || true'"
