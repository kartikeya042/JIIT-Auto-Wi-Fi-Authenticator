import os
import sys
import subprocess
from pathlib import Path
import ctypes

# Installation directory
INSTALL_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'JIIT-WifiAutoAuthenticator')

def is_admin():
    """Check if script is running with admin privileges"""
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def run_as_admin():
    """Re-run the script with admin privileges"""
    if sys.platform == 'win32':
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False
    return True


def remove_task_scheduler_task():
    """Remove the Task Scheduler task"""
    task_name = "JIIT-AutoAuth"
    
    try:
        # Check if task exists
        result = subprocess.run(
            ['schtasks', '/Query', '/TN', task_name],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return True, "Task was not found (already removed or never installed)"
        
        # Delete the task
        result = subprocess.run(
            ['schtasks', '/Delete', '/TN', task_name, '/F'],
            capture_output=True,
            text=True,
            check=True
        )
        
        return True, "Task Scheduler entry removed successfully!"
    
    except subprocess.CalledProcessError as e:
        return False, f"Error removing task: {e.stderr}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def remove_config_file():
    """Remove the saved credentials configuration file"""
    config_file = Path.home() / '.wifi_auto_login_config.json'
    
    try:
        if config_file.exists():
            config_file.unlink()
            return True, f"Credentials file removed: {config_file}"
        else:
            return True, "No credentials file found (already removed)"
    except Exception as e:
        return False, f"Error removing credentials file: {str(e)}"


def get_program_files():
    """Get list of program files using keyword-based detection"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        program_dir = Path(sys.executable).parent
    else:
        # Running as script
        program_dir = Path(__file__).parent
    
    files = []
    
    # Keywords to identify related executables (case-insensitive)
    keywords = ["jiit", "wifi", "auto", "auth", "installer", "uninstaller"]
    
    # Directories to search
    search_dirs = [
        program_dir,
        program_dir.parent,
        Path(INSTALL_DIR)
    ]
    
    # Search for matching executables
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        try:
            for file_path in search_dir.glob("*.exe"):
                # Check if filename contains any keywords (case-insensitive)
                filename_lower = file_path.name.lower()
                if any(keyword in filename_lower for keyword in keywords):
                    # Avoid duplicates
                    if file_path not in files:
                        files.append(file_path)
        except Exception as e:
            print(f"  ⚠ Error searching {search_dir}: {e}")
    
    return files


def create_self_delete_script():
    """Create a batch script that will delete the uninstaller after it exits"""
    if getattr(sys, 'frozen', False):
        uninstaller_path = Path(sys.executable)
        batch_script = uninstaller_path.parent / "cleanup.bat"
        
        batch_content = f'''@echo off
timeout /t 10 /nobreak >nul
del /f /q "{uninstaller_path}"
del /f /q "%~f0"
'''
        
        try:
            with open(batch_script, 'w') as f:
                f.write(batch_content)
            
            # Run the batch script
            subprocess.Popen(
                [str(batch_script)],
                creationflags=subprocess.CREATE_NO_WINDOW,
                shell=True
            )
            return True
        except:
            return False
    return False


def main():
    print("=" * 60)
    print("   JIIT WifiAutoAuthenticator - UNINSTALLER")
    print("=" * 60)
    print()
    
    # Check for admin privileges
    if not is_admin():
        print("⚠ This uninstaller needs Administrator privileges.")
        print("  Requesting admin access...")
        print()
        if not run_as_admin():
            sys.exit(0)
        return
    
    print("✓ Running with Administrator privileges")
    print()
    
    # Confirm uninstallation
    print("This will remove:")
    print("  • Auto-login Task Scheduler entry")
    print("  • Saved WiFi credentials")
    print("  • Program files (optional)")
    print()
    
    confirm = input("Are you sure you want to uninstall? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("\nUninstallation cancelled.")
        input("\nPress Enter to exit...")
        sys.exit(0)
    
    print()
    print("=" * 60)
    print("Starting Uninstallation...")
    print("=" * 60)
    print()
    
    # Step 1: Remove Task Scheduler task
    print("[1/3] Removing Task Scheduler entry...")
    success, message = remove_task_scheduler_task()
    if success:
        print(f"  ✓ {message}")
    else:
        print(f"  ✗ {message}")
    print()
    
    # Step 2: Remove config file
    print("[2/3] Removing saved credentials...")
    success, message = remove_config_file()
    if success:
        print(f"  ✓ {message}")
    else:
        print(f"  ✗ {message}")
    print()
    
    # Step 3: Ask about program files
    print("[3/3] Program files:")
    program_files = get_program_files()
    
    if program_files:
        print("\n  Found the following program files:")
        for file in program_files:
            print(f"    • {file.name}")
        print()
        
        delete_files = input("  Delete these program files? (yes/no): ").strip().lower()
        
        if delete_files in ['yes', 'y']:
            deleted = []
            failed = []
            
            for file in program_files:
                # Don't try to delete the uninstaller while it's running
                if file.name == "Uninstaller.exe":
                    continue
                
                try:
                    file.unlink()
                    deleted.append(file.name)
                except Exception as e:
                    failed.append(f"{file.name} ({e})")
            
            if deleted:
                print("\n  ✓ Deleted:")
                for name in deleted:
                    print(f"    • {name}")
            
            if failed:
                print("\n  ✗ Failed to delete:")
                for name in failed:
                    print(f"    • {name}")
            
            # Schedule uninstaller deletion
            print("\n  ⏳ Scheduling Uninstaller.exe deletion...")
            if create_self_delete_script():
                print("  ✓ Uninstaller will be deleted after exit")
            else:
                print("  ⚠ Please manually delete Uninstaller.exe")
        else:
            print("\n  ⊘ Program files kept")
    else:
        print("  ℹ No program files found in current directory")
    
    print()
    print("=" * 60)
    print("   UNINSTALLATION COMPLETE!")
    print("=" * 60)
    print()
    print("What was removed:")
    print("  ✓ Task Scheduler auto-login task")
    print("  ✓ Saved WiFi credentials")
    
    if delete_files in ['yes', 'y']:
        print("  ✓ Program files")
    
    print()
    print("WiFi auto-login has been disabled.")
    print("You will now need to login manually to college WiFi.")
    print()
    
    if delete_files in ['yes', 'y']:
        print("Note: Uninstaller.exe will be deleted in 10 seconds after closing.")
        print()
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nUninstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)