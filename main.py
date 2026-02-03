import os
import re
import time
import subprocess
import requests
import sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv
import psutil

load_dotenv()

ROBLOX_PACKAGE = "com.roblox.client"


class DiscordNotifier:
    def __init__(self, user_id):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.webhook_name = os.getenv("DISCORD_WEBHOOK_NAME", "Auto Rejoin Bot (Android)")
        self.mention_user = os.getenv("DISCORD_MENTION_USER", "").strip()
        self.enabled = (
            os.getenv("DISCORD_ENABLED", "false").lower() == "true"
            and self.webhook_url
            and "YOUR_WEBHOOK_URL" not in self.webhook_url
        )
        self.notify_on_start = (
            os.getenv("DISCORD_NOTIFY_ON_START", "true").lower() == "true"
        )
        self.notify_on_rejoin = (
            os.getenv("DISCORD_NOTIFY_ON_REJOIN", "true").lower() == "true"
        )
        self.notify_on_error = (
            os.getenv("DISCORD_NOTIFY_ON_ERROR", "true").lower() == "true"
        )
        self.user_id = user_id
        self.username, self.display_name = get_user_info(user_id)
        self.avatar_url = get_user_avatar(user_id) if self.username else None

    def format_mention(self):
        if not self.mention_user:
            return ""

        if self.mention_user.startswith("<@"):
            return self.mention_user
        elif self.mention_user.isdigit():
            return f"<@{self.mention_user}>"
        else:
            return self.mention_user

    def get_system_info(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            ram_used_gb = ram.used / (1024**3)
            ram_total_gb = ram.total / (1024**3)

            return {
                "cpu_percent": cpu_percent,
                "ram_percent": ram_percent,
                "ram_used_gb": round(ram_used_gb, 2),
                "ram_total_gb": round(ram_total_gb, 2),
            }
        except Exception as e:
            print(f"Warning: Failed to get system info: {e}")
            return {
                "cpu_percent": 0.0,
                "ram_percent": 0.0,
                "ram_used_gb": 0.0,
                "ram_total_gb": 0.0,
            }

    def send_embed(self, title, description, color, fields=None, show_user_info=True):
        if not self.enabled:
            return False

        system_info = self.get_system_info()

        if not fields:
            fields = []

        fields.append(
            {
                "name": "CPU Usage",
                "value": f"{system_info['cpu_percent']}%",
                "inline": True,
            }
        )
        fields.append(
            {
                "name": "RAM Usage",
                "value": f"{system_info['ram_used_gb']}/{system_info['ram_total_gb']} GB ({system_info['ram_percent']}%)",
                "inline": True,
            }
        )

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {"text": self.webhook_name},
            "fields": fields,
        }

        if show_user_info and self.username:
            embed["author"] = {
                "name": f"{self.display_name} (@{self.username})",
                "icon_url": self.avatar_url,
            }

        payload = {"username": self.webhook_name, "embeds": [embed]}

        mention = self.format_mention()
        if mention:
            payload["content"] = mention

        try:
            requests.post(self.webhook_url, json=payload, timeout=5)
            return True
        except:
            return False

    def notify_start(self, user_id, check_interval):
        if not self.notify_on_start:
            return
        fields = [
            {"name": "User ID", "value": str(user_id), "inline": True},
            {"name": "Check Interval", "value": f"{check_interval}s", "inline": True},
        ]
        self.send_embed(
            "Auto Rejoin Started",
            "Monitoring private server connection",
            3447003,
            fields,
        )

    def notify_rejoin(self, reason, game_id=None):
        if not self.notify_on_rejoin:
            return
        description = f"Reason: **{reason}**"
        if game_id:
            game_name = get_game_name(game_id)
            if game_name:
                description += f"\nGame: {game_name}"
            description += f"\nGame ID: `{game_id[:12]}...`"
        self.send_embed("Rejoining Server", description, 16776960)

    def notify_status(self, status, game_id=None, universe_id=None):
        if not self.enabled:
            return

        fields = []
        if universe_id:
            game_name = get_game_name(universe_id)
            if game_name:
                fields.append({"name": "Game", "value": game_name, "inline": True})
        
        if game_id:
            fields.append(
                {"name": "Game ID", "value": f"`{game_id[:12]}...`", "inline": True}
            )

        color = 5025616 if status == "In-Game" else 16776960

        title = "Status Update"
        description = f"Current status: **{status}**"

        self.send_embed(title, description, color, fields)

    def notify_error(self, error):
        if not self.notify_on_error:
            return
        self.send_embed("Error Occurred", f"```{error}```", 16711680)


