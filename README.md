# Spoiler Images Bot

A Telegram bot that adds spoiler tags to images/videos when forwarding them from private messages to a chat.

## Installation

### Python
```bash
pip install -r requirements.txt
python3 spoilerImagesBot.py
```

### Nix
```bash
nix run
```

## Configuration

Set these environment variables:

- `BOT_TOKEN` - Get from [@BotFather](https://t.me/botfather)
- `CHAT_ID` - Target chat ID (negative number for groups)

```bash
export BOT_TOKEN='your_bot_token'
export CHAT_ID='-1001234567890'
```

## Usage

1. Start the bot
2. Send images/videos to the bot privately
3. Bot forwards them with spoiler tags to the configured chat

Supports: photos, videos, animations, and media groups. 