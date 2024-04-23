from time import sleep
import sys
import os
from datetime import datetime
import logging
import csv
from tkinter import filedialog
from tkinter import *
from modules.purple_postgres_db import PurplePostgres
from modules.mqtt_client import MqttClient

# class MQTTAlertCount:
#     def __init__(self):
#         self.mqtt_client = MqttClient()
#         self.mqtt_client.client.on_message = self.on_message
#         while not self.mqtt_client.is_connected:
#             pass
#         self.mqtt_client.client.subscribe('uart/53/1/53_1_22003', 1)
#         self.alert_msgs = {}

#     def on_message(self, client, userdata, msg):
        
#         # logger.info(f"Message Received, Topic: {msg.topic} Paylod: {msg.payload}")

#         json_msg = self.mqtt_client.json_parse_line(msg.payload)
#         print(f"{json_msg['nodeId']}\t{json_msg['serialNumberIndex']}")
class SiteCheck:
    def __init__(self):
        self.PurpleDb = PurplePostgres()

        self.beacons_with_geofeature_error = self.beacons_with_geofeature_error()

        self.beacons_to_decommission = self.beacons_to_decommission()

        self.networks = self.networks()
        print('\nCheck for beacons where hardware and databse public IDs don\'t match:')
        print('---------------------------------------------------------------------------------')
        
        self.nodes_dict = self.nodes_by_serial_index()

        self.site_gateway2s = self.PurpleDb.get_list_of_gateway2s()
        
        # print('gateways',self.site_gateway2s)

        self.mqtt_client = MqttClient()
        self.mqtt_client.client.on_message = self.on_message
        while not self.mqtt_client.is_connected:
            pass
        subscribe_topic = f'uart/{self.PurpleDb.client_mqtt_id}/{self.PurpleDb.site_mqtt_id}/#'
        logger.debug(f'subscribing to {subscribe_topic}')
        self.mqtt_client.client.subscribe(subscribe_topic, 1)


        self.mismatched_node_ids = []

        print("Wait 30 seconds while we ping all beacons on the site networks and wait for their response")
        self.ping_all_beacons()
        sleep(15)
        self.ping_all_beacons()
        sleep(15)
        
        
        self.mark_mismatched_public_ids()
        self.correct_mismatched_public_ids()
        
        generate_csvs = input("\nWould you like to generate CSVs to save the above info? (Y/N): ")
        if generate_csvs in [ 'Y', 'y']:
            self.generate_csvs()

        input("\nSite Closeout Check complete, press Enter to close the window...")
    
    
    def beacons_with_geofeature_error(self):
        beacons_with_geofeature_error = self.PurpleDb.beacons_with_mismatched_networks_and_geofetures()
        print('\nBeacons that need to be reinstalled due to install geo_feature assignment issue:')
        print('---------------------------------------------------------------------------------')
        if beacons_with_geofeature_error:
            for beacon in beacons_with_geofeature_error:
                print(f"Building: {beacon['building_id']} Level: {beacon['level_id']} Location: {beacon['location_type']} {beacon['location_id']} {beacon['description']} Public ID: {beacon['node_public_id']} Serial Number Index: {beacon['serial_number_index']}")
        else:
            print("No beacons to reinstall due to this issue!")

        return beacons_with_geofeature_error

    def beacons_to_decommission(self):
        beacons_to_decommission = self.PurpleDb.beacons_to_decommision_no_geofeature()
        print('\nBeacons to decommission (not assigned to a geofeature):')
        print('---------------------------------------------------------------------------------')
        if beacons_to_decommission:
            for beacon in beacons_to_decommission:
                beacon['dashboard_url'] = f"https://prod.roaralwayson.net/clients/{self.PurpleDb.client_id}/sites/{self.PurpleDb.site_id}/networks/{beacon['network_id']}/nodes/{beacon['id']}"
                print(f"Public ID: {beacon['node_public_id']} Serial Number Index: {beacon['serial_number_index']}")
            
            decommission_promt = input(f"\nWould you like to decommission some or all of these beacons? (Y/N) ")
            if decommission_promt in [ 'Y', 'y']:
                for beacon in beacons_to_decommission:
                    decommission_promt = input(f"Would you like to decommission  Node Public ID: {beacon['node_public_id']} node.id: {beacon['id']}? (Y/N) ")
                    if decommission_promt in [ 'Y', 'y']:
                        self.PurpleDb.decommision_by_node_id(beacon['id'])
                        logger.debug(f"Decommissioned beacon Public Id: {beacon['node_public_id']} Serial Number Index: {beacon['serial_number_index']} node.id: {beacon['id']}, from Site: {self.PurpleDb.site_name}")
        else:
            print("No beacons to decommission!")

        return beacons_to_decommission
    
    def networks(self):
        site_networks = self.PurpleDb.site_networks()
        print('\nNetwork Master Sizes and # Uninstalled Bays per Network:')
        print('(note: master size only counts installed locations)')
        print('----------------------------------------------------------')
        networks = []
        for network in site_networks:
            network_master_size = self.PurpleDb.network_master_count(network_id=network['id'])
            uninstalled_bays = self.PurpleDb.uninstalled_bay_count(network_id=network['id'])
            networks.append({ 'network_id' : network['id'], 'master_size' : network_master_size, 'uninstalled_bays' : uninstalled_bays})
            print(f'Network: {network["id"]} Master Size: {network_master_size} Uninstalled Bays: {uninstalled_bays}')

        return networks

    def nodes_by_serial_index(self):
        site_nodes = self.PurpleDb.site_nodes()
        nodes_by_serial_index = {}
        for node in site_nodes:
            nodes_by_serial_index[node['serial_number_index']] = { 'db' : node }
        return nodes_by_serial_index

    def ping_all_beacons(self):
        base_topic = f'bcmd/{self.PurpleDb.client_mqtt_id}/{self.PurpleDb.site_mqtt_id}'
        for gateway in self.site_gateway2s:
            topic = f"{base_topic}/{gateway['thing_arn']}"
            logger.debug(f'ping beacons on topic: {topic}')
            self.mqtt_client.client.publish(topic,'action 0 status get_device_info2')

    def mark_mismatched_public_ids(self):
        mismatched_count = 0
        for serial_number_index in self.nodes_dict:
            node = self.nodes_dict[serial_number_index]
            if 'db' in node and 'hw' in node:
                if node['db']['node_public_id'] != node['hw']['node_public_id']:
                    self.nodes_dict[serial_number_index]['mismatched'] = True
                    if mismatched_count == 0:
                        logger.info('Beacons with mismatched public IDs:')
                    mismatched_count += 1
                    self.mismatched_node_ids.append({'serial_number_index' : serial_number_index,
                                 'db_public_id' : node['db']['node_public_id'],
                                 'hw_public_id' : node['hw']['node_public_id']})
        if len(self.mismatched_node_ids) > 0:
            logger.info(self.mismatched_node_ids)
        logger.info(f'{mismatched_count} mismatched public IDs found')
        return mismatched_count

    def correct_mismatched_public_ids(self):
        for serial_number_index in self.nodes_dict:
            node = self.nodes_dict[serial_number_index]
            if 'mismatched' in node:
                if node['mismatched'] == True:
                    self.PurpleDb.update_node_public_id(node_id = node['db']['id'],
                        serial_number_index = serial_number_index,
                        db_node_public_id = node['db']['node_public_id'],
                        hw_node_public_id = node['hw']['node_public_id'])


    def on_message(self, client, userdata, msg):
        
        # logger.info(f"Message Received, Topic: {msg.topic} Paylod: {msg.payload}")

        json_msg = self.mqtt_client.json_parse_line(msg.payload)
        if 'type' in json_msg:
            if json_msg['type'] == 'device_info':
                if json_msg['serialNumberIndex'] in self.nodes_dict:
                    self.nodes_dict[json_msg['serialNumberIndex']]['hw'] = {'node_public_id' : json_msg['nodeId']}
                    # logger.debug(self.nodes_dict[json_msg['serialNumberIndex']])

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
        "NetworkMasterSize.csv" : self.networks,
        "MismatchedNodeIds.csv" : self.mismatched_node_ids
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




