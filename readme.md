# JIIT-Auto-Wi-Fi-Authenticator

A Python script that automatically logs you into college WiFi networks with captive portal authentication.

## Features

- Automatic login to college WiFi networks (AP-prefix networks)
- Event-triggered execution (runs only when WiFi connects - battery efficient)
- First-time setup for credential management
- Standalone executable - no Python installation required
- Works across multiple WiFi networks with same authentication portal

## Quick Start (Windows)

1. Place the three executables in the same folder:
	- `JIIT-AutoAuth.exe` (main program)
	- `Installer.exe` (installer that sets up Task Scheduler)
	- `Uninstaller.exe` (removes Task Scheduler entry and files)

2. Run `Installer.exe` (right-click → Run as administrator) and follow the prompts:
	- The installer will launch the main program to collect your WiFi credentials.
	- After entering credentials, the installer will create a Task Scheduler task that runs the main program when your network changes.

3. To remove the program, run `Uninstaller.exe` (also requires administrator rights).

## Configuration

- **WiFi Keywords**: `AP`, `ABB`, `HOSTEL`, `LRC`, `JIIT` — the program looks for SSIDs containing any of these keywords (case-insensitive). Modify `main.py` if you need additional keywords.
- **Portal URL**: `http://172.16.68.6:8090/httpclient.html`
- **Monitoring Mode**: `False` (event-triggered is recommended to save battery; set to `True` for continuous monitoring)

## Building from Source
```bash
pip install requests pyinstaller
pyinstaller --onefile --name "JIIT-AutoAuth" main.py
```

To build the other helper executables (installer and uninstaller) use:

```bash
pyinstaller --onefile --name "Installer" installer.py
pyinstaller --onefile --name "Uninstaller" uninstaller.py
```

## Requirements

- Windows OS (this release provides Windows executables only)
- Network: Cyberoam/Sophos captive portal (configured at `http://172.16.68.6:8090/httpclient.html`)

Note: Linux/macOS are not supported by the provided executables in this repository at this time.

## Download

Pre-built Windows executables are available from the release page:

[https://github.com/kartikeya042/JIIT-Auto-Wi-Fi-Authenticator/releases/tag/v1.0](https://github.com/kartikeya042/JIIT-Auto-Wi-Fi-Authenticator/releases/tag/v1.0)

Use the assets attached to that release to download `JIIT-AutoAuth.exe`, `Installer.exe`, and `Uninstaller.exe`.

## Usage & Security Notes

- The credentials are stored in a file in your user home directory: `%USERPROFILE%\.wifi_auto_login_config.json` (Windows). The `Uninstaller.exe` removes this file during uninstallation.
- The executables must be kept together in the same folder so the installer can find and run the main program during setup.
- Signed binaries are not included in this repository. Unsigned executables may trigger Windows SmartScreen warnings — consider code signing before distributing widely.

This project is designed for JIIT college WiFi networks. Modifications may be needed for other institutions with different portal systems.