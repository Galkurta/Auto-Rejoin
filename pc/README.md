# Auto Rejoin Roblox Private Server (PC)

This Python script monitors your Roblox gameplay and automatically rejoins your Private Server if you get disconnected or switched to a public server.

## Features

- Automatic server switch detection using Game ID tracking
- Auto rejoin Private Server
- Real-time in-game status monitoring
- Clean terminal output
- Cross-platform support (Windows, macOS, Linux)
- Discord webhook notifications with system stats

## Requirements

- Python 3.7+ installed
- Roblox installed on PC
- Internet connection

## Installation

### Windows

1. Install Python (if not installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. Download script to any folder

3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

### macOS/Linux

1. Install Python (if not installed):
   ```bash
   # macOS
   brew install python3
   
   # Linux
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. Download script

3. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

## Configuration

### Quick Setup with Interactive Wizard

Run the interactive setup wizard:

**Windows:**
```cmd
python setup.py
```

**macOS/Linux:**
```bash
python3 setup.py
```

The wizard will guide you through setting up:
- Private Server Link
- Roblox User ID
- Roblox Cookie (optional, for Game ID tracking)
- Discord Webhook (optional, for notifications)

### Manual Configuration

1. Copy `.env.example` to `.env`
2. Edit `.env` with your settings:
   ```
   PS_LINK=your_private_server_link
   USER_ID=your_user_id
   CHECK_INTERVAL=30
   RESTART_DELAY=15
   ROBLOX_COOKIE=your_cookie
   DISCORD_WEBHOOK_URL=your_webhook
   ```

## Usage

### Start the bot

**Windows:**
```cmd
python main.py
```

**macOS/Linux:**
```bash
python3 main.py
```

Keep the terminal window open - the script runs continuously until you press Ctrl+C.

### Discord Notifications

The bot can send notifications to Discord with:
- Status updates (In-Game, rejoining)
- System stats (CPU/RAM usage)
- User info (username, avatar)
- Game details (game name, Game ID)

To enable Discord notifications:
1. Create a Discord webhook
2. Set `DISCORD_WEBHOOK_URL` in `.env`
3. Set `DISCORD_ENABLED=true`

## Troubleshooting

### Roblox Won't Open

- Check Roblox is installed correctly
- Try opening a regular game first
- Check browser is set as default

### Cookie Issues

- Cookie should start with `_|WARNING:`
- Re-login to Roblox if expired
- Use setup wizard for guided cookie extraction

### Game ID Not Detected

- Verify `ROBLOX_COOKIE` is set correctly
- Check `USER_ID` is correct
- Make sure you're logged into Roblox

## Security Notes

- DO NOT share your .env file or ROBLOX_COOKIE
- The cookie gives full access to your account
- Change Roblox password periodically
- The script only sends cookies to Roblox API

## License

Free to use and modify.

---

**Disclaimer**: This script is for educational purposes. Use responsibly and follow Roblox Terms of Service.
