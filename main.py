import os
import time
import json
import subprocess
import requests

CONFIG_FILE = "config.json"
ROBLOX_PACKAGE = "com.roblox.client"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Error: {CONFIG_FILE} not found!")
        exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def check_root():
    try:
        result = subprocess.run(['su', '-c', 'id'], 
                              capture_output=True, 
                              timeout=5)
        return result.returncode == 0
    except:
        return False

def run_shell_cmd(cmd_str, use_root=False, silent=False):
    if use_root:
        full_cmd = ['su', '-c', cmd_str]
    else:
        full_cmd = cmd_str.split()
    
    try:
        result = subprocess.run(full_cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

def get_roblox_pid():
    success, output = run_shell_cmd(f'pidof {ROBLOX_PACKAGE}', use_root=True, silent=True)
    if success and output:
        return output.split()[0]
    return None

def force_stop_roblox():
    pid = get_roblox_pid()
    if pid:
        run_shell_cmd(f'kill -9 {pid}', use_root=True, silent=True)
        time.sleep(1)
    
    run_shell_cmd(f'am force-stop {ROBLOX_PACKAGE}', use_root=True, silent=True)
    time.sleep(1)

def open_ps_link(link):
    cmd = f'am start -a android.intent.action.VIEW -d "{link}" -p {ROBLOX_PACKAGE}'
    success, _ = run_shell_cmd(cmd, use_root=True, silent=True)
    return success

def is_roblox_running():
    return get_roblox_pid() is not None

def check_user_presence(user_id, roblox_cookie=None):
    url = "https://presence.roblox.com/v1/presence/users"
    payload = {"userIds": [user_id]}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
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

def set_selinux_permissive():
    success, mode = run_shell_cmd('getenforce', use_root=True, silent=True)
    if success and mode.strip() == "Enforcing":
        run_shell_cmd('setenforce 0', use_root=True, silent=True)

def print_header():
    print("\n" + "="*50)
    print("  🎮 Auto Rejoin Roblox Private Server")
    print("="*50 + "\n")

def main():
    print_header()
    
    if not check_root():
        print("❌ Root access required!")
        print("   Please grant root permission when prompted.\n")
        return
    
    print("✓ Root access granted")
    
    set_selinux_permissive()
    
    config = load_config()
    ps_link = config.get("ps_link")
    user_id = config.get("user_id")
    interval = config.get("check_interval", 30)
    restart_delay = config.get("restart_delay", 15)
    roblox_cookie = config.get("roblox_cookie")

    if not ps_link or "YOUR_CODE" in ps_link:
        print("❌ Please configure Private Server link in config.json\n")
        return

    print(f"📋 Configuration:")
    print(f"   • User ID: {user_id}")
    print(f"   • Check Interval: {interval}s")
    print(f"   • Restart Delay: {restart_delay}s")
    print(f"   • Game ID Tracking: {'Enabled ✓' if roblox_cookie else 'Disabled (no cookie)'}")
    print()
    
    print("🔄 Starting Roblox...")
    force_stop_roblox()
    time.sleep(2)
    
    if not open_ps_link(ps_link):
        print("❌ Failed to open Roblox. Please check your setup.\n")
        return
    
    print(f"⏳ Waiting {restart_delay * 2}s for game to load...")
    time.sleep(restart_delay * 2)

    print("🔍 Detecting private server...")
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
                
                force_stop_roblox()
                time.sleep(2)
                open_ps_link(ps_link)
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