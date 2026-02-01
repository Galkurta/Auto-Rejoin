#!/usr/bin/env python3
import os
import sqlite3
import subprocess
from dotenv import load_dotenv


def check_root():
    try:
        result = subprocess.run(["su", "-c", "id"], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False


def run_shell_cmd(cmd_str):
    try:
        result = subprocess.run(
            ["su", "-c", cmd_str], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def check_package_installed(package_name):
    success, output = run_shell_cmd(f"pm list packages | grep {package_name}")
    return success and package_name in output


def find_all_browser_data():
    browsers = {
        "Chrome": "com.android.chrome",
        "Chrome Beta": "com.chrome.beta",
        "Chrome Dev": "com.chrome.dev",
        "Chrome Canary": "com.chrome.canary",
        "Edge": "com.microsoft.emmx",
        "Firefox": "org.mozilla.firefox",
        "Opera": "com.opera.browser",
        "Samsung Internet": "com.sec.android.app.sbrowser",
        "Brave": "com.brave.browser",
        "Kiwi Browser": "com.kiwibrowser.browser",
        "DuckDuckGo": "com.duckduckgo.mobile.android",
        "Roblox App": "com.roblox.client",
    }

    installed = {}

    for name, package in browsers.items():
        if check_package_installed(package):
            installed[name] = package

    return installed


def find_cookie_databases(package_name):
    base_path = f"/data/data/{package_name}"

    possible_paths = [
        f"{base_path}/app_chrome/Default/Cookies",
        f"{base_path}/app_chrome/Profile */Cookies",
        f"{base_path}/app_msedge/Default/Cookies",
        f"{base_path}/databases/webviewCookiesChromium.db",
        f"{base_path}/app_webview/Cookies",
        f"{base_path}/app_webview/Default/Cookies",
    ]

    if "firefox" in package_name:
        success, output = run_shell_cmd(
            f'find {base_path} -name "cookies.sqlite" 2>/dev/null'
        )
        if success and output:
            return output.strip().split("\n")

    found_paths = []
    for path in possible_paths:
        if "*" in path:
            success, output = run_shell_cmd(f"ls {path} 2>/dev/null")
            if success and output:
                for line in output.split("\n"):
                    if line.strip():
                        found_paths.append(line.strip())
        else:
            success, _ = run_shell_cmd(f'test -f {path} && echo "exists"')
            if success:
                found_paths.append(path)

    return found_paths


def copy_database(db_path, temp_path):
    try:
        success, _ = run_shell_cmd(f'cp "{db_path}" "{temp_path}"')
        if not success:
            return False

        run_shell_cmd(f'chmod 666 "{temp_path}"')
        return True
    except:
        return False


def extract_cookie_chromium(db_path):
    temp_db = "/sdcard/temp_cookies_chromium.db"

    try:
        if not copy_database(db_path, temp_db):
            return None

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT name, value, host_key 
                FROM cookies 
                WHERE (host_key LIKE '%roblox.com%' OR host_key LIKE '%www.roblox.com%')
                AND name = '.ROBLOSECURITY'
            """)
            result = cursor.fetchone()
        except:
            try:
                cursor.execute("""
                    SELECT name, value 
                    FROM cookies 
                    WHERE name = '.ROBLOSECURITY'
                """)
                result = cursor.fetchone()
            except:
                result = None

        conn.close()

        if os.path.exists(temp_db):
            os.remove(temp_db)

        if result:
            return result[1] if len(result) > 1 else result[0]

        return None

    except Exception as e:
        if os.path.exists(temp_db):
            os.remove(temp_db)
        return None


def extract_cookie_firefox(db_path):
    temp_db = "/sdcard/temp_cookies_firefox.db"

    try:
        if not copy_database(db_path, temp_db):
            return None

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, value, host 
            FROM moz_cookies 
            WHERE host LIKE '%roblox.com%' 
            AND name = '.ROBLOSECURITY'
        """)

        result = cursor.fetchone()
        conn.close()

        if os.path.exists(temp_db):
            os.remove(temp_db)

        if result:
            return result[1]

        return None

    except Exception as e:
        if os.path.exists(temp_db):
            os.remove(temp_db)
        return None


def auto_extract_cookie():
    if not check_root():
        print("Root access required for auto cookie extraction")
        print("You'll need to enter cookie manually\n")
        return None

    installed_browsers = find_all_browser_data()

    if not installed_browsers:
        print("No supported browsers/apps found for auto extraction")
        print("You'll need to enter cookie manually\n")
        return None

    cookie_found = False
    cookie_value = None
    found_in = None

    for browser_name, package_name in installed_browsers.items():
        print(f"Checking {browser_name} for cookie...")

        db_paths = find_cookie_databases(package_name)

        if not db_paths:
            continue

        for db_path in db_paths:
            if "firefox" in package_name:
                cookie = extract_cookie_firefox(db_path)
            else:
                cookie = extract_cookie_chromium(db_path)

            if cookie:
                cookie_value = cookie
                cookie_found = True
                found_in = browser_name
                print(f"Cookie found in {browser_name}!")
                break

        if cookie_found:
            break

    if cookie_found and cookie_value:
        print(f"Cookie extracted successfully ({len(cookie_value)} characters)\n")
        return cookie_value

    print("Cookie not found automatically")
    print("You'll need to enter cookie manually\n")
    return None


def setup():
    print("\nAuto Rejoin Setup")
    print("----------------\n")

    env_path = ".env"

    if os.path.exists(env_path):
        overwrite = (
            input("Existing .env file found. Overwrite? (y/n): ").strip().lower()
        )
        if overwrite != "y":
            print("Setup cancelled.")
            return

    print("Enter the following information:\n")

    ps_link = input("Private Server Link: ").strip()
    while not ps_link:
        ps_link = input("Private Server Link (required): ").strip()

    user_id = input("Roblox User ID: ").strip()
    while not user_id or not user_id.isdigit():
        user_id = input("Roblox User ID (numbers only, required): ").strip()

    check_interval = input("Check Interval (seconds, default 30): ").strip() or "30"
    restart_delay = input("Restart Delay (seconds, default 15): ").strip() or "15"

    print("\nOptional - leave empty to skip:")

    print("\nRoblox Cookie:")
    auto_cookie = (
        input("Auto-extract cookie from browser? (y/n, default y): ").strip().lower()
    )
    if auto_cookie != "n":
        roblox_cookie = auto_extract_cookie()
    else:
        roblox_cookie = input("Roblox Cookie (.ROBLOSECURITY): ").strip()

    discord_webhook = input("Discord Webhook URL: ").strip()

    if discord_webhook:
        discord_webhook_name = (
            input("Discord Bot Name (default: Auto Rejoin Bot): ").strip()
            or "Auto Rejoin Bot"
        )
        discord_mention_user = input(
            "Discord User to Mention (e.g., 123456789012345678 or @username): "
        ).strip()
    else:
        discord_webhook_name = "Auto Rejoin Bot"
        discord_mention_user = ""

    discord_enabled = (
        "true"
        if discord_webhook and "YOUR_WEBHOOK_URL" not in discord_webhook
        else "false"
    )

    if discord_enabled == "true":
        notify_start = input("Notify on start? (y/n, default y): ").strip().lower()
        notify_start = "true" if notify_start != "n" else "true"

        notify_rejoin = input("Notify on rejoin? (y/n, default y): ").strip().lower()
        notify_rejoin = "true" if notify_rejoin != "n" else "true"

        notify_error = input("Notify on errors? (y/n, default y): ").strip().lower()
        notify_error = "true" if notify_error != "n" else "true"
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

    print("Note: To get your Roblox cookie manually:")
    print("1. Open browser and go to roblox.com")
    print("2. Login to your account")
    print("3. Press F12 to open Developer Tools")
    print("4. Go to Application/Storage tab")
    print("5. Cookies -> https://www.roblox.com")
    print("6. Find .ROBLOSECURITY cookie and copy its value")


if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
