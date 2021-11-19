import subprocess
from time import sleep
import sys
import os
from pathlib import Path
import fileinput
import logging
from configparser import ConfigParser
from modules.purple_postgres_db import PurplePostgres

def target_params_from_db(conn, target_id, site_id, gateway_parameters):
    cur= conn.cursor()
    node_public_id = target_id.split('_')[2]
    logger.debug(f'node_public_id: {node_public_id}')
    cur.execute("SELECT 'node.node_public_id','node.board_type','node.device_type','network.id','network.network_key','gateway.thing_arn', 'access_point.wifi' \
                FROM node   \
                INNER JOIN network ON network.id = node.network_id \
                INNER JOIN gateway ON gateway.id = %s \
                INNER JOIN access_point on gateway.access_point_id = access_point.id \
                WHERE node.node_public_id = %s AND network.site_id = %s \
                LIMIT 2"
                ,(target_id, node_public_id, config['site']['id'])
                )
    logger.debug(f'Query: {cur.query}')
    rows = cur.fetchall()
    cur.close()
    if len(rows) == 1:
        logger.debug("Found device info by ID")
        target_gateway_params = rows[0]
        logger.debug(target_gateway_params)
        return target_gateway_params  
    elif len(rows) == 0:
        logger.error("Device info not found")
        return None
    elif len(rows) > 1:
        logger.error("Duplicate device IDs")
        return None



def main():
    PurpleDb = PurplePostgres(server = config['connection']['server'])
    
    input(f'If {PurpleDb.site_name} is the correct site hit [Enter] to contine, otherwise close the program and re-enter the site info.')

def test_main():    
    PurpleDb = PurplePostgres(server = config['connection']['server'],
                              site_id = '1y8rAybumasW7OJL3t3JRPJOkUY')

    beacons_with_geofeature_error = PurpleDb.beacons_with_mismatched_networks_and_geofetures()
    print('\nBeacons that need to be reinstalled due to install geo_feature assignment issue:')
    print('---------------------------------------------------------------------------------')
    for beacon in beacons_with_geofeature_error:
        print(f"Building: {beacon['building_id']} Level: {beacon['level_id']} Location: {beacon['location_type']} {beacon['location_id']} {beacon['description']} Public ID: {beacon['node_public_id']} Serial Number Index: {beacon['serial_number_index']}")
    
    beacons_to_decommission = PurpleDb.beacons_to_decommision_no_geofeature()
    print('\nBeacons to decommission (not assigned to a geofeature):')
    print('---------------------------------------------------------------------------------')
    for beacon in beacons_to_decommission:
        print(f"Public ID: {beacon['node_public_id']} Serial Number Index: {beacon['serial_number_index']} URL: https://prod.roaralwayson.net/clients/{PurpleDb.client_id}/sites/{PurpleDb.site_id}/networks/{beacon['network_id']}/nodes/{beacon['id']}")
    

    site_networks = PurpleDb.site_networks()
    print('\nNetwork Master Sizes and # Uninstalled Bays per Network:')
    print('----------------------------------------------------------')
    for network in site_networks:
        network_master_size = PurpleDb.network_master_count(network_id=network['id'])
        uninstalled_bays = PurpleDb.uninstalled_bay_count(network_id=network['id'])
        print(f'Network: {network["id"]} Master Size: {network_master_size} Uninstalled Bays: {uninstalled_bays}')

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    input(f"Critical Error, see info above. Press Enter to close the window...")

if __name__ == '__main__':
    #Initiate logging settings
    from logging.config import fileConfig
    logging.config.fileConfig('logs/logging.conf' , disable_existing_loggers=False, defaults={ 'logfilename' : 'gateway-programmer.log' } )
    logger = logging.getLogger('gateway-programmer')
    
    #Keep window open during error so the user can see the error.
    sys.excepthook = handle_exception

    config = ConfigParser()
    config.read('config.ini')

    test_main()




