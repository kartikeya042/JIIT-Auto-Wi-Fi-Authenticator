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
    """Get the path of the main executable"""
    # When running as script
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent / "JIIT-AutoAuth.exe"
    else:
        # Running as script - look for exe in same directory
        script_dir = Path(__file__).parent
        exe_path = script_dir / "JIIT-AutoAuth.exe"
        if not exe_path.exists():
            exe_path = script_dir / "dist" / "JIIT-AutoAuth.exe"
        return exe_path


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
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="Microsoft-Windows-WLAN-AutoConfig/Operational"&gt;&lt;Select Path="Microsoft-Windows-WLAN-AutoConfig/Operational"&gt;*[System[Provider[@Name='Microsoft-Windows-WLAN-AutoConfig'] and EventID=8001]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
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
    print("   JIIT WiFi Auto-Authenticator - INSTALLER")
    print("=" * 60)
    print()
    
    # Check for admin privileges
    if not is_admin():
        print("⚠ Administrator privileges required.")
        print("  Requesting elevation...")
        print()
        if not run_as_admin():
            sys.exit(0)
        return
    
    print("✓ Administrator access granted")
    print()
    
    # Find the main executable
    exe_path = get_exe_path()
    
    if not exe_path.exists():
        print("✗ ERROR: Main program not found")
        print(f"  Looking for: {exe_path.name}")
        print(f"  Searched in: {exe_path.parent}")
        print()
        print("Ensure the following files are in the same directory:")
        print(f"  • {exe_path.name} (main program)")
        print("  • Installer.exe (this file)")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print(f"✓ Located: {exe_path.name}")
    print()
    
    # Run the main program once for credential setup
    print("=" * 60)
    print("STEP 1: Configure WiFi Credentials")
    print("=" * 60)
    print()
    print("You will now be prompted to enter your JIIT WiFi credentials.")
    print("These will be securely saved for automatic authentication.")
    print()
    input("Press Enter to continue...")
    print()
    
    try:
        subprocess.run([str(exe_path)], check=True)
    except subprocess.CalledProcessError:
        print("\n⚠ Credential setup was cancelled or incomplete.")
        choice = input("Continue with Task Scheduler setup? (y/n): ")
        if choice.lower() != 'y':
            print("\nInstallation cancelled.")
            input("\nPress Enter to exit...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInstallation interrupted.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("STEP 2: Configure Automatic Authentication")
    print("=" * 60)
    print()
    print("Setting up Task Scheduler to run on WiFi connection...")
    
    success, message = create_task_scheduler_task(exe_path)
    
    print()
    if success:
        print("✓ " + message)
        print()
        print("=" * 60)
        print("   INSTALLATION SUCCESSFUL!")
        print("=" * 60)
        print()
        print("Setup Complete:")
        print("  ✓ Task Scheduler configured")
        print("  ✓ Auto-authentication enabled")
        print()
        print("How it works:")
        print("  • Detects when you connect to JIIT WiFi networks")
        print("  • Automatically authenticates using saved credentials")
        print("  • No manual intervention required")
        print()
        print("Supported networks: AP, ABB, HOSTEL, LRC, JIIT")
        print()
        print("To uninstall, run the Uninstaller.exe")
        print()
    else:
        print("✗ " + message)
        print()
        print("=" * 60)
        print("   INSTALLATION FAILED")
        print("=" * 60)
        print()
        print("Task Scheduler setup failed. Please check permissions.")
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