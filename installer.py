import os
import sys
import subprocess
from pathlib import Path
import shutil

def is_admin():
    """Check if script is running with admin privileges"""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def run_as_admin():
    """Re-run the script with admin privileges"""
    if sys.platform == 'win32':
        import ctypes
        if not is_admin():
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False
    return True


def get_exe_path():
    """Get the path of the main executable using keyword detection"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        search_dir = Path(sys.executable).parent
    else:
        # Running as script
        search_dir = Path(__file__).parent
    
    # Keywords to identify main executable
    keywords = ["jiit", "wifi", "auto", "auth"]
    
    # Search for matching exe
    try:
        for exe_file in search_dir.glob("*.exe"):
            filename_lower = exe_file.name.lower()
            # Skip installer and uninstaller
            if "installer" in filename_lower or "uninstaller" in filename_lower:
                continue
            # Check if it matches our keywords
            if any(keyword in filename_lower for keyword in keywords):
                return exe_file
        
        # Also check dist folder
        dist_dir = search_dir / "dist"
        if dist_dir.exists():
            for exe_file in dist_dir.glob("*.exe"):
                filename_lower = exe_file.name.lower()
                if "installer" not in filename_lower and "uninstaller" not in filename_lower:
                    if any(keyword in filename_lower for keyword in keywords):
                        return exe_file
    except:
        pass
    
    # Fallback to default name
    return search_dir / "JIIT-AutoAuth.exe"


def create_task_scheduler_task(exe_path):
    """Create the Task Scheduler task using XML"""
    
    task_name = "JIIT-AutoAuth"
    
    # XML for the task
    task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Automatically logs into JIIT college WiFi when connected</Description>
    <URI>\\{task_name}</URI>
  </RegistrationInfo>
  <Triggers>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="Microsoft-Windows-NetworkProfile/Operational"&gt;&lt;Select Path="Microsoft-Windows-NetworkProfile/Operational"&gt;*[System[Provider[@Name='Microsoft-Windows-NetworkProfile'] and EventID=10000]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
      <Delay>PT5S</Delay>
    </EventTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
    </Exec>
  </Actions>
</Task>'''
    
    # Save XML to temp file
    temp_xml = Path.home() / "temp_task.xml"
    with open(temp_xml, 'w', encoding='utf-16') as f:
        f.write(task_xml)
    
    try:
        # Delete existing task if it exists
        subprocess.run(
            ['schtasks', '/Delete', '/TN', task_name, '/F'],
            capture_output=True,
            check=False
        )
        
        # Create the task
        result = subprocess.run(
            ['schtasks', '/Create', '/XML', str(temp_xml), '/TN', task_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Clean up temp file
        temp_xml.unlink()
        
        return True, "Task created successfully!"
    
    except subprocess.CalledProcessError as e:
        return False, f"Error creating task: {e.stderr}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
    finally:
        # Clean up temp file if it still exists
        if temp_xml.exists():
            temp_xml.unlink()


def main():
    print("=" * 60)
    print("   JIIT WiFi Auto-Login - INSTALLER")
    print("=" * 60)
    print()
    
    # Check for admin privileges
    if not is_admin():
        print("⚠ This installer needs Administrator privileges.")
        print("  Requesting admin access...")
        print()
        if not run_as_admin():
            sys.exit(0)
        return
    
    print("✓ Running with Administrator privileges")
    print()
    
    # Find the main executable
    exe_path = get_exe_path()
    
    if not exe_path.exists():
        print("✗ ERROR: Could not find JIIT-WiFiAutoLogin.exe")
        print(f"  Expected location: {exe_path}")
        print()
        print("Please ensure both files are in the same folder:")
        print("  - JIIT-WiFiAutoLogin.exe (main program)")
        print("  - Installer.exe (this installer)")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print(f"✓ Found main program: {exe_path}")
    print()
    
    # Run the main program once for credential setup
    print("=" * 60)
    print("STEP 1: First-Time Credential Setup")
    print("=" * 60)
    print()
    print("The WiFi login program will now run.")
    print("Please enter your college WiFi credentials when prompted.")
    print()
    input("Press Enter to continue...")
    print()
    
    try:
        subprocess.run([str(exe_path)], check=True)
    except subprocess.CalledProcessError:
        print("\n⚠ Setup was cancelled or failed.")
        choice = input("Do you want to continue with Task Scheduler setup anyway? (y/n): ")
        if choice.lower() != 'y':
            print("Installation cancelled.")
            input("\nPress Enter to exit...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("STEP 2: Setting up Auto-Login on WiFi Connect")
    print("=" * 60)
    print()
    print("Creating Task Scheduler task...")
    
    success, message = create_task_scheduler_task(exe_path)
    
    print()
    if success:
        print("✓ " + message)
        print()
        print("=" * 60)
        print("   INSTALLATION COMPLETE!")
        print("=" * 60)
        print()
        print("What happens now:")
        print("  • Whenever you connect to college WiFi (AP networks)")
        print("  • The script will automatically log you in")
        print("  • No manual action needed!")
        print()
        print("To test: Disconnect and reconnect to college WiFi")
        print()
        print("To uninstall:")
        print("  1. Open Task Scheduler (Win+R → taskschd.msc)")
        print("  2. Find 'JIIT-WiFi-AutoLogin' in the list")
        print("  3. Right-click → Delete")
        print()
    else:
        print("✗ " + message)
        print()
        print("=" * 60)
        print("   INSTALLATION FAILED")
        print("=" * 60)
        print()
        print("Please try manual setup or contact support.")
        print()
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)