def check_root():
    try:
        result = subprocess.run(["su", "-c", "id"], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False


def run_shell_cmd(cmd_str, use_root=False, silent=False):
    if use_root:
        full_cmd = ["su", "-c", cmd_str]
    else:
        full_cmd = cmd_str.split()

    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def get_roblox_pid():
    success, output = run_shell_cmd(
        f"pidof {ROBLOX_PACKAGE}", use_root=True, silent=True
    )
    if success and output:
        return output.split()[0]
    return None


def force_stop_roblox():
    pid = get_roblox_pid()
    if pid:
        run_shell_cmd(f"kill -9 {pid}", use_root=True, silent=True)
        time.sleep(1)

    run_shell_cmd(f"am force-stop {ROBLOX_PACKAGE}", use_root=True, silent=True)
    time.sleep(1)


def open_ps_link(link):
    cmd = f'am start -a android.intent.action.VIEW -d "{link}" -p {ROBLOX_PACKAGE}'
    success, _ = run_shell_cmd(cmd, use_root=True, silent=True)
    return success


def is_roblox_running():
    return get_roblox_pid() is not None


def get_user_info(user_id):
    url = f"https://users.roblox.com/v1/users/{user_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("name"), data.get("displayName")
    except Exception as e:
        pass

    return None, None


def get_user_avatar(user_id):
    url = "https://thumbnails.roblox.com/v1/users/avatar-headshot"
    params = {
        "userIds": user_id,
        "size": "150x150",
        "format": "Png",
        "isCircular": True,
    }
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            images = data.get("data", [])
            if images:
                return images[0].get("imageUrl")
    except Exception as e:
        pass

    return None


def get_game_name(universe_id):
    url = "https://games.roblox.com/v1/games"
    params = {"universeIds": universe_id}
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            games = data.get("data", [])
            if games:
                return games[0].get("name")
    except Exception as e:
        pass

    return None


def copy_database(db_path, temp_path):
    """Copy database file to accessible location."""
    try:
        success, _ = run_shell_cmd(f'cp "{db_path}" "{temp_path}"', use_root=True, silent=True)
        if not success:
            return False
        run_shell_cmd(f'chmod 666 "{temp_path}"', use_root=True, silent=True)
        return True
    except:
        return False


def get_latest_log_file():
    log_dirs = [
        "/data/data/com.roblox.client/files/Logs",
        "/data/data/com.roblox.client/cache",
    ]
    
    for log_dir in log_dirs:
        success, output = run_shell_cmd(f"ls -t {log_dir}/*.log 2>/dev/null | head -1", use_root=True, silent=True)
        if success and output:
            return output
    return None


def extract_ids_from_log(log_path):
    if not log_path:
        return None, None, None, None
    
    patterns = {
        "place_id": r'"placeId"\s*:\s*(\d+)',
        "universe_id": r'"universeId"\s*:\s*(\d+)',
        "game_id": r'"gameId"\s*:\s*"([a-f0-9-]+)"',
        "job_id": r'"jobId"\s*:\s*"([a-f0-9-]+)"',
        "user_id": r'"userId"\s*:\s*(\d+)',
        "place_name": r'"placeName"\s*:\s*"([^"]+)"',
    }
    
    success, content = run_shell_cmd(f"cat {log_path}", use_root=True, silent=True)
    if not success or not content:
        return None, None, None, None
    
    place_id = None
    universe_id = None
    job_id = None
    user_id = None
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, content)
        if matches:
            if pattern_name == "place_id":
                place_id = matches[-1] if len(matches) > 1 else matches[0]
            elif pattern_name == "universe_id":
                universe_id = matches[-1] if len(matches) > 1 else matches[0]
            elif pattern_name == "job_id":
                job_id = matches[-1] if len(matches) > 1 else matches[0]
            elif pattern_name == "user_id":
                user_id = matches[-1] if len(matches) > 1 else matches[0]
    
    return place_id, universe_id, job_id, user_id


