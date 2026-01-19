import os
import json
import sqlite3
import shutil
import platform
import base64
from pathlib import Path

CONFIG_FILE = "config.json"

def print_header():
    print("\n" + "="*50)
    print("  🍪 Roblox Cookie Extractor (PC)")
    print("="*50 + "\n")

def get_browser_paths():
    system = platform.system()
    home = Path.home()
    
    paths = {}
    
    if system == "Windows":
        paths = {
            "Chrome": home / "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies",
            "Chrome (Old)": home / "AppData/Local/Google/Chrome/User Data/Default/Cookies",
            "Edge": home / "AppData/Local/Microsoft/Edge/User Data/Default/Network/Cookies",
            "Edge (Old)": home / "AppData/Local/Microsoft/Edge/User Data/Default/Cookies",
            "Opera": home / "AppData/Roaming/Opera Software/Opera Stable/Network/Cookies",
            "Opera GX": home / "AppData/Roaming/Opera Software/Opera GX Stable/Network/Cookies",
            "Brave": home / "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Network/Cookies",
            "Vivaldi": home / "AppData/Local/Vivaldi/User Data/Default/Network/Cookies",
        }
    elif system == "Darwin":
        paths = {
            "Chrome": home / "Library/Application Support/Google/Chrome/Default/Cookies",
            "Edge": home / "Library/Application Support/Microsoft Edge/Default/Cookies",
            "Opera": home / "Library/Application Support/com.operasoftware.Opera/Cookies",
            "Brave": home / "Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies",
        }
    elif system == "Linux":
        paths = {
            "Chrome": home / ".config/google-chrome/Default/Cookies",
            "Chromium": home / ".config/chromium/Default/Cookies",
            "Edge": home / ".config/microsoft-edge/Default/Cookies",
            "Opera": home / ".config/opera/Cookies",
            "Brave": home / ".config/BraveSoftware/Brave-Browser/Default/Cookies",
        }
    
    return paths

def get_firefox_paths():
    system = platform.system()
    home = Path.home()
    
    if system == "Windows":
        firefox_dir = home / "AppData/Roaming/Mozilla/Firefox/Profiles"
    elif system == "Darwin":
        firefox_dir = home / "Library/Application Support/Firefox/Profiles"
    elif system == "Linux":
        firefox_dir = home / ".mozilla/firefox"
    else:
        return []
    
    if not firefox_dir.exists():
        return []
    
    profiles = []
    for profile in firefox_dir.iterdir():
        if profile.is_dir():
            cookies_db = profile / "cookies.sqlite"
            if cookies_db.exists():
                profiles.append(("Firefox", cookies_db))
    
    return profiles

def decrypt_windows_chrome_cookie(encrypted_value):
    try:
        import win32crypt
        
        decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)
        return decrypted[1].decode('utf-8')
    except ImportError:
        return None
    except Exception as e:
        return None

