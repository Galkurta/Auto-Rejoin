# Auto Rejoin Roblox Private Server (Rooted Android)

This Python script monitors your gameplay status and automatically rejoins a Private Server if a switch to a public server or a disconnection is detected.

## ✨ Features

- ✅ Automatic server switch detection (Private → Public) using Game ID tracking
- ✅ Auto rejoin Private Server within 10-30 seconds
- ✅ Real-time in-game status monitoring
- ✅ SELinux auto-configuration for maximum compatibility
- ✅ Clean terminal output with timestamps
- ✅ **New:** Auto cookie extractor script included
- ✅ Support for Cloud Phones & PC Emulators (with root)

## 📋 Requirements

1. **Rooted Android Device** (Required - Magisk/KernelSU)
   - Physical Android phone/tablet
   - Cloud phone (Redfinger, NOX Cloud, etc.)
   - PC Emulator (BlueStacks, LDPlayer, NoxPlayer, MEmu - with root enabled)
2. **Termux** app installed (Recommended: **F-Droid version**)
   - ⚠️ **Important:** Do not use the Google Play Store version (it is outdated).
   - Download from [F-Droid](https://f-droid.org/packages/com.termux/) or [GitHub Releases](https://github.com/termux/termux-app/releases).
3. **Roblox** app installed
4. **Roblox Cookie** (.ROBLOSECURITY) for Game ID tracking

## 🔧 Installation

### 1. Setup Termux

Open Termux and run:

```bash
pkg update && pkg upgrade
pkg install python
pip install requests
```

### 2. Setup Storage Permission

```bash
termux-setup-storage
```

Allow access when prompted.

### 3. Download/Copy Script

Save the script in an accessible folder (e.g., `/sdcard`):

```bash
git clone https://github.com/Galkurta/AutoRejoin.git
cd AutoRejoin
```

## ⚙️ Configuration (`config.json`)

### 1. Get Private Server Link

- Open your Roblox Private Server
- Copy the share link (example: `https://www.roblox.com/share?code=XXXXX&type=Server`)

### 2. Get User ID

- Open your Roblox profile
- User ID is in the URL (example: `roblox.com/users/12345678/profile`)

### 3. Get Roblox Cookie (.ROBLOSECURITY)

**IMPORTANT: This cookie is highly sensitive! Do not share it with anyone!**

#### Option A: Automatic Extraction (Recommended)

Run the included helper script to extract the cookie from your installed browser (Chrome, Edge, Firefox, etc.):

```bash
python getcookie.py
```

If successful, it will automatically update your `config.json`.

#### Option B: Manual Method

**On Desktop/Mobile Browser:**

1. Open [roblox.com](https://www.roblox.com) and login
2. Open Developer Tools (F12)
3. Select **Application** (Chrome) or **Storage** (Firefox) tab
4. Click **Cookies** → `https://www.roblox.com`
5. Find the cookie named `.ROBLOSECURITY`
6. Copy the entire cookie value (starting from `_|WARNING:...`)

#### On Chrome Android:

1. Install an extension like "Cookie Editor" or use `chrome://inspect`
2. Open roblox.com and login
3. Open Cookie Editor and copy `.ROBLOSECURITY`

### 4. Edit config.json

```json
{
  "ps_link": "https://www.roblox.com/share?code=YOUR_CODE&type=Server",
  "user_id": 12345678,
  "check_interval": 10,
  "restart_delay": 30,
  "roblox_cookie": "_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_YOUR_COOKIE_HERE"
}
```

**Parameters:**

- `ps_link`: Your Private Server Link (replaces `ps_link`)
- `user_id`: Your Roblox User ID
- `check_interval`: Check interval in seconds (10 = check every 10 seconds)
- `restart_delay`: Wait time for game loading in seconds (30 = wait 30 seconds)
- `roblox_cookie`: .ROBLOSECURITY Cookie for Game ID tracking

## 🚀 How to Run

### Method 1: Using su (Recommended)

```bash
cd /sdcard/Auto-Rejoin
su
python main.py
```

### Method 2: Using tsu (Alternative)

```bash
cd /sdcard/Auto-Rejoin
tsu
python main.py
```

**Ensure you grant Root permissions when the Magisk/KernelSU popup appears!**

## 📊 Normal Output

```
==================================================
  🎮 Auto Rejoin Roblox Private Server
==================================================

✓ Root access granted
📋 Configuration:
   • User ID: 12345678
   • Check Interval: 10s
   • Restart Delay: 30s
   • Game ID Tracking: Enabled ✓

🔄 Starting Roblox...
⏳ Waiting 60s for game to load...
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

This script uses **Game ID Tracking** to detect server switches:

1. **On Start**: The script opens the Private Server and records its Game ID.
2. **Monitoring**: Every X seconds (according to `check_interval`), the script:
   - Checks if Roblox is running.
   - Checks the current Game ID via the Roblox Presence API.
   - Compares it with the Private Server's Game ID.
3. **Auto Rejoin**: If the Game ID changes (moved to a public server), the script will:
   - Force stop Roblox.
   - Reopen the Private Server link.
   - Update the expected Game ID.

## 💻 Support for Cloud Phone & PC Emulator

### Cloud Phone (Redfinger, NOX Cloud, etc.)

✅ **Compatible** - The script works on cloud phones provided:

1. Cloud phone has root access.
2. Termux can be installed.
3. Stable internet connection.

**Setup:**

1. Install Termux on the cloud phone.
2. Follow the installation instructions above.
3. Run the script as usual.

**Benefits:**

- Runs 24/7 without relying on a physical device.
- Does not drain your main device's battery.
- Accessible from anywhere.

### PC Emulator (BlueStacks, LDPlayer, NoxPlayer, MEmu)

✅ **Compatible with root requirement** - Choose an emulator that supports root:

| Emulator         | Root Support    | Recommended            |
| ---------------- | --------------- | ---------------------- |
| **LDPlayer**     | ✅ Built-in     | ⭐⭐⭐⭐⭐ Recommended |
| **NoxPlayer**    | ✅ Built-in     | ⭐⭐⭐⭐               |
| **MEmu**         | ✅ Built-in     | ⭐⭐⭐⭐               |
| **BlueStacks 5** | ⚠️ Needs Magisk | ⭐⭐⭐                 |

**How to Enable Root:**

**LDPlayer:**

1. Open Settings → Other Settings
2. Enable "Root permission"
3. Restart emulator

**NoxPlayer:**

1. Click gear icon (Settings)
2. General tab
3. Enable "Root startup"
4. Restart emulator

**MEmu:**

1. Open Settings
2. Enable "ROOT"
3. Restart emulator

**BlueStacks 5:**

1. Install Magisk via recovery
2. Follow Magisk installation guide
3. More complex - not recommended for beginners

### Performance & Recommendations

**Physical Device:**

- Best for daily use.
- Battery efficient with split `check_interval` 30s.
- Most stable.

**Cloud Phone:**

- Best for 24/7 operation.
- Independent of physical device.
- Requires cloud service subscription.

**PC Emulator:**

- Best for testing/development.
- Can run multiple instances.
- High RAM usage.

**Tip:** For 24/7 operation, use a Cloud Phone or a PC that is always on with an emulator.

### Cookie Extraction Failed

If `getcookie.py` can't find your cookie:

1. **Check installed browsers:** `su -c "pm list packages | grep -E 'chrome|firefox|edge'"`
2. **Verify login:** Ensure you are logged into Roblox in that browser.
3. **Try manual extraction:** Use the manual method described in Configuration.

### SELinux Error

```bash
# Check status
su -c "getenforce"

# Manually set to Permissive
su -c "setenforce 0"
```

### Game ID Not Detected

- Ensure `roblox_cookie` is correctly set in config.json.
- Cookie must be complete and valid (login to browser to verify).
- Avoid spaces or extra characters when copy-pasting.

### Roblox Not Opening

```bash
# Manual test
su -c "am start -a android.intent.action.VIEW -d 'YOUR_PS_LINK' -p com.roblox.client"

# Or test with monkey
su -c "monkey -p com.roblox.client 1"
```

### Script Crash/Error

- Ensure Python and requests are installed: `pip install requests`
- Check root permission: `su -c "id"`
- Check error logs for debugging.

## ⚠️ Security Notes

1. **DO NOT SHARE** your `config.json` file or `.ROBLOSECURITY` cookie!
2. This cookie is equivalent to a password - anyone with it can log in as you.
3. Change your Roblox password periodically for security.
4. Logging out from all devices will reset the cookie (requires re-setup).

## 📱 Usage Tips

- Set `check_interval` to 10 for fast detection (more API calls).
- Set `check_interval` to 30 to save battery (slower detection).
- `restart_delay` should be 30-60 seconds depending on your game loading speed.
- The script runs continuously until manually stopped (Ctrl+C).

## 🔄 Auto-Start on Boot (Optional)

To run the script automatically on device boot, use Termux:Boot or Tasker with root.

## 📝 License

Free to use and modify.

## 🤝 Support

If there are issues or questions, open an issue in this repository.

---

**Disclaimer**: This script is for educational purposes. Use wisely and follow Roblox Terms of Service.
