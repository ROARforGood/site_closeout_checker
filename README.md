# site_closeout_checker

## Setup

1. Download the latest verison from the [repository release page](https://github.com/ROARforGood/site_closeout_checker/releases).
2. Extract the files to a folder somewhere within your user directory (for example C:\Users\YourUsername\Documents\).
3. Copy the SSH keys into the keys folder (contact Rich or a sys admin for the keys).
4. Make sure your IP aaddress is whitelisted for access (contact Rich or a sys admin to whitelist your IP).
5. create a config_db.ini file based on the config_db.ini.template with database credentials
6. Create a config.ini file based on the config.ini.template, enter the filepath of your MQTT crentials and target environment

## Usage

Run `SiteCloseoutChecker.exe` and enter the info requested by the prompts.

## Develop

### Build

To build executables run the following commands from the root directory
```
pyinstaller site_closeout_checker.py --onefile --name SiteCloseoutChecker.exe --distpath . --paths=modules\ --icon roar.ico
```
