# gateway-programmer-freertos

## Setup

Currently some specialized knowledge is required to setup and configure gateway programming,  contact Rich Nelson with any questions.

This setup for this process has some overlap with the [crushem beacon provisioning](https://github.com/ROARforGood/crushem_provisioning) process.

You can find the linked instructions  for installing:
- [Python](https://github.com/ROARforGood/crushem_provisioning#python)
- [Git](https://github.com/ROARforGood/crushem_provisioning#git)
- [Nordic Command Line Tools](https://github.com/ROARforGood/crushem_provisioning#nordic-tools)
- [SSH Github Access](https://github.com/ROARforGood/crushem_provisioning#ssh-setup)
- [Label printer Setup](https://github.com/ROARforGood/crushem_provisioning#label-printer-setup)

### Copy Firmware/Dev Env folders

Copy the gateway dev and mingw32 folder from the thumb drive to the root of the C:/ drive

### Configure AWS credentials

- open mingw32.exe and enter the command aws configure.  Input your AWS IAM credentials.


### Clone the Repo

Clone the repo with the command
```
git clone git@github.com:ROARforGood/gateway-programmer-freertos.git
```

### Install virtual env and packages
cd into the downloaded directory
```
cd crushem_provisioning
```

Setup the virtual environment and install the required packaged by running the command ```python -m venv .venv``` in the crushem_provisioning project root directory.

You can now run `Update.bat` to set up the program dependencies.

### Configure COM port

The COM port for the ESP32 (wifi chip) programmer, needs to be set within the dev environment.

in the mingw32 terminal navigate to the firmware root directory, (this can be done manually, or in the process of programming a gateway a window will open and navigate to the correct directory.

Enter the dev env config with the command `make menuconfig`,

### Config.ini

If not already done, you'll need to create a config.ini file based on the config.ini.template.  And set the correct values and paths for your computer.

### IP whitelist

This program requires use of an SSH tunnel, your IP address will need to be updated.  To do this file an issue with a request in the [purple-dev-ops](https://github.com/ROARforGood/purple-dev-ops/issues) repo, tagging `nbarkovsky`.

If you need it done quicker, file the issue, but also contact a member of the dev team to have temporary access granted.

## Programming a Gateway

### Required Equipment

- Zebra Thermal Print GK420d, GX420d, GK420t or GX420t
  - with 1.25" x 0.25" labels
- Fanstel DK-BWG840F serial adapter
  - w/ micro usb cable
- Nordic nRF52-DK dev board
  - with 10 pin serial cable
- 2D barcode scanner

### Connecting to a board

- Disassemble the gateway with a small phillips screwdriver, remove the JS5 header in the JS4 connector.
- connect the board as seen in the photo below.
  - Serial adapter `To Wifi(ESP) connected to the Gateway JS4 header
  - 10 pin serial cable from the nRF52-DK Debug Out to the Gateway JS3 connector.
![Gateway hook up](https://user-images.githubusercontent.com/33539057/133156010-f3c2bf7d-da0f-416e-a5e5-6cb0af55f5ac.jpg)


### Programming the gateway

- For Gateways going to customer sites launch the `FlashProductionGateway_0.901.bat`.
- Follow the promts entering:
    - the client ID
    - site ID
    - confirm if correct
    - then enter the gateway ID when prompted

The gateways should then be programmed, firts the sinknode, then the wifi chip in a seprate window.
_Note: do not use the mouse or keyboard when the Wifi chip is being programmed, and after it is successfully programmed, you will have to manually exit that window._
