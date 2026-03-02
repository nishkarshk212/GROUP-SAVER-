# NSFW Detection Bot

A Telegram bot that detects and removes NSFW content from your groups.

## Features

- Auto NSFW content detection in messages
- Profile photo scanning for NSFW content
- Automatic message deletion when inappropriate content is detected
- Join/leave notifications to a log channel
- Multilingual support for NSFW word detection
- Drug-related term detection

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables in a `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   LOG_CHANNEL_ID=your_log_channel_id_or_username
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from @BotFather
- `LOG_CHANNEL_ID`: Channel ID or username for join/leave notifications (optional)
- `PFP_NSFWD_ENABLED`: Enable/disable profile photo scanning (default: 1)
- `NSFW_WORD_LANGS`: Languages for NSFW word detection (default: en,ru,zh,es,fr,de,ja,ko,ar,hi,it,pt,pl,cs,nl,sv,tr,th,fa,fil)

## Log Channel Feature

The bot can send notifications to a log channel when it joins or leaves groups. See [SETUP_LOG_CHANNEL.md](SETUP_LOG_CHANNEL.md) for setup instructions.

## Commands

- `/start` - Show bot information
- `/checkpfp` - Check if your profile photo is NSFW
- `/checkbotpfp` - Check if bot's profile photo is NSFW
- `/whereami` - Show where the bot is active (bot owner only)

## License

MIT# GROUP-SAVER-
