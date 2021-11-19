import subprocess
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

config_db = ConfigParser()
config_db.read('config_db.ini')

def powershell_command(command, terminal_output = 1):
    error = False
    output = [subprocess.PIPE, None]
    
    if terminal_output:
        print(command)
    
    p = subprocess.call(["powershell.exe", command],
                         stdout=output[terminal_output],
                         stderr=output[terminal_output], shell=True)
    p.communicate()
    error = p.returncode
    if error:
        print("Error executing command:", command)

    return error
    
def main():
    server = config['connection']['server']
    ssh_address = config_db[server]['ssh_tunnel']
    powershell_command(f'ssh -L 5555:{ssh_address}.cbxvcrk7rtag.us-east-1.rds.amazonaws.com:5432 ec2-user@bastion.roaralwayson.com -i .\keys\kp-tf-deployer.pem')

if __name__ == "__main__":
    main()
