# Setting up Log Channel for Bot Join/Leave Notifications

## Overview
The bot can send notifications to a designated Telegram channel when it joins or leaves groups/channels. This helps monitor where your bot is active.

## Setup Instructions

### 1. Prepare Your Log Channel
- Create a Telegram channel where you want to receive join/leave notifications
- Add your bot as an administrator to this channel (required to send messages)
- Obtain the channel's ID or username

### 2. Get Channel ID
You have two options for identifying your log channel:

#### Option A: Channel Username
- If your channel username is `@my_bot_logs`, use `@my_bot_logs` as the ID

#### Option B: Numeric Channel ID
- Use a bot like @userinfobot to get the numeric ID of your channel
- Channel IDs are typically negative numbers like `-1001234567890`

### 3. Configure Environment Variable
Update your `.env` file with the channel identifier:

```
LOG_CHANNEL_ID=@your_channel_username
```
OR
```
LOG_CHANNEL_ID=-1001234567890
```

### 4. Invite Link Limitation
Note: The invite link format (like `https://t.me/+u0QG9eqTor1lZDQ1`) cannot be used directly. You must add the bot to the channel and use either the username (with @) or numeric ID.

## Expected Behavior
- When the bot joins a new group/channel, it will send a message to your log channel
- When the bot leaves or is removed from a group/channel, it will send a notification
- Messages will include the chat title, ID, and type