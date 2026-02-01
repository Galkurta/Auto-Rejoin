import os
import time
import psutil
import subprocess
import webbrowser
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

ROBLOX_PROCESS_NAMES = ["RobloxPlayerBeta.exe", "RobloxPlayer.exe"]


class DiscordNotifier:
    def __init__(self, user_id):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.webhook_name = os.getenv("DISCORD_WEBHOOK_NAME", "Auto Rejoin Bot (PC)")
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


def find_roblox_process():
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] in ROBLOX_PROCESS_NAMES:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def is_roblox_running():
    return find_roblox_process() is not None


def kill_roblox():
    killed = False
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] in ROBLOX_PROCESS_NAMES:
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
        print(f"Failed to open link: {e}")
        return False


def get_user_info(user_id):
    url = f"https://users.roblox.com/v1/users/{user_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

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
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

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


def main():
    if not os.path.exists(".env"):
        print("Error: .env file not found")
        print("Run: python setup.py")
        return

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

    if not user_id or user_id == "0":
        print("Error: Set your USER_ID in .env file")
        print("Run: python setup.py")
        return

    print(f"Config: User {user_id}, Interval {interval}s")
    if discord.enabled:
        print(f"Discord notifications enabled")

    if is_roblox_running():
        print("Roblox is already running")
        print("Stopping current instance...")
        kill_roblox()
        time.sleep(2)

    print("Starting Roblox...")
    if not open_private_server(ps_link):
        print("Error: Failed to open Roblox")
        return

    print(f"Initializing...")
    print("(Roblox should open in your browser and launch the game)")
    time.sleep(restart_delay * 2)

    print()
    _, private_game_id, _ = check_user_presence(user_id, roblox_cookie)

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
                user_id, expected_game_id, roblox_cookie
            )

            if needs_rejoin:
                print(f"{reason} - Rejoining...")

                discord.notify_rejoin(reason, current_game_id)

                kill_roblox()
                time.sleep(2)
                open_private_server(ps_link)
                time.sleep(restart_delay * 2)

                _, new_game_id, new_universe_id = check_user_presence(user_id, roblox_cookie)
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
            else:
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
