#!/bin/bash
cd "/Users/nishkarshkr/Desktop/bot-app" || exit 1
export RUN_NSFW_GUARDIAN=1
export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin"
.venv/bin/python -V >/dev/null 2>&1 || { rm -rf .venv; python3 -m venv .venv; }
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
echo "Starting NSFW Guardian Bot..."
.venv/bin/python nsfw_guardian.py