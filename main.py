import os
import time
import json
import subprocess
import requests

CONFIG_FILE = "config.json"
ROBLOX_PACKAGE = "com.roblox.client"

def load_config():
    """Load configuration from json file."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found!")
        exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def check_root():
    """Check if script has root access."""
    try:
        result = subprocess.run(['su', '-c', 'id'], 
                              capture_output=True, 
                              timeout=5)
        return result.returncode == 0
    except:
        return False

def run_shell_cmd(cmd_str, use_root=False, silent=False):
    """
    Run a shell command.
    Returns: (success: bool, output: str)
    """
    if use_root:
        full_cmd = ['su', '-c', cmd_str]
    else:
        full_cmd = cmd_str.split()

    if not silent:
        print(f"  [Exec] {cmd_str}")
    
    try:
        result = subprocess.run(full_cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            if not silent:
                print(f"  > Exit code: {result.returncode}")
            return False, result.stderr.strip()
    except Exception as e:
        if not silent:
            print(f"  > Error: {e}")
        return False, str(e)

def get_roblox_pid():
    """Get Roblox process ID using pidof."""
    success, output = run_shell_cmd(f'pidof {ROBLOX_PACKAGE}', use_root=True, silent=True)
    if success and output:
        return output.split()[0]
    return None

def force_stop_roblox():
    """Force stop Roblox using multiple methods."""
    print("Stopping Roblox...")
    
    pid = get_roblox_pid()
    if pid:
        print(f"  > Found Roblox PID: {pid}")
        run_shell_cmd(f'kill -9 {pid}', use_root=True)
        time.sleep(1)
    
    run_shell_cmd(f'am force-stop {ROBLOX_PACKAGE}', use_root=True, silent=True)

    time.sleep(1)
    print("  > Roblox stopped.")

def open_ps_link(link):
    print(f"Opening Private Server Link...")
    
    cmd = f'am start -a android.intent.action.VIEW -d "{link}" -p {ROBLOX_PACKAGE}'
    success, output = run_shell_cmd(cmd, use_root=True, silent=True)
    
    if success:
        print(f"  ✓ Roblox opened successfully!")
        return True
    else:
        print(f"  ✗ Failed to open Roblox")
        print(f"  Link: {link}")
        return False

def is_roblox_running():
    pid = get_roblox_pid()
    return pid is not None

def check_user_presence(user_id, roblox_cookie=None, verbose=False):
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
            
            if verbose:
                print(f"  API Response: {data}")
            
            user_presences = data.get("userPresences", [])
            if user_presences:
                presence = user_presences[0]
                presence_type = presence.get("userPresenceType")
                game_id = presence.get("gameId")
                
                is_ingame = presence_type == 2
                
                if verbose and not game_id:
                    print(f"  gameId not in API response")
                    if not roblox_cookie:
                        print(f"  No cookie provided - authentication required for gameId")
                
                return is_ingame, game_id
        else:
            if verbose:
                print(f"  API returned status {r.status_code}")
    except Exception as e:
        print(f"  API Error: {e}")
    
    return True, None

def should_rejoin(user_id, expected_game_id, roblox_cookie=None):
    if not is_roblox_running():
        return True, "Process not running", None
    
    is_ingame, current_game_id = check_user_presence(user_id, roblox_cookie)
    
    if not is_ingame:
        return True, "Not in-game", current_game_id

    if expected_game_id and current_game_id and current_game_id != expected_game_id:
        return True, "Server changed (Private→Public)", current_game_id
    
    return False, "OK", current_game_id 

def set_selinux_permissive():
    print("Checking SELinux status...")
    success, mode = run_shell_cmd('getenforce', use_root=True, silent=True)
    
    if success and mode.strip() == "Enforcing":
        print("  > SELinux is Enforcing, setting to Permissive...")
        run_shell_cmd('setenforce 0', use_root=True, silent=True)
        print("  ✓ SELinux set to Permissive (temporary)")
    else:
        print(f"  > SELinux: {mode}")

def main():
    print("=" * 50)
    print("  Auto Rejoin Roblox Script (Termux/Root)")
    print("=" * 50)
    
    if not check_root():
        print("Error: Root access required!")
        print("   Grant root permission when prompted.")
        return
    
    set_selinux_permissive()

    config = load_config()
    ps_link = config.get("ps_link")
    user_id = config.get("user_id")
    interval = config.get("check_interval", 30)
    restart_delay = config.get("restart_delay", 15)
    roblox_cookie = config.get("roblox_cookie")

    if not ps_link or "YOUR_CODE" in ps_link:
        print("Warning: Configure Private Server link in config.json first!")
        return

    print(f"\n Configuration:")
    print(f"   User ID: {user_id}")
    print(f"   Check Interval: {interval}s")
    print(f"   Restart Delay: {restart_delay}s")
    if roblox_cookie:
        print(f"   Cookie: Set ✓ (Game ID tracking enabled)")
    else:
        print(f"   Cookie: Not set (Basic presence checking only)")
    print(f"\n{'='*50}\n")
    
    force_stop_roblox()
    time.sleep(2)
    open_ps_link(ps_link)
    
    print(f"\nWaiting {restart_delay * 2}s for game to load...\n")
    time.sleep(restart_delay * 2)

    print("Getting private server game ID...")
    _, private_game_id = check_user_presence(user_id, roblox_cookie, verbose=True)
    if private_game_id:
        print(f"Private server game ID: {private_game_id}\n")
    else:
        print("Warning: Could not get game ID from API.")
        if not roblox_cookie:
            print("   Add 'roblox_cookie' to config.json for Game ID tracking.")
        print("   Script will fall back to basic presence checking only.\n")

    loop_count = 0
    expected_game_id = private_game_id
    
    while True:
        try:
            loop_count += 1
            
            print(f"[Check #{loop_count}] ", end="")
            
            needs_rejoin, reason, current_game_id = should_rejoin(user_id, expected_game_id, roblox_cookie)
            
            if needs_rejoin:
                print(f"{reason} - Rejoining...")
                if current_game_id and expected_game_id:
                    print(f"   Game ID: {expected_game_id[:8]}... → {current_game_id[:8]}...")
                
                force_stop_roblox()
                time.sleep(2)
                open_ps_link(ps_link)
                print(f"Waiting {restart_delay * 2}s...")
                time.sleep(restart_delay * 2)
                
                _, new_game_id = check_user_presence(user_id, roblox_cookie)
                if new_game_id:
                    expected_game_id = new_game_id
                    print(f"Rejoined with game ID: {new_game_id[:8]}...")
            else:
                if current_game_id and expected_game_id:
                    match_status = "✓" if current_game_id == expected_game_id else "✗"
                    print(f"In-Game {match_status} (ID: {current_game_id[:8]}...)")
                else:
                    print(f"In-Game")
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n\nExiting script...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()