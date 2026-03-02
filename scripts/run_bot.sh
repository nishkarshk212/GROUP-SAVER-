#!/bin/bash
set -e
cd "/Users/nishkarshkr/Desktop/bot-app" || exit 1
export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin"
.venv/bin/python -V >/dev/null 2>&1 || { rm -rf .venv; python3 -m venv .venv; }
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt

# Check if there's a specific bot to run via environment variable, otherwise run default
if [ "$RUN_NSFW_GUARDIAN" = "1" ]; then
  echo "Starting NSFW Guardian Bot..."
  exec .venv/bin/python nsfw_guardian.py
else
  echo "Starting Default NSFW Detection Bot..."
  exec .venv/bin/python bot.py
fi