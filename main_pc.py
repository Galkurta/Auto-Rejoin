import os
import time
import json
import psutil
import subprocess
import webbrowser
import requests
from pathlib import Path

CONFIG_FILE = "config.json"
ROBLOX_PROCESS_NAMES = ["RobloxPlayerBeta.exe", "RobloxPlayer.exe"]

def print_header():
    print("\n" + "="*50)
    print("  🎮 Auto Rejoin Roblox Private Server (PC)")
    print("="*50 + "\n")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Error: {CONFIG_FILE} not found!")
        print("   Creating template config.json...")
        create_template_config()
        exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def create_template_config():
    """Create a template config file."""
    template = {
        "ps_link": "https://www.roblox.com/share?code=YOUR_CODE&type=Server",
        "user_id": 0,
        "check_interval": 10,
        "restart_delay": 30,
        "roblox_cookie": ""
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(template, f, indent=2)
    print(f"✓ Created {CONFIG_FILE}")

def find_roblox_process():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] in ROBLOX_PROCESS_NAMES:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def is_roblox_running():
    return find_roblox_process() is not None

def kill_roblox():
    killed = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] in ROBLOX_PROCESS_NAMES:
                proc.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if killed:
        time.sleep(2)
    
    return killed

def open_private_server(link):
    try:
        webbrowser.open(link)
        return True
    except Exception as e:
        print(f"❌ Failed to open link: {e}")
        return False

def check_user_presence(user_id, roblox_cookie=None):
    url = "https://presence.roblox.com/v1/presence/users"
    payload = {"userIds": [user_id]}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    cookies = {}
    if roblox_cookie:
        cookies[".ROBLOSECURITY"] = roblox_cookie
    
    try:
        r = requests.post(url, json=payload, headers=headers, cookies=cookies, timeout=10)
        if r.status_code == 200:
            data = r.json()
            user_presences = data.get("userPresences", [])
            if user_presences:
                presence = user_presences[0]
                presence_type = presence.get("userPresenceType")
                game_id = presence.get("gameId")
                is_ingame = presence_type == 2
                return is_ingame, game_id
    except Exception as e:
        pass
    
    return True, None

def should_rejoin(user_id, expected_game_id, roblox_cookie=None):
    if not is_roblox_running():
        return True, "Process stopped", None
    
    is_ingame, current_game_id = check_user_presence(user_id, roblox_cookie)
    
    if not is_ingame:
        return True, "Not in-game", current_game_id

    if expected_game_id and current_game_id and current_game_id != expected_game_id:
        return True, "Server switched", current_game_id
    
    return False, "OK", current_game_id

def main():
    print_header()
    
    config = load_config()
    ps_link = config.get("ps_link")
    user_id = config.get("user_id")
    interval = config.get("check_interval", 30)
    restart_delay = config.get("restart_delay", 15)
    roblox_cookie = config.get("roblox_cookie")

    if not ps_link or "YOUR_CODE" in ps_link:
        print("❌ Please configure Private Server link in config.json\n")
        return

    if user_id == 0:
        print("❌ Please set your user_id in config.json\n")
        return

    print(f"📋 Configuration:")
    print(f"   • User ID: {user_id}")
    print(f"   • Check Interval: {interval}s")
    print(f"   • Restart Delay: {restart_delay}s")
    print(f"   • Game ID Tracking: {'Enabled ✓' if roblox_cookie else 'Disabled (no cookie)'}")
    print()
    
    if is_roblox_running():
        print("⚠ Roblox is already running")
        print("   Stopping current instance...")
        kill_roblox()
        time.sleep(2)
    
    print("🔄 Starting Roblox...")
    if not open_private_server(ps_link):
        print("❌ Failed to open Roblox. Check your setup.\n")
        return
    
    print(f"⏳ Waiting {restart_delay * 2}s for game to load...")
    print("   (Roblox should open in your browser and launch the game)")
    time.sleep(restart_delay * 2)

    print("\n🔍 Detecting private server...")
    _, private_game_id = check_user_presence(user_id, roblox_cookie)
    
    if private_game_id:
        print(f"✓ Game ID: {private_game_id[:12]}...")
    else:
        if roblox_cookie:
            print("⚠ Warning: Could not get Game ID (check cookie)")
        else:
            print("⚠ Game ID tracking disabled (add cookie to config.json)")
    
    print("\n" + "="*50)
    print("  📊 Monitoring Status")
    print("="*50 + "\n")

    loop_count = 0
    expected_game_id = private_game_id
    
    while True:
        try:
            loop_count += 1
            timestamp = time.strftime("%H:%M:%S")
            
            needs_rejoin, reason, current_game_id = should_rejoin(
                user_id, expected_game_id, roblox_cookie
            )
            
            if needs_rejoin:
                print(f"[{timestamp}] 🔴 {reason} - Rejoining...")
                
                kill_roblox()
                time.sleep(2)
                open_private_server(ps_link)
                time.sleep(restart_delay * 2)
                
                _, new_game_id = check_user_presence(user_id, roblox_cookie)
                if new_game_id:
                    expected_game_id = new_game_id
                    print(f"           ✓ Rejoined successfully")
                else:
                    print(f"           ⚠ Rejoined (Game ID unavailable)")
            else:
                if current_game_id and expected_game_id:
                    if current_game_id == expected_game_id:
                        print(f"[{timestamp}] 🟢 In-Game (Private Server)")
                    else:
                        print(f"[{timestamp}] 🟡 In-Game (Unknown server)")
                else:
                    print(f"[{timestamp}] 🟢 In-Game")
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n" + "="*50)
            print("  👋 Script stopped by user")
            print("="*50 + "\n")
            break
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()