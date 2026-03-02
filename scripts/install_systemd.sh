#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
repo_dir="$(pwd)"
svc_name="telegram-nsfwbot"
user_name="$(id -un)"
sudo -n true 2>/dev/null || true
if command -v apt-get >/dev/null 2>&1; then
  if ! command -v python3 >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3
  fi
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-pip libgl1 libglib2.0-0
fi
unit_path="/etc/systemd/system/${svc_name}.service"
tmp_unit="$(mktemp)"
cat > "$tmp_unit" <<UNIT
[Unit]
Description=Telegram NSFW Bot
After=network.target

[Service]
Type=simple
User=${user_name}
WorkingDirectory=${repo_dir}
ExecStart=/bin/bash ${repo_dir}/scripts/run_bot.sh
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT
sudo mv "$tmp_unit" "$unit_path"
sudo chmod 644 "$unit_path"
sudo systemctl daemon-reload
sudo systemctl enable --now "$svc_name"
sudo systemctl status "$svc_name" --no-pager || true
