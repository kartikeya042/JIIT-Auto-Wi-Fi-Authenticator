import requests
import time
import subprocess
import sys
import json
import os
import tempfile
from pathlib import Path

# Configuration file path
CONFIG_FILE = Path.home() / '.wifi_auto_login_config.json'

# Lock file to prevent multiple instances
LOCK_FILE = Path(tempfile.gettempdir()) / "jiit_wifi_auth.lock"

# Portal configuration
PORTAL_URL = "http://172.16.68.6:8090/httpclient.html"

# Auto-detect college WiFi networks
# Recognize SSIDs that contain any of these keywords (case-insensitive)
WIFI_KEYWORDS = ["AP", "ABB", "HOSTEL", "LRC", "JIIT"]

# Monitoring mode - set to True to run continuously (NOT RECOMMENDED for battery)
# Set to False for event-triggered mode (RECOMMENDED)
MONITOR_MODE = False


def acquire_lock():
    """Acquire lock to prevent multiple instances"""
    try:
        if LOCK_FILE.exists():
            # Check if lock is stale (older than 2 minutes)
            lock_age = time.time() - LOCK_FILE.stat().st_mtime
            if lock_age < 120:  # 2 minutes
                return False
            # Remove stale lock
            LOCK_FILE.unlink()
        
        # Create lock file
        LOCK_FILE.write_text(str(os.getpid()))
        return True
    except:
        return False


def release_lock():
    """Release the lock"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except:
        pass


def load_credentials():
    """Load saved credentials from config file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return None


def save_credentials(username, password):
    """Save credentials to config file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'username': username, 'password': password}, f)
        print(f"✓ Credentials saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False


def setup_credentials():
    """Interactive setup to get user credentials"""
    print("\n" + "=" * 50)
    print("FIRST TIME SETUP")
    print("=" * 50)
    print("Please enter your college WiFi credentials.")
    print("These will be saved securely for automatic login.\n")
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("✗ Username and password cannot be empty")
        return None
    
    confirm = input("\nSave these credentials? (y/n): ").strip().lower()
    if confirm == 'y':
        if save_credentials(username, password):
            return {'username': username, 'password': password}
    
    return None


def get_connected_wifi():
    """Get the currently connected WiFi network name"""
    try:
        result = subprocess.run(
            ['netsh', 'wlan', 'show', 'interfaces'],
            capture_output=True,
            text=True,
            check=True
        )
        
        for line in result.stdout.split('\n'):
            if 'SSID' in line and 'BSSID' not in line:
                return line.split(':')[1].strip()
    except:
        pass
    return None


def check_internet_connection():
    """Check if we can access the internet"""
    try:
        response = requests.get('http://www.gstatic.com/generate_204', 
                               timeout=5, 
                               allow_redirects=False)
        return response.status_code == 204
    except:
        return False


def login_to_portal(username, password):
    """Login to the captive portal"""
    try:
        session = requests.Session()
        
        # Prepare login data
        login_data = {
            'mode': '191',
            'username': username,
            'password': password,
            'a': str(int(time.time() * 1000)),
            'producttype': '0'
        }
        
        # Submit login
        login_url = PORTAL_URL.rsplit('/', 1)[0] + '/login.xml'
        response = session.post(login_url, data=login_data, timeout=10)
        
        # Wait and check if login was successful
        time.sleep(3)
        return check_internet_connection()
    except:
        return False


def attempt_login(username, password, current_wifi):
    """Attempt to login to the current WiFi"""
    print(f"Connected to: {current_wifi}")
    
    # Check if already authenticated
    if check_internet_connection():
        print("✓ Internet already accessible")
        return True
    
    # Attempt login
    print("Logging in...")
    if login_to_portal(username, password):
        print("✓ Login successful!")
        return True
    else:
        print("✗ Login failed")
        return False


def monitor_wifi_changes(username, password):
    """Continuously monitor for WiFi changes and auto-login"""
    print("\n" + "=" * 50)
    print("MONITORING MODE - Watching for WiFi changes...")
    print("Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    last_wifi = None
    last_login_attempt = {}
    
    while True:
        try:
            current_wifi = get_connected_wifi()
            
            # If WiFi changed
            if current_wifi != last_wifi:
                if current_wifi:
                    print(f"\n[{time.strftime('%H:%M:%S')}] WiFi changed to: {current_wifi}")
                    
                    # Check if it's a college WiFi (contains any keyword)
                    if any(k.lower() in current_wifi.lower() for k in WIFI_KEYWORDS):
                        print("→ College WiFi detected!")
                        
                        # Avoid repeated login attempts within 60 seconds
                        last_attempt_time = last_login_attempt.get(current_wifi, 0)
                        if time.time() - last_attempt_time > 60:
                            attempt_login(username, password, current_wifi)
                            last_login_attempt[current_wifi] = time.time()
                        else:
                            print("→ Recent login attempt, skipping...")
                    else:
                        print("→ Not a college WiFi, ignoring")
                else:
                    print(f"\n[{time.strftime('%H:%M:%S')}] WiFi disconnected")
                
                last_wifi = current_wifi
            
            # Check every 3 seconds
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error in monitoring: {e}")
            time.sleep(5)


def main():
    print("=" * 50)
    print("College WiFi Auto-Login Script")
    print("=" * 50)
    
    # Check if another instance is running
    if not acquire_lock():
        print("\n⚠ Another instance is already running. Exiting.")
        return
    
    try:
        # First, check if internet is already accessible
        print("\nChecking internet connectivity...")
        if check_internet_connection():
            print("✓ Internet already accessible. No login needed.")
            print("=" * 50)
            return
        
        print("✗ No internet access detected.")
        print("Proceeding with authentication...\n")
        
        # Load or setup credentials
        credentials = load_credentials()
        
        if not credentials:
            credentials = setup_credentials()
            if not credentials:
                print("\n✗ Setup cancelled or failed")
                return
        else:
            print(f"✓ Loaded credentials for user: {credentials['username']}")
        
        username = credentials['username']
        password = credentials['password']
        
        # Check if we should run in monitoring mode
        if MONITOR_MODE:
            monitor_wifi_changes(username, password)
        else:
            # Single attempt mode (original behavior)
            max_attempts = 5
            
            for attempt in range(1, max_attempts + 1):
                print(f"\nAttempt {attempt}/{max_attempts}")
                
                current_wifi = get_connected_wifi()
                if not current_wifi:
                    print("No WiFi connected, waiting...")
                    time.sleep(5)
                    continue
                
                # Check if WiFi name contains any of the configured keywords
                if not any(k.lower() in current_wifi.lower() for k in WIFI_KEYWORDS):
                    print(f"Not a college network: {current_wifi}")
                    print(f"(Looking for networks matching: {', '.join(WIFI_KEYWORDS)})")
                    time.sleep(5)
                    continue
                
                if attempt_login(username, password, current_wifi):
                    return
                
                print("Retrying...")
                time.sleep(10)
            
            print("\n✗ Failed after maximum attempts")
            print("Your credentials might be incorrect.")
            print(f"To reset, delete the file: {CONFIG_FILE}")
    finally:
        release_lock()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        release_lock()
        sys.exit(0)