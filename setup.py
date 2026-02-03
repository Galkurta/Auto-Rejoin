#!/usr/bin/env python3
import os
import subprocess
import re
import requests
from typing import Optional, Tuple, Dict, List
from dotenv import load_dotenv


def run_shell_cmd(cmd: str, use_root: bool = True, silent: bool = False) -> Tuple[bool, str]:
    """Run shell command with optional root access."""
    if use_root:
        cmd = f"su -c '{cmd}'"
    
    try:
        if silent:
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True, ""
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return True, result.stdout
    except subprocess.CalledProcessError:
        return False, ""


def check_root() -> bool:
    """Check if root access is available."""
    success, _ = run_shell_cmd("su -c id", use_root=False)
    return success


def extract_user_id_from_log(log_path: str) -> Optional[str]:
    """Extract user ID from Roblox log file."""
    pattern = r'"userId"\s*:\s*(\d+)'
    
    success, content = run_shell_cmd(f"cat {log_path}", use_root=True, silent=True)
    if not success or not content:
        return None
    
    matches = re.findall(pattern, content)
    if matches:
        return matches[-1] if len(matches) > 1 else matches[0]
    
    return None


def find_roblox_package() -> Optional[str]:
    """Find Roblox package name by searching for installed packages."""
    success, output = run_shell_cmd("pm list packages | grep roblox", use_root=True, silent=False)
    if success and output:
        packages = [line.split(":")[-1] for line in output.strip().split("\n") if line.strip()]
        if packages:
            print(f"Found Roblox packages: {', '.join(packages)}")
            return packages[0]
    return None


def find_log_directory(package_name: str) -> Optional[str]:
    """Find Roblox log directory."""
    possible_dirs = [
        f"/data/data/{package_name}/files/Logs",
        f"/sdcard/Android/data/{package_name}/files/Logs",
        f"/data/data/{package_name}/cache/Logs",
    ]
    
    for log_dir in possible_dirs:
        success, output = run_shell_cmd(f"test -d {log_dir} && echo 'exists'", use_root=True, silent=False)
        if success and "exists" in output:
            return log_dir
    return None


def find_storage_directory(package_name: str) -> Optional[str]:
    """Find Roblox storage directory."""
    possible_dirs = [
        f"/data/data/{package_name}/shared",
        f"/data/data/{package_name}/files",
    ]
    
    for storage_dir in possible_dirs:
        success, output = run_shell_cmd(f"test -d {storage_dir} && echo 'exists'", use_root=True, silent=False)
        if success and "exists" in output:
            return storage_dir
    return None


