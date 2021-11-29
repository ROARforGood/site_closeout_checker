# site_closeout_checker

## Setup

1. Download the latest verison from the [repository release page](https://github.com/ROARforGood/site_closeout_checker/releases).
2. Extract the files then copy the SSH keys into the keys folder. You'll need to contact Rich or a sys admin for the keys.
3. Make sure your IP aaddress is whitelisted for access, (Contact Rish or a sys admin to whitelist your IP).

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