def extract_chromium_cookie(db_path, browser_name):
    temp_db = "temp_cookies.db"
    
    try:
        shutil.copy2(db_path, temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, value, host_key, encrypted_value
            FROM cookies 
            WHERE (host_key LIKE '%roblox.com%' OR host_key LIKE '%.roblox.com%')
            AND name = '.ROBLOSECURITY'
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if os.path.exists(temp_db):
            os.remove(temp_db)
        
        if result:
            if result[1]:
                return result[1]
            
            if result[3] and platform.system() == "Windows":
                print(f"   → Cookie is encrypted, attempting decryption...")
                decrypted = decrypt_windows_chrome_cookie(result[3])
                if decrypted:
                    print(f"   ✓ Successfully decrypted!")
                    return decrypted
                else:
                    print(f"   ✗ Decryption failed (install pywin32: pip install pywin32)")
                    return None
            
            return None
        
        return None
        
    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            print(f"   ✗ Database locked - close {browser_name} first!")
        
        if os.path.exists(temp_db):
            os.remove(temp_db)
        return None
    except Exception as e:
        if os.path.exists(temp_db):
            os.remove(temp_db)
        return None

def extract_firefox_cookie(db_path):
    temp_db = "temp_firefox_cookies.db"
    
    try:
        shutil.copy2(db_path, temp_db)
        
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

def update_config_with_cookie(cookie_value):
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        else:
            config = {
                "ps_link": "https://www.roblox.com/share?code=YOUR_CODE&type=Server",
                "user_id": 0,
                "check_interval": 10,
                "restart_delay": 30
            }
        
        config["roblox_cookie"] = cookie_value
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        return False

def manual_cookie_guide():
    print("\n" + "="*50)
    print("  📖 Manual Cookie Extraction Guide")
    print("="*50 + "\n")
    
    print("Since automatic extraction failed, follow these steps:\n")
    
    print("1️⃣  Open your browser (Chrome, Edge, or Firefox)")
    print("2️⃣  Go to https://www.roblox.com and login")
    print("3️⃣  Press F12 to open Developer Tools")
    print("4️⃣  Click on 'Application' tab (Chrome/Edge) or 'Storage' tab (Firefox)")
    print("5️⃣  In the sidebar, click: Cookies → https://www.roblox.com")
    print("6️⃣  Find the cookie named '.ROBLOSECURITY'")
    print("7️⃣  Double-click the 'Value' field and copy it (Ctrl+C)")
    print("8️⃣  Paste it into config.json as 'roblox_cookie'\n")
    
    print("📝 The cookie value should look like:")
    print("   _|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this...\n")
    
    print("⚠️  IMPORTANT:")
    print("   • Copy the ENTIRE value (it's very long)")
    print("   • Do NOT share this cookie with anyone")
    print("   • This cookie = your password!\n")

def main():
    print_header()
    
    print(f"💻 Operating System: {platform.system()}\n")
    
    if platform.system() == "Windows":
        try:
            import win32crypt
            print("✓ pywin32 installed (can decrypt Chrome/Edge cookies)")
        except ImportError:
            print("⚠️  pywin32 not installed - encrypted cookies cannot be decrypted")
            print("   Install with: pip install pywin32")
            print("   (Or use manual extraction method)\n")
    
    print("⚠️  IMPORTANT:")
    print("   Please CLOSE all browsers before continuing!")
    print("   This prevents database locking issues.\n")
    
    input("Press Enter when all browsers are closed...")
    print()
    
    print("🔍 Searching for browser cookies...\n")
    
    cookie_found = False
    cookie_value = None
    found_in = None
    
    browser_paths = get_browser_paths()
    
    for browser_name, db_path in browser_paths.items():
        if not db_path.exists():
            continue
        
        print(f"📱 Checking {browser_name}...")
        print(f"   Path: {db_path}")
        
        cookie = extract_chromium_cookie(db_path, browser_name)
        if cookie:
            cookie_value = cookie
            cookie_found = True
            found_in = browser_name
            print(f"   ✓ Cookie found!")
            break
        else:
            print(f"   ✗ No Roblox cookie found")
    
    if not cookie_found:
        firefox_profiles = get_firefox_paths()
        
        for browser_name, db_path in firefox_profiles:
            print(f"\n📱 Checking {browser_name}...")
            print(f"   Profile: {db_path.parent.name}")
            
            cookie = extract_firefox_cookie(db_path)
            if cookie:
                cookie_value = cookie
                cookie_found = True
                found_in = f"{browser_name} ({db_path.parent.name})"
                print(f"   ✓ Cookie found!")
                break
            else:
                print(f"   ✗ No Roblox cookie found")
    
    print("\n" + "="*50)
    
    if cookie_found and cookie_value:
        print(f"\n✅ SUCCESS! Cookie found in {found_in}!\n")
        
        preview = cookie_value[:80] + "..." if len(cookie_value) > 80 else cookie_value
        print(f"🍪 Cookie preview: {preview}\n")
        
        print("💾 Updating config.json...")
        if update_config_with_cookie(cookie_value):
            print("✓ config.json updated successfully!")
            print(f"\n📝 Cookie length: {len(cookie_value)} characters")
            print("\n✨ You can now run main_pc.py!")
        else:
            print("⚠️  Failed to update config.json")
            print(f"\nManually add this to config.json:")
            print(f'"roblox_cookie": "{cookie_value}"')
    else:
        print("\n❌ Cookie not found in any browser!\n")
        
        manual_cookie_guide()
    
    print("="*50 + "\n")

if __name__ == "__main__":
    main()