#!/usr/bin/env python3
import os


def setup():
    print("\nAuto Rejoin Setup (PC)")
    print("-----------------------\n")

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

    print("Note: To get your Roblox cookie:")
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
