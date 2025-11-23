# JIIT-Auto-Wi-Fi-Authenticator

A Python script that automatically logs you into college WiFi networks with captive portal authentication.

## Features

- Automatic login to college WiFi networks (AP-prefix networks)
- Event-triggered execution (runs only when WiFi connects - battery efficient)
- First-time setup for credential management
- Standalone executable - no Python installation required
- Works across multiple WiFi networks with same authentication portal

## Quick Start

1. Run `JIIT-WiFiAutoLogin.exe`
2. Enter your WiFi credentials on first run
3. Set up Task Scheduler event trigger for automatic login on WiFi connection

## Configuration

- **WiFi Prefix**: `AP` (modify `WIFI_PREFIX` to match your network naming)
- **Portal URL**: `http://172.16.68.6:8090/httpclient.html`
- **Monitoring Mode**: `False` (battery-efficient event-triggered mode)

## Building from Source
```bash
pip install requests pyinstaller
pyinstaller --onefile --name "JIIT-WiFiAutoLogin" main.py
```

## Requirements

- Windows OS
- Network: Cyberoam/Sophos captive portal

## Note

This project is designed for JIIT college WiFi networks. Modifications may be needed for other institutions with different portal systems.