def extract_user_id_from_cookie(cookie: str) -> Optional[str]:
    """Extract User ID from Roblox cookie using API."""
    try:
        headers = {
            "Cookie": f".ROBLOSECURITY={cookie}",
            "User-Agent": "Roblox/WinInet",
            "Referer": "https://www.roblox.com/"
        }
        response = requests.get("https://users.roblox.com/v1/users/authenticated", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user_id = data.get("id")
            return str(user_id)
    except Exception:
        pass
    return None


def extract_cookie_from_roblox_app() -> Optional[str]:
    """Extract Roblox cookie from Roblox app on Android."""
    package_name = find_roblox_package()
    if not package_name:
        return None
    
    shared_prefs_dir = f"/data/data/{package_name}/shared_prefs"
    success, output = run_shell_cmd(f"ls {shared_prefs_dir} 2>/dev/null", use_root=True, silent=False)
    
    if not success or not output:
        return None
    
    cookie_pattern = rb'"ROBLOSECURITY"\s*>\s*([^<]+)'
    
    for pref_file in output.strip().split("\n"):
        pref_path = f"{shared_prefs_dir}/{pref_file.strip()}"
        success, content = run_shell_cmd(f"cat {pref_path}", use_root=True, silent=True)
        if success and content:
            content_bytes = content.encode('utf-8', errors='ignore')
            matches = re.findall(cookie_pattern, content_bytes)
            if matches:
                cookie = matches[-1].decode('utf-8').strip()
                if cookie and cookie != "null":
                    return cookie
    
    return None


def extract_cookie_from_chrome_android() -> Optional[str]:
    """Extract Roblox cookie from Chrome browser on Android."""
    package_name = "com.android.chrome"
    cookies_path = "/data/data/com.android.chrome/app_chrome/Default/Cookies"
    
    success, output = run_shell_cmd(f"test -f {cookies_path} && echo 'exists'", use_root=True, silent=False)
    if not success or "exists" not in output:
        return None
    
    try:
        success, content = run_shell_cmd(f"cat {cookies_path}", use_root=True, silent=True)
        if not success or not content:
            return None
        
        pattern = rb'.ROBLOSECURITY([^\x00]+?)(?:\x00|$)'
        matches = re.findall(pattern, content.encode('utf-8', errors='ignore'))
        if matches:
            for match in matches:
                cookie = match.decode('utf-8', errors='ignore').strip()
                if cookie and len(cookie) > 50 and cookie.startswith('"'):
                    cookie = cookie.strip('"')
                    return cookie
    except Exception:
        pass
    
    return None


def auto_extract_cookie() -> Optional[str]:
    """Automatically extract Roblox cookie from available sources."""
    print("Attempting to extract cookie automatically...")
    
    cookie = extract_cookie_from_roblox_app()
    if cookie:
        print("Cookie extracted from Roblox app.")
        return cookie
    
    cookie = extract_cookie_from_chrome_android()
    if cookie:
        print("Cookie extracted from Chrome browser.")
        return cookie
    
    print("No cookie found in automatic sources.")
    return None


def auto_extract_user_id() -> Optional[str]:
    """Automatically extract User ID from Roblox app local files or cookie."""
    print("Checking for Roblox app and local files...")
    
    package_name = find_roblox_package()
    if package_name:
        log_dir = find_log_directory(package_name)
        if log_dir:
            print(f"Found log directory: {log_dir}")
            success, output = run_shell_cmd(f"ls -t {log_dir}/*.log 2>/dev/null | head -1", use_root=True, silent=True)
            if success and output.strip():
                log_file = output.strip().split('\n')[0]
                print(f"Found log file: {log_file}")
                user_id = extract_user_id_from_log(log_file)
                if user_id:
                    print(f"User ID extracted: {user_id}")
                    return user_id
                else:
                    print("No userId pattern found in log file.")
            else:
                print(f"No .log files found in {log_dir}")
        else:
            print("Log directory not found.")
        
        storage_dir = find_storage_directory(package_name)
        if storage_dir:
            print(f"Found storage directory: {storage_dir}")
            success, output = run_shell_cmd(f"ls {storage_dir}/*.db* 2>/dev/null | head -5", use_root=True, silent=True)
            if success and output.strip():
                print(f"Checking storage files...")
                for line in output.strip().split("\n"):
                    storage_file = line.strip()
                    if storage_file:
                        print(f"Checking: {storage_file}")
                        success, content = run_shell_cmd(f"cat {storage_file}", use_root=True, silent=True)
                        if success and content:
                            content_bytes = content.encode('utf-8', errors='ignore')
                            user_matches = re.findall(rb'userId["\s:]+(\d{8,12})', content_bytes)
                            if user_matches:
                                user_id = user_matches[-1].decode('utf-8')
                                print(f"User ID extracted: {user_id}")
                                return user_id
            else:
                print("No storage database files found.")
        else:
            print("Storage directory not found.")
    
    print("User ID not found in local files.")
    print("You may need to run Roblox at least once to generate log files.")
    return None

DEFAULT_CHECK_INTERVAL = 30
DEFAULT_RESTART_DELAY = 15
DEFAULT_DISCORD_BOT_NAME = "Auto Rejoin Bot"

PACKAGES = {
    "Roblox App": "com.roblox.client",
}


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

    ps_link = get_validated_input(
        "Private Server Link: ",
        validate_url,
        error_msg="Invalid URL format. Please enter a valid Roblox private server link."
    )

    print("")

    print("Roblox User ID:")
    auto_user_id = auto_extract_user_id()
    
    if auto_user_id:
        print(f"Auto-detected User ID: {auto_user_id}")
        if get_yes_no_input("Use this User ID?", True):
            user_id = auto_user_id
        else:
            user_id = get_validated_input(
                "Roblox User ID: ",
                validate_user_id,
                error_msg="Invalid User ID. Please enter a valid numeric Roblox User ID."
            )
    else:
        auto_cookie = auto_extract_cookie()
        if auto_cookie:
            print("Fetching User ID from auto-extracted cookie...")
            user_id = extract_user_id_from_cookie(auto_cookie)
            if user_id:
                print(f"User ID retrieved: {user_id}")
            else:
                print("Failed to get User ID from auto-extracted cookie.")
                use_cookie = get_yes_no_input("Enter cookie manually?", False)
                if use_cookie:
                    cookie = input("Enter your Roblox cookie (.ROBLOSECURITY): ").strip()
                    if cookie:
                        print("Fetching User ID from cookie...")
                        user_id = extract_user_id_from_cookie(cookie)
                        if user_id:
                            print(f"User ID retrieved: {user_id}")
                        else:
                            print("Failed to get User ID from cookie. Please enter manually.")
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
                else:
                    user_id = get_validated_input(
                        "Roblox User ID: ",
                        validate_user_id,
                        error_msg="Invalid User ID. Please enter a valid numeric Roblox User ID."
                    )
        else:
            use_cookie = get_yes_no_input("Enter cookie manually to get User ID? (Cookie will NOT be saved)", False)
            if use_cookie:
                cookie = input("Enter your Roblox cookie (.ROBLOSECURITY): ").strip()
                if cookie:
                    print("Fetching User ID from cookie...")
                    user_id = extract_user_id_from_cookie(cookie)
                    if user_id:
                        print(f"User ID retrieved: {user_id}")
                    else:
                        print("Failed to get User ID from cookie. Please enter manually.")
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
