# site_closeout_checker

## Build

To build executables run the following commands from the root directory
```
pyinstaller site_closeout_checker.py --onefile --name SiteCloseoutChecker.exe --paths=modules\ --icon roar.ico
pyinstaller modules\sshtunnel_launcher.py --onefile --name SSHTunnelLauncher.exe --paths=modules\ --icon roar.ico
```