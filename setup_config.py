import json
import os
import webbrowser

CONFIG_FILE = "config.json"

def print_header():
    print("\n" + "="*60)
    print("  ⚙️  Roblox Auto-Rejoin Configuration Setup")
    print("="*60 + "\n")

def create_or_load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        return {
            "ps_link": "",
            "user_id": 0,
            "check_interval": 10,
            "restart_delay": 30,
            "roblox_cookie": ""
        }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\n✅ Configuration saved to {CONFIG_FILE}")

def get_cookie_manually():
    print("\n" + "="*60)
    print("  🍪 Get Roblox Cookie")
    print("="*60 + "\n")
    
    print("📋 Follow these steps:\n")
    print("1. A browser window will open to Roblox.com")
    print("2. Login to your Roblox account (if not already logged in)")
    print("3. Press F12 to open Developer Tools")
    print("4. Click 'Application' tab (Chrome/Edge) or 'Storage' tab (Firefox)")
    print("5. In left sidebar: Cookies → https://www.roblox.com")
    print("6. Find cookie named '.ROBLOSECURITY'")
    print("7. Double-click the Value field and copy all of it (Ctrl+A, Ctrl+C)")
    print("8. Come back here and paste it\n")
    
    choice = input("Press Enter to open Roblox.com, or type 'skip' to skip: ").strip().lower()
    
    if choice != 'skip':
        webbrowser.open("https://www.roblox.com")
        print("\n✓ Browser opened. Follow the steps above...\n")
    
    print("⚠️  The cookie is VERY LONG (1000+ characters)")
    print("   Make sure to copy ALL of it!\n")
    
    cookie = input("Paste your .ROBLOSECURITY cookie here: ").strip()
    
    if not cookie:
        print("❌ No cookie entered!")
        return None
    
    if not cookie.startswith("_|WARNING:"):
        print("\n⚠️  Warning: Cookie doesn't start with '_|WARNING:'")
        print("   Make sure you copied the ENTIRE value!")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return None
    
    print(f"\n✓ Cookie received ({len(cookie)} characters)")
    return cookie

def get_private_server_link():
    print("\n" + "="*60)
    print("  🔗 Get Private Server Link")
    print("="*60 + "\n")
    
    print("📋 How to get your Private Server link:\n")
    print("1. Go to your Roblox game")
    print("2. Click 'Servers' tab")
    print("3. Find your Private Server")
    print("4. Click the '⋯' menu → 'Copy Link'")
    print("5. Paste it here\n")
    
    link = input("Paste your Private Server link: ").strip()
    
    if not link:
        print("❌ No link entered!")
        return None
    
    if "roblox.com" not in link or "code=" not in link:
        print("\n⚠️  Warning: This doesn't look like a valid Roblox link")
        print("   It should contain 'roblox.com' and 'code='")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return None
    
    print(f"\n✓ Link received")
    return link

def get_user_id():
    print("\n" + "="*60)
    print("  👤 Get Your Roblox User ID")
    print("="*60 + "\n")
    
    print("📋 How to find your User ID:\n")
    print("1. Go to your Roblox profile")
    print("2. Look at the URL: roblox.com/users/12345678/profile")
    print("3. The number (12345678) is your User ID\n")
    
    choice = input("Press Enter to open your profile, or type 'skip': ").strip().lower()
    
    if choice != 'skip':
        webbrowser.open("https://www.roblox.com/users/profile")
        print("\n✓ Browser opened to your profile...\n")
    
    while True:
        user_id_str = input("Enter your User ID: ").strip()
        
        if not user_id_str:
            print("❌ No User ID entered!")
            continue
        
        try:
            user_id = int(user_id_str)
            if user_id <= 0:
                print("❌ User ID must be a positive number!")
                continue
            print(f"\n✓ User ID set to {user_id}")
            return user_id
        except ValueError:
            print("❌ User ID must be a number!")

def main():
    print_header()
    
    print("This wizard will help you set up the configuration.\n")
    
    config = create_or_load_config()
    
    has_cookie = config.get("roblox_cookie") and config["roblox_cookie"] != ""
    has_link = config.get("ps_link") and config["ps_link"] != ""
    has_user_id = config.get("user_id") and config["user_id"] != 0
    
    print("📊 Current Configuration Status:")
    print(f"   • Cookie:      {'✓ Set' if has_cookie else '✗ Not set'}")
    print(f"   • Server Link: {'✓ Set' if has_link else '✗ Not set'}")
    print(f"   • User ID:     {'✓ Set' if has_user_id else '✗ Not set'}")
    print()
    
    if has_cookie and has_link and has_user_id:
        print("✅ Configuration is complete!")
        reconfigure = input("\nReconfigure? (y/n): ").strip().lower()
        if reconfigure != 'y':
            print("\n👋 Setup cancelled. Run main_pc.py to start the script!")
            return
        print()
    
    if not has_cookie or input("\n🍪 Get new cookie? (y/n): ").strip().lower() == 'y':
        cookie = get_cookie_manually()
        if cookie:
            config["roblox_cookie"] = cookie
        else:
            print("\n⚠️  Cookie not set. You can set it later by editing config.json")
    
    if not has_link or input("\n🔗 Set new server link? (y/n): ").strip().lower() == 'y':
        link = get_private_server_link()
        if link:
            config["ps_link"] = link
        else:
            print("\n⚠️  Link not set. You can set it later by editing config.json")
    
    if not has_user_id or input("\n👤 Set new user ID? (y/n): ").strip().lower() == 'y':
        user_id = get_user_id()
        if user_id:
            config["user_id"] = user_id
    
    print("\n" + "="*60)
    print("  ⚙️  Advanced Settings (Optional)")
    print("="*60 + "\n")
    
    adjust = input("Adjust check interval and restart delay? (y/n): ").strip().lower()
    
    if adjust == 'y':
        print(f"\nCurrent check_interval: {config['check_interval']}s")
        print("(How often to check if you're still in the server)")
        new_interval = input("Enter new value (or press Enter to keep): ").strip()
        if new_interval:
            try:
                config["check_interval"] = int(new_interval)
                print(f"✓ Set to {new_interval}s")
            except ValueError:
                print("❌ Invalid number, keeping old value")
        
        print(f"\nCurrent restart_delay: {config['restart_delay']}s")
        print("(How long to wait after rejoining)")
        new_delay = input("Enter new value (or press Enter to keep): ").strip()
        if new_delay:
            try:
                config["restart_delay"] = int(new_delay)
                print(f"✓ Set to {new_delay}s")
            except ValueError:
                print("❌ Invalid number, keeping old value")
    
    save_config(config)
    
    print("\n" + "="*60)
    print("  ✅ Setup Complete!")
    print("="*60 + "\n")
    
    print("📋 Configuration Summary:")
    print(f"   • Cookie:        {'Set ✓' if config['roblox_cookie'] else 'Not set ✗'}")
    print(f"   • Server Link:   {'Set ✓' if config['ps_link'] else 'Not set ✗'}")
    print(f"   • User ID:       {config['user_id'] if config['user_id'] else 'Not set ✗'}")
    print(f"   • Check Every:   {config['check_interval']}s")
    print(f"   • Restart Delay: {config['restart_delay']}s")
    print()
    
    if config['roblox_cookie'] and config['ps_link'] and config['user_id']:
        print("🚀 Ready to go! Run main_pc.py to start the auto-rejoin script!")
    else:
        print("⚠️  Some settings are missing. Edit config.json to complete setup.")
    
    print()

if __name__ == "__main__":
    main()