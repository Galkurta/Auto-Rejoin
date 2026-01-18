import os
import json
import sqlite3
import subprocess
import shutil
from pathlib import Path

CONFIG_FILE = "config.json"

def print_header():
    print("\n" + "="*50)
    print("  🍪 Roblox Cookie Extractor")
    print("="*50 + "\n")

def check_root():
    try:
        result = subprocess.run(['su', '-c', 'id'], 
                              capture_output=True, 
                              timeout=5)
        return result.returncode == 0
    except:
        return False

def run_root_cmd(cmd):
    try:
        result = subprocess.run(['su', '-c', cmd],
                              capture_output=True,
                              text=True,
                              timeout=10)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_package_installed(package_name):
    success, output = run_root_cmd(f'pm list packages | grep {package_name}')
    return success and package_name in output

def find_all_browser_data():
    browsers = {
        'Chrome': 'com.android.chrome',
        'Chrome Beta': 'com.chrome.beta',
        'Chrome Dev': 'com.chrome.dev',
        'Chrome Canary': 'com.chrome.canary',
        'Edge': 'com.microsoft.emmx',
        'Firefox': 'org.mozilla.firefox',
        'Opera': 'com.opera.browser',
        'Samsung Internet': 'com.sec.android.app.sbrowser',
        'Brave': 'com.brave.browser',
        'Kiwi Browser': 'com.kiwibrowser.browser',
        'DuckDuckGo': 'com.duckduckgo.mobile.android',
        'Roblox App': 'com.roblox.client'
    }
    
    installed = {}
    print("🔍 Detecting installed apps...\n")
    
    for name, package in browsers.items():
        if check_package_installed(package):
            print(f"   ✓ {name}: Installed")
            installed[name] = package
        else:
            print(f"   ✗ {name}: Not found")
    
    return installed

def find_cookie_databases(package_name):
    """Find all possible cookie database locations for a package."""
    base_path = f"/data/data/{package_name}"
    
    # Common paths for different browsers
    possible_paths = [
        f"{base_path}/app_chrome/Default/Cookies",
        f"{base_path}/app_chrome/Profile */Cookies",
        f"{base_path}/app_msedge/Default/Cookies",
        f"{base_path}/databases/webviewCookiesChromium.db",
        f"{base_path}/app_webview/Cookies",
        f"{base_path}/app_webview/Default/Cookies",
    ]
    
    # Firefox uses different structure
    if 'firefox' in package_name:
        success, output = run_root_cmd(f'find {base_path} -name "cookies.sqlite" 2>/dev/null')
        if success and output:
            return output.strip().split('\n')
    
    # Check all possible paths
    found_paths = []
    for path in possible_paths:
        if '*' in path:
            # Wildcard search
            success, output = run_root_cmd(f'ls {path} 2>/dev/null')
            if success and output:
                for line in output.split('\n'):
                    if line.strip():
                        found_paths.append(line.strip())
        else:
            success, _ = run_root_cmd(f'test -f {path} && echo "exists"')
            if success:
                found_paths.append(path)
    
    return found_paths

def copy_database(db_path, temp_path):
    try:
        success, _ = run_root_cmd(f'cp "{db_path}" "{temp_path}"')
        if not success:
            return False
        
        run_root_cmd(f'chmod 666 "{temp_path}"')
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

def main():
    print_header()
    
    if not check_root():
        print("❌ Root access required!")
        print("   This script needs root to access browser data.\n")
        return
    
    print("✓ Root access granted\n")
    
    installed_browsers = find_all_browser_data()
    
    if not installed_browsers:
        print("\n❌ No supported browsers/apps found!\n")
        print("💡 Please install Chrome, Edge, or Firefox and login to Roblox\n")
        return
    
    print("\n" + "="*50)
    print("  🔎 Searching for Roblox cookie...")
    print("="*50 + "\n")
    
    cookie_found = False
    cookie_value = None
    found_in = None
    
    for browser_name, package_name in installed_browsers.items():
        print(f"📱 Checking {browser_name}...")
        
        db_paths = find_cookie_databases(package_name)
        
        if not db_paths:
            print(f"   ✗ No cookie database found")
            continue
        
        print(f"   ✓ Found {len(db_paths)} database(s)")
        
        for db_path in db_paths:
            print(f"   → Extracting from: {os.path.basename(db_path)}...")
            
            if 'firefox' in package_name:
                cookie = extract_cookie_firefox(db_path)
            else:
                cookie = extract_cookie_chromium(db_path)
            
            if cookie:
                cookie_value = cookie
                cookie_found = True
                found_in = browser_name
                print(f"   ✓ Cookie found!")
                break
        
        if cookie_found:
            break
        else:
            print(f"   ✗ No Roblox cookie in this browser")
    
    print("\n" + "="*50)
    
    if cookie_found and cookie_value:
        print(f"\n✅ SUCCESS! Cookie found in {found_in}!\n")
        
        preview = cookie_value[:80] + "..." if len(cookie_value) > 80 else cookie_value
        print(f"🍪 Cookie preview: {preview}\n")
        
        print("💾 Updating config.json...")
        if update_config_with_cookie(cookie_value):
            print("✓ config.json updated successfully!")
            print(f"\n📝 Cookie length: {len(cookie_value)} characters")
            print("\n✨ You can now run the auto-rejoin script!")
        else:
            print("⚠ Failed to update config.json")
            print(f"\nManually add this to config.json:")
            print(f'"roblox_cookie": "{cookie_value}"')
    else:
        print("\n❌ Cookie not found in any installed browser!\n")
        print("📋 Possible reasons:")
        print("   1. Haven't logged into Roblox.com in any browser")
        print("   2. Browser data was cleared")
        print("   3. Cookie expired or was deleted\n")
        print("💡 Solution:")
        print("   1. Open Chrome/Edge/Firefox on this device")
        print("   2. Go to https://www.roblox.com")
        print("   3. Login to your Roblox account")
        print("   4. Wait 5 seconds after login")
        print("   5. Run this script again\n")
        print("📱 Installed browsers detected:")
        for browser in installed_browsers.keys():
            print(f"   • {browser}")
        print()
    
    print("="*50 + "\n")

if __name__ == "__main__":
    main()