#!/bin/bash
set -e
cd "$(dirname "$0")/.."
repo_dir="$(pwd)"
plist_path="$HOME/Library/LaunchAgents/com.telegram.nsfwbot.plist"
logs_dir="$HOME/Library/Logs"
mkdir -p "$HOME/Library/LaunchAgents" "$logs_dir"
cat > "$plist_path" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.telegram.nsfwbot</string>
  <key>WorkingDirectory</key>
  <string>${HOME}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/env</string>
    <string>bash</string>
    <string>${repo_dir}/scripts/run_bot.sh</string>
  </array>
  <key>KeepAlive</key>
  <true/>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${logs_dir}/telegram-nsfwbot.out.log</string>
  <key>StandardErrorPath</key>
  <string>${logs_dir}/telegram-nsfwbot.err.log</string>
</dict>
</plist>
PLIST
launchctl remove com.telegram.nsfwbot 2>/dev/null || true
launchctl unload "$plist_path" 2>/dev/null || true
launchctl load "$plist_path"
launchctl start com.telegram.nsfwbot
