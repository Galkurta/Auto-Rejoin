import os
import time
import subprocess
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
import psutil

load_dotenv()

ROBLOX_PACKAGE = "com.roblox.client"


class DiscordNotifier:
    def __init__(self, user_id):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.webhook_name = os.getenv("DISCORD_WEBHOOK_NAME")
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
            # cpu_percent can fail on Android/Termux
            try:
                cpu_percent = psutil.cpu_percent(interval=0.5)
            except Exception:
                cpu_percent = 0.0
            
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

        content_lines = []

        if description:
             content_lines.append(f"{description}")

        if fields:
            for field in fields:
                name = field.get("name", "")
                value = field.get("value", "")
                content_lines.append(f"• **{name}:** {value}")

        content_lines.append("")
        content_lines.append("──────────────────────────────")
        content_lines.append("")

        system_info = self.get_system_info()
        
        if self.display_name:
             content_lines.append(f"• **Account Name:** {self.display_name}")
        
        content_lines.append(f"• **CPU Usage:** {system_info['cpu_percent']}%")
        content_lines.append(f"• **RAM Usage:** {system_info['ram_used_gb']}/{system_info['ram_total_gb']} GB ({system_info['ram_percent']}%)")

        mention = self.format_mention()
        if mention:
            content_lines.append(f"\n{mention}")

        final_description = "\n".join(content_lines)

        embed = {
            "title": f"**{title}**", # Bold title for impact
            "description": final_description,
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {"text": self.webhook_name},
            #"fields": [] # explicitly empty, we moved everything to description
            "thumbnail": {"url": "https://tr.rbxcdn.com/53eb9b17fe1432a809c73a1ca3434645/150/150/Image/Png"} # Re-adding thumbnail as it looks good in the example
        }
        
        if show_user_info and self.username:
             embed["author"] = {
                "name": f"{self.display_name} (@{self.username})",
                "icon_url": self.avatar_url,
            }

        payload = {"username": self.webhook_name, "embeds": [embed]}

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
        
        # dynamic title based on reason
        title = f"[ Rejoining ] - {reason}"
        
        clean_fields = []

        if game_id:
            clean_fields.append({"name": "Target Game ID", "value": f"`{game_id}`"})

        self.send_embed(title, "", 16776960, clean_fields)

    def notify_status(self, status, game_id=None, universe_id=None):
        if not self.enabled:
            return

        title = f"[ {status} ]" 
        description = "" 
        
        if universe_id:
             game_name = get_game_name(universe_id)
             if game_name:
                 title = f"[ {status} ] - {game_name}"

        clean_fields = []
        if game_id:
             clean_fields.append({"name": "Game ID", "value": f"`{game_id}`"})
        
        if universe_id and " - " not in title:
             game_name = get_game_name(universe_id)
             if game_name:
                 clean_fields.append({"name": "Game Name", "value": game_name})

        # Define color based on status
        color = 5025616 if status == "In-Game" else 16776960

        self.send_embed(title, description, color, clean_fields)

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


def check_user_presence(user_id, roblox_cookie=None):
    url = "https://presence.roblox.com/v1/presence/users"
    payload = {"userIds": [user_id]}
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

    cookies = {}
    if roblox_cookie:
        cookies[".ROBLOSECURITY"] = roblox_cookie

    try:
        r = requests.post(
            url, json=payload, headers=headers, cookies=cookies, timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            user_presences = data.get("userPresences", [])
            if user_presences:
                presence = user_presences[0]
                presence_type = presence.get("userPresenceType")
                game_id = presence.get("gameId")
                universe_id = presence.get("universeId")
                is_ingame = presence_type == 2
                return is_ingame, game_id, universe_id
    except Exception as e:
        pass

    return True, None, None


def should_rejoin(user_id, expected_game_id, roblox_cookie=None):
    if not is_roblox_running():
        return True, "Process stopped", None, None

    is_ingame, current_game_id, universe_id = check_user_presence(user_id, roblox_cookie)

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


def main():
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
    roblox_cookie = os.getenv("ROBLOX_COOKIE")

    discord = DiscordNotifier(user_id)

    if not ps_link or "YOUR_CODE" in ps_link:
        print("Error: Configure PS_LINK in .env file")
        print("Run: python setup.py")
        return

    print(f"Config: User {user_id}, Interval {interval}s")

    force_stop_roblox()
    time.sleep(2)

    if not open_ps_link(ps_link):
        print("Error: Failed to open Roblox")
        return

    print(f"Initializing...")
    time.sleep(restart_delay * 2)

    _, private_game_id, _ = check_user_presence(user_id, roblox_cookie)

    if private_game_id:
        print(f"Game ID: {private_game_id[:12]}...")

    print("Monitoring active (Ctrl+C to stop)\n")

    discord.notify_start(user_id, interval)

    expected_game_id = private_game_id
    last_game_id = None

    while True:
        try:
            needs_rejoin, reason, current_game_id, universe_id = should_rejoin(
                user_id, expected_game_id, roblox_cookie
            )

            if needs_rejoin:
                print(f"{reason} - Rejoining...")

                discord.notify_rejoin(reason, current_game_id)

                force_stop_roblox()
                time.sleep(2)
                open_ps_link(ps_link)
                time.sleep(restart_delay * 2)

                _, new_game_id, new_universe_id = check_user_presence(user_id, roblox_cookie)
                if new_game_id:
                    expected_game_id = new_game_id
                    new_game_name = get_game_name(new_universe_id)
                    print("Rejoined successfully")
                    if new_game_name:
                        print(f"Game: {new_game_name}")
                    print()
                    print()
                    last_game_id = new_game_id
                    discord.notify_status("Rejoined", new_game_id, new_universe_id)
                else:
                    print("Rejoined (Game ID unavailable)\n")
                    last_game_id = None
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