#!/usr/bin/env python3
import os
import subprocess
import re
from typing import Optional, Tuple, Dict, List
from dotenv import load_dotenv


def run_shell_cmd(cmd: str, use_root: bool = True, silent: bool = False) -> Tuple[bool, str]:
    """Execute shell command with optional root access."""
    prefix = "su -c " if use_root else ""
    full_cmd = f"{prefix}{cmd}"
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception:
        return False, ""


def check_root() -> bool:
    """Check if root access is available."""
    success, _ = run_shell_cmd("su -c id", use_root=False)
    return success


def get_latest_log_file() -> Optional[str]:
    """Find the latest Roblox log file."""
    log_dirs = [
        "/data/data/com.roblox.client/files/Logs",
        "/sdcard/Android/data/com.roblox.client/files/Logs",
    ]
    
    for log_dir in log_dirs:
        success, output = run_shell_cmd(f"test -d {log_dir} && echo 'exists'", use_root=True, silent=True)
        if success and "exists" in output:
            print(f"Log directory exists: {log_dir}")
            success, output = run_shell_cmd(f"ls -t {log_dir}/*.log 2>/dev/null | head -1", use_root=True, silent=True)
            if success and output.strip():
                log_file = output.strip().split('\n')[0]
                return log_file
            else:
                print(f"No .log files found in {log_dir}")
        else:
            print(f"Log directory not found: {log_dir}")
    
    return None


def extract_user_id_from_log(log_path: Optional[str]) -> Optional[str]:
    """Extract user ID from Roblox log file."""
    if not log_path:
        return None
    
    pattern = r'"userId"\s*:\s*(\d+)'
    
    success, content = run_shell_cmd(f"cat {log_path}", use_root=True, silent=True)
    if not success or not content:
        return None
    
    matches = re.findall(pattern, content)
    if matches:
        return matches[-1] if len(matches) > 1 else matches[0]
    
    return None


def extract_user_id_from_storage() -> Optional[str]:
    """Extract user ID from Roblox storage files."""
    storage_files = [
        "/data/data/com.roblox.client/shared/rbx-storage.db",
        "/data/data/com.roblox.client/shared/rbx-storage.db-wal",
    ]
    
    for storage_file in storage_files:
        success, _ = run_shell_cmd(f"test -f {storage_file} && echo 'exists'", use_root=True, silent=True)
        if success:
            print(f"Storage file found: {storage_file}")
            success, content = run_shell_cmd(f"cat {storage_file}", use_root=True, silent=True)
            if success and content:
                content_bytes = content.encode('utf-8', errors='ignore')
                
                user_matches = re.findall(rb'userId["\s:]+(\d{8,12})', content_bytes)
                if user_matches:
                    try:
                        return user_matches[-1].decode('utf-8')
                    except:
                        pass
                else:
                    print(f"No userId pattern found in {storage_file}")
        else:
            print(f"Storage file not found: {storage_file}")
    
    return None


def auto_extract_user_id() -> Optional[str]:
    """Automatically extract User ID from Roblox app local files."""
    if not check_root():
        print("Root access not available. Cannot auto-detect User ID.")
        return None
    
    print("Checking for Roblox app and local files...")
    
    log_file = get_latest_log_file()
    if log_file:
        print(f"Found log file: {log_file}")
    else:
        print("No Roblox log files found.")
    
    user_id = extract_user_id_from_log(log_file)
    
    if not user_id:
        print("User ID not found in logs, checking storage files...")
        user_id = extract_user_id_from_storage()
    
    if user_id:
        print(f"User ID extracted: {user_id}")
    else:
        print("User ID not found in local files.")
    
    return user_id

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
