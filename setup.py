#!/usr/bin/env python3
import os
import sqlite3
import subprocess
import requests
import re
import tempfile
from contextlib import contextmanager
from typing import Optional, Tuple, Dict, List
from dotenv import load_dotenv

DEFAULT_CHECK_INTERVAL = 30
DEFAULT_RESTART_DELAY = 15
DEFAULT_DISCORD_BOT_NAME = "Auto Rejoin Bot"

PACKAGES = {
    "Roblox App": "com.roblox.client",
}

WEBVIEW_COOKIE_PATHS = [
    "databases/webviewCookiesChromium.db",
    "app_webview/Cookies",
    "app_webview/Default/Cookies",
]

ROBLOX_COOKIE_NAME = ".ROBLOSECURITY"


def validate_url(url: str) -> bool:
    """Validate if a string is a properly formatted URL."""
    if not url:
        return False
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(pattern.match(url))


def validate_user_id(user_id: str) -> bool:
    """Validate if a string is a valid Roblox User ID (digits only)."""
    return bool(user_id) and user_id.isdigit() and len(user_id) >= 3


def validate_discord_webhook(url: str) -> bool:
    """Validate if a URL is a Discord webhook."""
    if not url:
        return False
    return url.startswith("https://discord.com/api/webhooks/") or url.startswith("https://ptb.discord.com/api/webhooks/") or url.startswith("https://canary.discord.com/api/webhooks/")


def validate_numeric_input(value: str, min_val: int = 1, max_val: int = 3600) -> bool:
    """Validate if a string is a valid number within range."""
    if not value or not value.isdigit():
        return False
    num = int(value)
    return min_val <= num <= max_val


def get_validated_input(prompt: str, validator, default: Optional[str] = None, error_msg: str = "Invalid input. Please try again.") -> str:
    """Get user input with validation."""
    while True:
        user_input = input(prompt).strip()
        if default and not user_input:
            return default
        if validator(user_input):
            return user_input
        print(error_msg)


def get_yes_no_input(prompt: str, default: bool = True) -> bool:
    """Get yes/no input from user with default value."""
    default_str = "y" if default else "n"
    user_input = input(f"{prompt} (y/n, default {default_str}): ").strip().lower()
    if not user_input:
        return default
    return user_input != "n"