def extract_ids_from_storage():
    storage_files = [
        "/data/data/com.roblox.client/shared/rbx-storage.db",
        "/data/data/com.roblox.client/databases/rbx-storage.db",
        "/data/data/com.roblox.client/files/rbx-storage.db",
    ]
    
    temp_db = "/sdcard/temp_rbx_storage.db"
    
    for storage_file in storage_files:
        success, _ = run_shell_cmd(f'test -f {storage_file} && echo "exists"', use_root=True, silent=True)
        if not success:
            continue
        
        if not copy_database(storage_file, temp_db):
            continue
        
        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            place_id = None
            universe_id = None
            job_id = None
            user_id = None
            
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table});")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    place_id_col = next((col for col in columns if 'place' in col.lower() and 'id' in col.lower()), None)
                    universe_id_col = next((col for col in columns if 'universe' in col.lower() and 'id' in col.lower()), None)
                    job_id_col = next((col for col in columns if 'job' in col.lower() and 'id' in col.lower()), None)
                    user_id_col = next((col for col in columns if 'user' in col.lower() and 'id' in col.lower()), None)
                    
                    if place_id_col:
                        cursor.execute(f"SELECT {place_id_col} FROM {table} WHERE {place_id_col} IS NOT NULL AND {place_id_col} != '' LIMIT 1;")
                        result = cursor.fetchone()
                        if result and result[0]:
                            place_id = str(result[0])
                    
                    if universe_id_col:
                        cursor.execute(f"SELECT {universe_id_col} FROM {table} WHERE {universe_id_col} IS NOT NULL AND {universe_id_col} != '' LIMIT 1;")
                        result = cursor.fetchone()
                        if result and result[0]:
                            universe_id = str(result[0])
                    
                    if job_id_col:
                        cursor.execute(f"SELECT {job_id_col} FROM {table} WHERE {job_id_col} IS NOT NULL AND {job_id_col} != '' LIMIT 1;")
                        result = cursor.fetchone()
                        if result and result[0]:
                            job_id = str(result[0])
                    
                    if user_id_col:
                        cursor.execute(f"SELECT {user_id_col} FROM {table} WHERE {user_id_col} IS NOT NULL AND {user_id_col} != '' LIMIT 1;")
                        result = cursor.fetchone()
                        if result and result[0]:
                            user_id = str(result[0])
                    
                    if place_id and universe_id:
                        break
                except:
                    continue
            
            conn.close()
            
            if os.path.exists(temp_db):
                os.remove(temp_db)
            
            if place_id and universe_id:
                return place_id, universe_id, job_id, user_id
            elif place_id or universe_id:
                return place_id, universe_id, job_id, user_id
            
        except Exception:
            pass
        finally:
            if os.path.exists(temp_db):
                try:
                    os.remove(temp_db)
                except:
                    pass
    
    return None, None, None, None


def check_local_game_status():
    is_running = is_roblox_running()
    
    if not is_running:
        return False, None, None, None, None
    
    log_file = get_latest_log_file()
    place_id, universe_id, job_id, user_id = extract_ids_from_log(log_file)
    
    if not place_id or not universe_id:
        place_id, universe_id, job_id, user_id = extract_ids_from_storage()
    
    if place_id or universe_id or job_id or user_id:
        return True, place_id, universe_id, job_id, user_id
    
    return False, None, None, None, None


def get_local_game_info():
    is_ingame, place_id, universe_id, job_id, user_id = check_local_game_status()
    
    info = {
        "is_ingame": is_ingame,
        "place_id": place_id,
        "universe_id": universe_id,
        "job_id": job_id,
        "user_id": user_id,
        "source": "local_files"
    }
    
    return info


def check_user_presence(user_id):
    is_ingame, place_id, universe_id, job_id, local_user_id = check_local_game_status()
    
    if is_ingame and (place_id or universe_id or job_id):
        return True, place_id, universe_id
    
    return False, None, None


def should_rejoin(user_id, expected_game_id):
    if not is_roblox_running():
        return True, "Process stopped", None, None

    is_ingame, current_game_id, universe_id = check_user_presence(user_id)

    if not is_ingame:
        return True, "Not in-game", current_game_id, universe_id

    if expected_game_id and current_game_id and current_game_id != expected_game_id:
        return True, "Server switched", current_game_id, universe_id

    return False, "OK", current_game_id, universe_id


def set_selinux_permissive():
    success, mode = run_shell_cmd("getenforce", use_root=True, silent=True)
    if success and mode.strip() == "Enforcing":
        run_shell_cmd("setenforce 0", use_root=True, silent=True)


def print_header():
    print("\n" + "-" * 50)
    print("  Auto Rejoin Roblox Private Server")
    print("-" * 50 + "\n")


def print_local_game_info():
    print("\n" + "=" * 50)
    print("  Local Game Information (Extracted from Files)")
    print("=" * 50)
    
    if not check_root():
        print("❌ Root access required")
        return
    
    info = get_local_game_info()
    
    print(f"\nSource: {info['source']}")
    print(f"Status: {'In-Game' if info['is_ingame'] else 'Not In-Game'}")
    
    if info['place_id']:
        print(f"Place ID: {info['place_id']}")
    if info['universe_id']:
        print(f"Universe ID: {info['universe_id']}")
    if info['job_id']:
        print(f"Job ID: {info['job_id']}")
    if info['user_id']:
        print(f"User ID: {info['user_id']}")
    
    if info['is_ingame'] and info['universe_id']:
        game_name = get_game_name(info['universe_id'])
        if game_name:
            print(f"Game Name: {game_name}")
    
    print("=" * 50 + "\n")


