# site_closeout_checker

## Setup

Download the latest verison from the release page.

You'll need to contact Rich or a sys admin for the keys, and to whitelist your IP address in order for the program to work.

## Usage

Run `SSHTunnelLauncher.exe` to launch the SSH tunnel.  If your set up properly this should run without errors, leave the window open.

Run `SiteCloseoutChecker.exe` and enter the info requested by the prompts.

## Develop

### Build

To build executables run the following commands from the root directory
```
pyinstaller site_closeout_checker.py --onefile --name SiteCloseoutChecker.exe --paths=modules\ --icon roar.ico
pyinstaller modules\sshtunnel_launcher.py --onefile --name SSHTunnelLauncher.exe --paths=modules\ --icon roar.ico
```
