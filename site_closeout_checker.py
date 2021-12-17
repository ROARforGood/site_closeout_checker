from time import sleep
import sys
import os
from datetime import datetime
import logging
import csv
from tkinter import filedialog
from tkinter import *
from modules.purple_postgres_db import PurplePostgres


class SiteCheck:
    def __init__(self):
        self.PurpleDb = PurplePostgres(server = 'tfprod')

        
        self.beacons_with_geofeature_error = self.PurpleDb.beacons_with_mismatched_networks_and_geofetures()
        print('\nBeacons that need to be reinstalled due to install geo_feature assignment issue:')
        print('---------------------------------------------------------------------------------')
        if self.beacons_with_geofeature_error:
            for beacon in self.beacons_with_geofeature_error:
                print(f"Building: {beacon['building_id']} Level: {beacon['level_id']} Location: {beacon['location_type']} {beacon['location_id']} {beacon['description']} Public ID: {beacon['node_public_id']} Serial Number Index: {beacon['serial_number_index']}")
        else:
            print("No beacons to reinstall due to this issue!")

        self.beacons_to_decommission = self.PurpleDb.beacons_to_decommision_no_geofeature()
        print('\nBeacons to decommission (not assigned to a geofeature):')
        print('---------------------------------------------------------------------------------')
        if self.beacons_to_decommission:
            for beacon in self.beacons_to_decommission:
                beacon['dashboard_url'] = f"https://prod.roaralwayson.net/clients/{self.PurpleDb.client_id}/sites/{self.PurpleDb.site_id}/networks/{beacon['network_id']}/nodes/{beacon['id']}"
                print(f"Public ID: {beacon['node_public_id']} Serial Number Index: {beacon['serial_number_index']}")
            
            decommission_promt = input(f"\nWould you like to decommission some or all of these beacons? (Y/N) ")
            if decommission_promt in [ 'Y', 'y']:
                for beacon in self.beacons_to_decommission:
                    decommission_promt = input(f"Would you like to decommission  Node Public ID: {beacon['node_public_id']} node.id: {beacon['id']}? (Y/N) ")
                    if decommission_promt in [ 'Y', 'y']:
                        self.PurpleDb.decommision_by_node_id(beacon['id'])
                        logger.debug(f"Decommissioned beacon Public Id: {beacon['node_public_id']} Serial Number Index: {beacon['serial_number_index']} node.id: {beacon['id']}, from Site: {self.PurpleDb.site_name}")
        else:
            print("No beacons to decommission!")

        site_networks = self.PurpleDb.site_networks()
        print('\nNetwork Master Sizes and # Uninstalled Bays per Network:')
        print('(note: master size only counts installed locations)')
        print('----------------------------------------------------------')
        self.networks = []
        for network in site_networks:
            network_master_size = self.PurpleDb.network_master_count(network_id=network['id'])
            uninstalled_bays = self.PurpleDb.uninstalled_bay_count(network_id=network['id'])
            self.networks.append({ 'network_id' : network['id'], 'master_size' : network_master_size, 'uninstalled_bays' : uninstalled_bays})
            print(f'Network: {network["id"]} Master Size: {network_master_size} Uninstalled Bays: {uninstalled_bays}')

        
        generate_csvs = input("\nWould you like to generate CSVs to save the above info? (Y/N): ")
        if generate_csvs in [ 'Y', 'y']:
            self.generate_csvs()

        input("\nSite Closeout Check complete, press Enter to close the window...")
    def generate_csvs(self):
        """Generate and save CSVs
        """    
        base_output_directory = filedialog.askdirectory(title = "Select Save Location")
        
        
        #Key: csv filename Value: dict of data for that sheet
        output_directory = os.path.join(base_output_directory, f'Site-Check-{self.PurpleDb.client_mqtt_id}_{self.PurpleDb.site_mqtt_id}-{self.PurpleDb.site_name}-({datetime.now().strftime("%y-%m-%d_%H%M%S")})')
        os.mkdir(output_directory)

        
        csv_dict = {
        "BeaconsWithGeofeatureError.csv" : self.beacons_with_geofeature_error,
        "BeaconsToDecommission.csv" : self.beacons_to_decommission,
        "NetworkMasterSize.csv" : self.networks
        }
        
        for csv_file in csv_dict:
            if csv_dict[csv_file]:
                csv_path = os.path.join(output_directory, csv_file)
                with open(csv_path, 'w', newline='') as file:
                    writer = csv.writer(file)            
                    
                    csv_headers = list(csv_dict[csv_file][0].keys())
                    writer.writerow(csv_headers)
                    
                    for index, item in enumerate(csv_dict[csv_file]):
                        row_list = list(item[key] for key in csv_headers)
                        writer.writerow(row_list)
        
    
def main():
    site_check = SiteCheck()
    
    
    

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    input(f"Critical Error, see info above. Press Enter to close the window...")

if __name__ == '__main__':
    #Initiate logging settings
    from logging.config import fileConfig
    logging.config.fileConfig('logs/logging.conf' , disable_existing_loggers=False, defaults={ 'logfilename' : 'site_closeout_checker.log' } )
    logger = logging.getLogger('site_closeout_checker')
    
    #Keep window open during error so the user can see the error.
    sys.excepthook = handle_exception

    main()




