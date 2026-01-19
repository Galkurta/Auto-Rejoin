# Auto Rejoin Roblox Private Server (PC - Windows/Mac/Linux)

This Python script monitors your Roblox gameplay and automatically rejoins your Private Server if you get disconnected or switched to a public server.

## ✨ Features

- ✅ Automatic server switch detection (Private → Public) using Game ID tracking
- ✅ Auto rejoin Private Server within 10-30 seconds
- ✅ Real-time in-game status monitoring
- ✅ Clean terminal output with timestamps
- ✅ **Cross-platform support** (Windows, macOS, Linux)
- ✅ **Automatic cookie extraction** from browsers
- ✅ No root/admin required (unlike Android version)

## 📋 Requirements

- **Python 3.7+** installed
- **Roblox** installed on PC
- **Roblox Cookie** (.ROBLOSECURITY) for Game ID tracking
- Internet connection

## 🔧 Installation

### Windows

1. **Install Python** (if not installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, ✅ check "Add Python to PATH"

2. **Download the script:**

   ```cmd
   # Download and extract to any folder, e.g., C:\AutoRejoin
   ```

3. **Install dependencies:**
   ```cmd
   cd C:\AutoRejoin
   pip install psutil requests
   ```

### macOS

1. **Install Python** (if not installed):

   ```bash
   # Python 3 is usually pre-installed on macOS
   # If not, install via Homebrew:
   brew install python3
   ```

2. **Download the script:**

   ```bash
   # Download and extract to ~/AutoRejoin
   cd ~/AutoRejoin
   ```

3. **Install dependencies:**
   ```bash
   pip3 install psutil requests
   ```

### Linux

1. **Install Python:**

   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **Download the script:**

   ```bash
   git clone https://github.com/Galkurta/Auto-Rejoin.git
   cd Auto-Rejoin
   ```

3. **Install dependencies:**
   ```bash
   pip3 install psutil requests
   ```

## ⚙️ Configuration

### Quick Setup with Interactive Wizard (Recommended) ⭐

**The easiest way to set up!** Just run the interactive setup wizard:

**Windows:**

```cmd
cd C:\Auto-Rejoin
python setup_config.py
```

**macOS/Linux:**

```bash
cd ~/Auto-Rejoin
python3 setup_config.py
```

The wizard will:

- ✅ **Open Roblox.com** automatically for login
- ✅ **Guide you step-by-step** to copy your cookie
- ✅ **Help you get** your Private Server link
- ✅ **Help you find** your User ID
- ✅ **Save everything** to config.json automatically

Just follow the on-screen instructions - no manual file editing needed!

---

### Alternative: Automatic Cookie Extraction

If you prefer automatic extraction (requires being logged into Roblox in browser first):

1. **Login to Roblox** in your browser (Chrome, Edge, Firefox, etc.)
2. **Close ALL browsers** (important!)
3. **Run the cookie extractor:**

   **Windows:**

   ```cmd
   python get_cookie_pc.py
   ```

   **macOS/Linux:**

   ```bash
   python3 get_cookie_pc.py
   ```

   **Note:** This may not work with modern browsers due to cookie encryption. If it fails, use the **Interactive Wizard** or **Manual Method** below.

4. **Edit config.json** to add remaining details (ps_link, user_id)

---

### Manual Setup (Advanced)

<details>
<summary>📖 Click to see manual configuration steps</summary>

If you prefer to manually edit config.json:

1. **Get your Roblox cookie:**
   - Open browser and go to [roblox.com](https://www.roblox.com)
   - Make sure you're logged in
   - Press **F12** to open Developer Tools
   - Go to **Application** (Chrome) or **Storage** (Firefox) tab
   - Click **Cookies** → `https://www.roblox.com`
   - Find the cookie named `.ROBLOSECURITY`
   - Copy the entire value (starts with `_|WARNING:...`)

2. **Get your Private Server link:**
   - Go to your Roblox game
   - Click 'Servers' tab
   - Find your Private Server
   - Click '⋯' → 'Copy Link'

3. **Get your User ID:**
   - Go to your Roblox profile
   - Look at URL: `roblox.com/users/12345678/profile`
   - The number is your User ID

4. **Edit config.json:**
   ```json
   {
     "ps_link": "https://www.roblox.com/share?code=YOUR_CODE&type=Server",
     "user_id": 12345678,
     "check_interval": 10,
     "restart_delay": 30,
     "roblox_cookie": "_|WARNING:-DO-NOT-SHARE-THIS..."
   }
   ```

</details>

## 🚀 Quick Start Guide

**For first-time users, follow these simple steps:**

1. **Install Python & Dependencies:**

   ```bash
   # Windows
   pip install psutil requests

   # macOS/Linux
   pip3 install psutil requests
   ```

2. **Run the Interactive Setup Wizard:**

   ```bash
   # Windows
   python setup_config.py

   # macOS/Linux
   python3 setup_config.py
   ```

3. **Follow the wizard's instructions:**
   - It will open Roblox.com for you
   - Guide you to copy your cookie
   - Help you set up everything else

4. **Start the auto-rejoin script:**

   ```bash
   # Windows
   python main_pc.py

   # macOS/Linux
   python3 main_pc.py
   ```

5. **Done!** Keep the terminal open and play Roblox normally.

---

**Windows:**

```cmd
cd C:\Auto-Rejoin
python main_pc.py
```

**macOS/Linux:**

```bash
cd ~/Auto-Rejoin
python3 main_pc.py
```

**Keep the terminal window open!** The script runs continuously and will auto-rejoin when needed.

## 📊 Normal Output

```
==================================================
  🎮 Auto Rejoin Roblox Private Server (PC)
==================================================

📋 Configuration:
   • User ID: 12345678
   • Check Interval: 10s
   • Restart Delay: 30s
   • Game ID Tracking: Enabled ✓

🔄 Starting Roblox...
⏳ Waiting 60s for game to load...
   (Roblox should open in your browser and launch the game)

🔍 Detecting private server...
✓ Game ID: 49073d8d-d97...

==================================================
  📊 Monitoring Status
==================================================

[14:23:15] 🟢 In-Game (Private Server)
[14:23:25] 🟢 In-Game (Private Server)
[14:23:35] 🔴 Server switched - Rejoining...
           ✓ Rejoined successfully
[14:24:15] 🟢 In-Game (Private Server)
```

## 🔍 How It Works

1. **On Start**: Opens your Private Server link in browser → Roblox launches → Records Game ID
2. **Monitoring**: Every X seconds (check_interval):
   - Checks if Roblox.exe is running
   - Gets current Game ID from Roblox API
   - Compares with Private Server Game ID
3. **Auto Rejoin**: If Game ID changes or Roblox crashes:
   - Kills Roblox process
   - Opens Private Server link again
   - Updates expected Game ID

## 📂 Project Structure

```
AutoRejoin/
├── main_pc.py          # Main auto-rejoin script for PC
├── setup_config.py     # ⭐ Interactive setup wizard (RECOMMENDED)
├── get_cookie_pc.py    # Automatic cookie extractor
├── config.json         # Configuration file (auto-generated)
└── README_PC.md        # This file
```

## 🔧 Scripts Overview

### setup_config.py ⭐ **RECOMMENDED**

Interactive wizard that guides you through the entire setup process:

- Opens Roblox.com automatically
- Step-by-step instructions for cookie extraction
- Helps you get Private Server link
- Finds your User ID
- Saves everything to config.json

**Usage:**

```bash
python setup_config.py
```

### main_pc.py

Main script for auto-rejoining private servers. Monitors game status and automatically rejoins when server changes are detected.

**Usage:**

```bash
python main_pc.py
```

### get_cookie_pc.py

Automatically extracts Roblox cookie from installed browsers (Chrome, Edge, Firefox, etc.).
May not work with modern browsers due to encryption - use setup_config.py instead.

**Usage:**

```bash
python get_cookie_pc.py
```

## 🌐 Supported Browsers

Cookie auto-extraction works with:

### Windows

- ✅ Google Chrome
- ✅ Microsoft Edge
- ✅ Opera / Opera GX
- ✅ Brave
- ✅ Vivaldi
- ✅ Firefox (all profiles)

### macOS

- ✅ Google Chrome
- ✅ Microsoft Edge
- ✅ Opera
- ✅ Brave
- ✅ Firefox

### Linux

- ✅ Google Chrome
- ✅ Chromium
- ✅ Microsoft Edge
- ✅ Opera
- ✅ Brave
- ✅ Firefox

## ❓ Troubleshooting

### Setup Issues

**"No cookie found" when using get_cookie_pc.py:**

- Modern browsers (Chrome 80+) encrypt cookies - this is normal
- **Solution:** Use `setup_config.py` instead (the interactive wizard)
- Or: Use manual extraction method (F12 in browser)

**Can't find my User ID:**

- Run `setup_config.py` - it will open your profile automatically
- Or: Go to roblox.com/users/profile and look at the URL

**Don't know how to get Private Server link:**

- Run `setup_config.py` - it has step-by-step instructions
- Or: Game → Servers tab → Your Private Server → ⋯ → Copy Link

### Cookie Extraction Failed

**Error: "Database locked"**

- ✅ Close ALL browser windows completely
- ✅ Check Task Manager/Activity Monitor for browser processes
- ✅ Kill all browser processes
- ✅ Run script again

**Error: "Cookie is encrypted"**

- Modern browsers (Chrome 80+) encrypt cookies
- Solution: Use manual extraction method (see collapsed section above)
- Or: Try Firefox (stores cookies unencrypted)

**Cookie not found:**

1. Make sure you're logged into Roblox in browser
2. Check you're logged in: see your username on roblox.com
3. Wait 10 seconds after login
4. Close browser
5. Run script again

### Roblox Won't Open

**Link opens but game doesn't launch:**

- Check Roblox is installed correctly
- Try opening a regular game first
- Check Windows/Mac security settings allow Roblox

**Permission errors:**

- No admin/root needed for this script
- If you get permission errors, check antivirus settings

### Script Crashes

**"Module not found" error:**

```bash
pip install psutil requests
# or on macOS/Linux:
pip3 install psutil requests
```

**"Process not found" error:**

- Roblox process name might be different
- Check Task Manager for exact process name
- Edit `ROBLOX_PROCESS_NAMES` in script if needed

### Game ID Not Detected

- Verify `roblox_cookie` is set correctly in config.json
- Cookie should start with `_|WARNING:`
- Check cookie hasn't expired (re-login to Roblox)
- Make sure `user_id` is correct (your Roblox User ID)

## 🔐 Security Notes

1. **DO NOT SHARE** your config.json file or .ROBLOSECURITY cookie!
2. This cookie = your password - anyone with it can access your account
3. Change Roblox password periodically for security
4. Logging out from all devices resets the cookie (requires re-setup)
5. The script only reads cookies, never sends them anywhere except Roblox API

## 📱 Usage Tips

- **Check Interval**:
  - 10s = faster detection, more API calls
  - 30s = slower detection, fewer API calls (recommended)
- **Restart Delay**:
  - Adjust based on your PC/internet speed
  - Faster PC = 20-30s
  - Slower PC/internet = 40-60s
- **Running in Background**:
  - Minimize terminal window (don't close it!)
  - Script runs until you press Ctrl+C
- **Auto-start on Boot**:
  - Windows: Create a .bat file in Startup folder
  - macOS: Create Launch Agent
  - Linux: Create systemd service

## 🔄 Auto-Start Examples

### Windows (Startup Folder)

Create `start_rejoin.bat`:

```bat
@echo off
cd C:\Auto-Rejoin
python main_pc.py
pause
```

Place in: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`

### macOS (Login Items)

Create `start_rejoin.command`:

```bash
#!/bin/bash
cd ~/Auto-Rejoin
python3 main_pc.py
```

Make executable: `chmod +x start_rejoin.command`
Add to System Preferences → Users & Groups → Login Items

### Linux (systemd)

Create `/etc/systemd/system/roblox-rejoin.service`:

```ini
[Unit]
Description=Roblox Auto Rejoin
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/AutoRejoin
ExecStart=/usr/bin/python3 main_pc.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable: `sudo systemctl enable roblox-rejoin.service`

## ⚠️ Limitations

- Script must keep running (don't close terminal)
- Requires active internet connection
- May not work with some VPNs/proxies
- Cookie expires if you change password/logout
- Windows may show security warnings (add to exclusions)

## 🆚 PC vs Android Version

| Feature           | PC Version            | Android Version   |
| ----------------- | --------------------- | ----------------- |
| Root Required     | ❌ No                 | ✅ Yes            |
| Cookie Extraction | 🔒 Encrypted (manual) | ✅ Auto           |
| Process Control   | ✅ Full               | ✅ Full           |
| 24/7 Operation    | ⚠️ PC must stay on    | ✅ Cloud phone    |
| Setup Difficulty  | ⭐⭐ Easy             | ⭐⭐⭐⭐ Advanced |

## 📝 License

Free to use and modify.

## 🤝 Support

For issues or questions, open an issue on GitHub.

---

**Disclaimer**: This script is for educational purposes. Use responsibly and follow Roblox Terms of Service.