@contextmanager
def temp_database_path(suffix: str = ".db"):
    """Context manager for temporary database files."""
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_path = temp_file.name
        temp_file.close()
        yield temp_path
    finally:
        if temp_file and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def check_root() -> bool:
    """Check if the script has root access via su."""
    try:
        result = subprocess.run(["su", "-c", "id"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        return False


def run_shell_cmd(cmd_str: str) -> Tuple[bool, str]:
    """Execute a shell command with root privileges."""
    try:
        result = subprocess.run(
            ["su", "-c", cmd_str], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError) as e:
        return False, str(e)


def check_package_installed(package_name):
    success, output = run_shell_cmd(f"pm list packages | grep {package_name}")
    return success and package_name in output


def find_installed_app() -> Dict[str, str]:
    """Find all installed supported apps."""
    installed = {}

    for name, package in PACKAGES.items():
        if check_package_installed(package):
            installed[name] = package

    return installed


def find_cookie_databases(package_name: str) -> List[str]:
    """Find cookie database files for Roblox app WebView."""
    base_path = f"/data/data/{package_name}"
    found_paths = []

    for path in WEBVIEW_COOKIE_PATHS:
        full_path = f"{base_path}/{path}"
        if "*" in full_path:
            success, output = run_shell_cmd(f"ls {full_path} 2>/dev/null")
            if success and output:
                for line in output.split("\n"):
                    if line.strip():
                        found_paths.append(line.strip())
        else:
            success, _ = run_shell_cmd(f'test -f {full_path} && echo "exists"')
            if success:
                found_paths.append(full_path)

    return found_paths


def copy_database(db_path: str, temp_path: str) -> bool:
    """Copy database file from protected path to accessible location."""
    try:
        success, _ = run_shell_cmd(f'cp "{db_path}" "{temp_path}"')
        if not success:
            return False
        run_shell_cmd(f'chmod 666 "{temp_path}"')
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError):
        return False


def extract_cookie_from_webview(db_path: str) -> Optional[str]:
    """Extract Roblox cookie from Roblox app WebView database."""
    with temp_database_path("_cookies_webview.db") as temp_db:
        if not copy_database(db_path, temp_db):
            return None

        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    SELECT name, value, host_key 
                    FROM cookies 
                    WHERE (host_key LIKE '%roblox.com%' OR host_key LIKE '%www.roblox.com%')
                    AND name = ?
                """, (ROBLOX_COOKIE_NAME,))
                result = cursor.fetchone()
            except sqlite3.OperationalError:
                cursor.execute("""
                    SELECT name, value 
                    FROM cookies 
                    WHERE name = ?
                """, (ROBLOX_COOKIE_NAME,))
                result = cursor.fetchone()

            conn.close()

            if result:
                return result[1] if len(result) > 1 else result[0]
            return None
        except (sqlite3.Error, OSError, IndexError):
            return None


def auto_extract_cookie() -> Optional[str]:
    """Automatically extract Roblox cookie from Roblox app."""
    if not check_root():
        print("Root access required for auto cookie extraction")
        print("You'll need to enter cookie manually\n")
        return None

    installed_apps = find_installed_app()

    if not installed_apps:
        print("Roblox app not found for auto extraction")
        print("You'll need to enter cookie manually\n")
        return None

    for app_name, package_name in installed_apps.items():
        print(f"Checking {app_name} for cookie...")

        db_paths = find_cookie_databases(package_name)

        if not db_paths:
            continue

        for db_path in db_paths:
            cookie = extract_cookie_from_webview(db_path)

            if cookie:
                print(f"Cookie found in {app_name}!")
                print(f"Cookie extracted successfully ({len(cookie)} characters)\n")
                return cookie

    print("Cookie not found automatically")
    print("You'll need to enter cookie manually\n")
    return None


def get_roblox_user_info(cookie: str) -> Tuple[Optional[int], Optional[str]]:
    """Fetch Roblox user information using the provided cookie."""
    try:
        url = "https://users.roblox.com/v1/users/authenticated"
        headers = {
            "Cookie": f".ROBLOSECURITY={cookie}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("id"), data.get("name")
        elif response.status_code == 401:
            print(f"Error: Cookie appears to be invalid or expired (Status 401)")
        else:
            print(f"Error: Failed to fetch user info (Status {response.status_code})")
        return None, None
    except (requests.RequestException, requests.Timeout, requests.ConnectionError) as e:
        print(f"Error fetching user info: {e}")
        return None, None
    except (ValueError, KeyError) as e:
        print(f"Error parsing user info response: {e}")
        return None, None


def setup() -> None:
    """Run the interactive setup wizard for Auto Rejoin configuration."""
    print("\nAuto Rejoin Setup")
    print("----------------\n")

    env_path = ".env"

    if os.path.exists(env_path):
        if not get_yes_no_input("Existing .env file found. Overwrite?", False):
            print("Setup cancelled.")
            return

    print("Enter the following information:\n")

    print("Roblox Cookie:")
    if get_yes_no_input("Auto-extract cookie from Roblox app?", True):
        roblox_cookie = auto_extract_cookie()
    else:
        roblox_cookie = None

    if not roblox_cookie:
        roblox_cookie = get_validated_input(
            "Roblox Cookie (.ROBLOSECURITY): ",
            lambda x: len(x) > 10,
            error_msg="Cookie appears to be too short. Please enter a valid cookie."
        )

    fetched_user_id = None
    fetched_username = None

    if roblox_cookie:
        print("\nVerifying cookie and fetching User ID...")
        fetched_user_id, fetched_username = get_roblox_user_info(roblox_cookie)
        if fetched_user_id:
            print(f"Success! Logged in as: {fetched_username} (ID: {fetched_user_id})")
        else:
            print("Could not fetch User ID automatically.")

    print("")

    ps_link = get_validated_input(
        "Private Server Link: ",
        validate_url,
        error_msg="Invalid URL format. Please enter a valid Roblox private server link."
    )

    if fetched_user_id:
        if get_yes_no_input(f"Use User ID {fetched_user_id} ({fetched_username})?", True):
            user_id = str(fetched_user_id)
        else:
            user_id = get_validated_input(
                "Roblox User ID: ",
                validate_user_id,
                error_msg="Invalid User ID. Please enter a valid numeric Roblox User ID."
            )
    else:
        user_id = get_validated_input(
            "Roblox User ID: ",
            validate_user_id,
            error_msg="Invalid User ID. Please enter a valid numeric Roblox User ID."
        )

    check_interval = get_validated_input(
        f"Check Interval (seconds, default {DEFAULT_CHECK_INTERVAL}): ",
        lambda x: validate_numeric_input(x, 5, 3600) or x == "",
        str(DEFAULT_CHECK_INTERVAL),
        "Invalid interval. Please enter a number between 5 and 3600."
    )

    restart_delay = get_validated_input(
        f"Restart Delay (seconds, default {DEFAULT_RESTART_DELAY}): ",
        lambda x: validate_numeric_input(x, 5, 300) or x == "",
        str(DEFAULT_RESTART_DELAY),
        "Invalid delay. Please enter a number between 5 and 300."
    )

    print("\n----------------\nDiscord Configuration (Optional)\n")

    configure_discord = get_yes_no_input("Do you want to setup Discord Webhook?", False)

    if configure_discord:
        discord_webhook = get_validated_input(
            "Discord Webhook URL: ",
            validate_discord_webhook,
            error_msg="Invalid Discord webhook URL. Please enter a valid webhook URL."
        )
    else:
        discord_webhook = ""

    if discord_webhook:
        discord_webhook_name = (
            input(f"Discord Bot Name (default: {DEFAULT_DISCORD_BOT_NAME}): ").strip()
            or DEFAULT_DISCORD_BOT_NAME
        )
        print("\nNote: To find your Discord User ID, enable Developer Mode in Discord settings, right-click your profile, and click 'Copy ID'.")
        discord_mention_user = input(
            "Discord User ID to Mention (e.g., 8328109058... or @username): "
        ).strip()
    else:
        discord_webhook_name = DEFAULT_DISCORD_BOT_NAME
        discord_mention_user = ""

    discord_enabled = (
        "true"
        if discord_webhook and "YOUR_WEBHOOK_URL" not in discord_webhook
        else "false"
    )

    if discord_enabled == "true":
        notify_start = get_yes_no_input("Notify on start?", True)
        notify_rejoin = get_yes_no_input("Notify on rejoin?", True)
        notify_error = get_yes_no_input("Notify on errors?", True)
    else:
        notify_start = "true"
        notify_rejoin = "true"
        notify_error = "true"

    env_content = f"""PS_LINK={ps_link}
USER_ID={user_id}
CHECK_INTERVAL={check_interval}
RESTART_DELAY={restart_delay}
ROBLOX_COOKIE={roblox_cookie}
DISCORD_WEBHOOK_URL={discord_webhook}
DISCORD_WEBHOOK_NAME={discord_webhook_name}
DISCORD_MENTION_USER={discord_mention_user}
DISCORD_ENABLED={discord_enabled}
DISCORD_NOTIFY_ON_START={notify_start}
DISCORD_NOTIFY_ON_REJOIN={notify_rejoin}
DISCORD_NOTIFY_ON_ERROR={notify_error}
"""

    with open(env_path, "w") as f:
        f.write(env_content.strip())

    print(f"\nConfiguration saved to {env_path}")
    print("Setup complete. You can now run main.py\n")


if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