def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        print_local_game_info()
        return
    
    if not os.path.exists(".env"):
        print("Error: .env file not found")
        print("Run: python setup.py")
        return

    if not check_root():
        print("Error: Root access required")
        return

    set_selinux_permissive()

    ps_link = os.getenv("PS_LINK")
    user_id = os.getenv("USER_ID")
    interval = int(os.getenv("CHECK_INTERVAL", "30"))
    restart_delay = int(os.getenv("RESTART_DELAY", "15"))

    discord = DiscordNotifier(user_id)

    if not ps_link or "YOUR_CODE" in ps_link:
        print("Error: Configure PS_LINK in .env file")
        print("Run: python setup.py")
        return

    print(f"Config: User {user_id}, Interval {interval}s")

    if is_roblox_running():
        print(f"Roblox already running, checking current session...")
        local_info = get_local_game_info()
        if local_info['is_ingame']:
            print(f"Already in-game!")
            if local_info['place_id']:
                print(f"Place ID: {local_info['place_id']}")
            if local_info['universe_id']:
                print(f"Universe ID: {local_info['universe_id']}")
            print("Monitoring current session (Ctrl+C to stop)\n")
        else:
            print("Roblox running but not in-game, connecting to private server...")
            if not open_ps_link(ps_link):
                print("Error: Failed to open Roblox")
                return
            print(f"Waiting for game to start...")
            time.sleep(restart_delay)
    else:
        print(f"Starting Roblox and connecting to private server...")
        if not open_ps_link(ps_link):
            print("Error: Failed to open Roblox")
            return
        print(f"Waiting for game to start...")
        time.sleep(restart_delay * 2)

    local_info = get_local_game_info()
    if local_info['place_id']:
        print(f"Place ID: {local_info['place_id']}")
    if local_info['universe_id']:
        print(f"Universe ID: {local_info['universe_id']}")

    _, private_game_id, _ = check_user_presence(user_id)

    if private_game_id:
        print(f"Game ID: {private_game_id[:12]}...")

    print("Monitoring active (Ctrl+C to stop)\n")

    discord.notify_start(user_id, interval)

    expected_game_id = private_game_id
    last_game_id = None
    last_game_name = None
    last_status = None

    while True:
        try:
            needs_rejoin, reason, current_game_id, universe_id = should_rejoin(
                user_id, expected_game_id
            )

            if needs_rejoin:
                print(f"{reason} - Rejoining...")

                discord.notify_rejoin(reason, current_game_id)

                force_stop_roblox()
                time.sleep(2)
                open_ps_link(ps_link)
                time.sleep(restart_delay * 2)

                _, new_game_id, new_universe_id = check_user_presence(user_id)
                if new_game_id:
                    expected_game_id = new_game_id
                    new_game_name = get_game_name(new_universe_id)
                    print("Rejoined successfully")
                    if new_game_name:
                        print(f"Game: {new_game_name}")
                    print()
                    last_game_id = new_game_id
                    last_game_name = new_game_name
                    last_status = "In-Game"
                    discord.notify_status("Rejoined", new_game_id, new_universe_id)
                else:
                    print("Rejoined (Game ID unavailable)\n")
                    last_game_id = None
                    last_game_name = None
                    last_status = "rejoined"
                    # Fallback notification
                    discord.notify_status("Rejoined (Waiting for data...)", None, None)
            else:
                if not expected_game_id and current_game_id:
                    expected_game_id = current_game_id
                    print(f"Tracking Game ID: {expected_game_id[:12]}...")

                status = (
                    "In-Game"
                    if (
                        current_game_id
                        and expected_game_id
                        and current_game_id == expected_game_id
                    )
                    else "In-Game (Unknown server)"
                )

                if current_game_id and current_game_id != last_game_id:
                    game_name = get_game_name(universe_id)
                    last_game_id = current_game_id
                    last_game_name = game_name
                    last_status = status
                    print(f"{status}")
                    if game_name:
                        print(f"Game: {game_name}")
                    discord.notify_status(status, current_game_id, universe_id)

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\nStopped by user\n")
            break
        except Exception as e:
            error_msg = str(e)
            print(f"Error: {error_msg}")
            discord.notify_error(error_msg)
            time.sleep(5)


if __name__ == "__main__":
    main()
