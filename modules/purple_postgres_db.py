import psycopg2
import psycopg2.extras
import logging
from sshtunnel import SSHTunnelForwarder
from configparser import ConfigParser
logger = logging.getLogger('purple_postgres_db')

CONFIG_DB = ConfigParser()
CONFIG_DB.read('config_db.ini')
CONFIG = ConfigParser()
CONFIG.read('config.ini')
class PurplePostgres:
    def __init__(self, server = False, site_id = False):
        if server == False:
            server = CONFIG['connection']['server']
        db_credentials = CONFIG_DB[server]
        logger.debug(f'DB Host: {db_credentials["host"]}')
        self.server = server
        self.db_connection(db_credentials)
        if site_id:
            self.site_id = site_id
        else:
            site = self.get_site_id()
            self.site_name = site['name']
            self.site_id =  site['id']

        self.site_mqtt_id = self.get_site_mqtt_id(self.site_id)
        self.client_mqtt_id = self.get_client_mqtt_id(self.site_id)
    
    def db_connection(self, db_credentials):
        tunnel = self.launch_sshtunnel(db_credentials)
        try:
            self.conn = psycopg2.connect(host = tunnel.local_bind_host,
                                        port = tunnel.local_bind_port,
                                        database = db_credentials['database'],
                                        user = db_credentials['user'],
                                        password = db_credentials['password'])
            
            if self.conn.status:
                logger.info(f"Successful connection to server: {self.server}")

            # create a cursor
            cur = self.conn.cursor()
            
            # # execute a statement
            # cur.execute("SELECT site.name FROM public.site \
            #             WHERE site.id = '%s' \
            #             LIMIT 1"%(self.site_id))
    
            # # display the PostgreSQL database server version
            # self.site_name = cur.fetchone()[0]
            # print('Working with site:', self.site_name, '\n')
        
            # close the communication with the PostgreSQL
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            print("Database Connection Failed :(")
            print("- Make sue there is not another SSH tunnel already open, SSH tunnel is now integrated ino the program!")
            print("- Make sure your're IP address is white listed (contacts the dev team for more info)")
            print("- Confirm that the database credentials in config.ini are correct")
            input("Press Enter to Exit the Program...")
            raise ValueError("Database Connection Failed")
    
    
    def launch_sshtunnel(self, db_credentials):  
        sshtunnel_logger = logging.getLogger("paramiko.transport")
        sshtunnel_logger.setLevel(logging.WARNING)
            
        try:
            # SSH Tunnel Configuration
            tunnel =  SSHTunnelForwarder(
                ssh_host = 'bastion.roaralwayson.com',
                ssh_port = 22,
                ssh_username = 'ec2-user',
                ssh_pkey= '.\keys\kp-tf-deployer.pem',
                remote_bind_address=(f'{db_credentials["ssh_tunnel"]}.cbxvcrk7rtag.us-east-1.rds.amazonaws.com', 5432),
                local_bind_address=('localhost', int(db_credentials['port']))
            )
            tunnel.start()
        except (Exception) as error:
            print(error)
            print("Launching SSH Tunnel failed :(")
            print("- Confirm that the database credentials in config.ini are correct")
            print("- Ensure you have a live internet connection")
            input("Press Enter to Exit the Program...")
            raise ValueError("Launching SSH Tunnel Failed")
        return tunnel
    
    
    def cursor_fetchall_to_dict(self, cursor):
        columns = [desc[0] for desc in cursor.description]
        real_dict = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return real_dict
    
    def get_records_dict(self, query: str) -> dict:
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        logger.debug(f"Executing query: {query}")
        cur.execute(query)
        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()

        return records_dict
    
    def get_client_id(self, site_id):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        
        cur.execute("""select client_id from site
                where site.id = '%s'
                """
            %(site_id,)
            )

        client_dict = self.cursor_fetchall_to_dict(cur)
        if len(client_dict) < 1:
            logger.error("No matching client for this site")
            input("Press Enter to Exit...")
            raise ValueError("No matching client on this server")
        client_id = client_dict[0]["client_id"]
        # print(f'client id:{client_id}\n')
    


        cur.close()
        
        return client_id 

    def get_site_id(self):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        
        # cur.execute("""SELECT id FROM public.network
        #                WHERE id = %s AND network.site_id = '%s'
        #                """
        #             %(network_id, self.site_id)
        #             )
        
        self.client_mqtt_id = input('Enter customer Client ID: ')
        cur.execute("""SELECT name, id FROM client
                WHERE \"mqttTopic\" = '%s'
                """
            %(self.client_mqtt_id,)
            )
        client_dict = self.cursor_fetchall_to_dict(cur)
        if len(client_dict) < 1:
            logger.error("No matching client on this server")
            input("Press Enter to Exit...")
            raise ValueError("No matching client on this server")
        client = client_dict[0]
        self.client_id = client["id"]
        logger.info(f'Client found: {client["name"]} \n')
        
        self.site_mqtt_id = input('Enter Site ID: ')
        cur.execute("""SELECT name, id FROM site
                WHERE \"mqttTopic\" = '%s' AND client_id = '%s'
                """
            %(self.site_mqtt_id,client['id'])
            )
        site_dict = self.cursor_fetchall_to_dict(cur)
        if len(site_dict) < 1:
            logger.error("No matching site for this client")
            input("Press Enter to Exit...")
            raise ValueError("No matching client on this server")
        site = site_dict[0]
        logger.info(f'Site found: {site["name"]}\n')



        cur.close()
        
        return site     

    def get_site_mqtt_id(self, site_id):
        site = self.get_records_dict(f"""SELECT \"mqttTopic\" from site 
                    WHERE site.id = '{self.site_id}'""")
        
        return site[0]['mqttTopic']   
     
    def get_client_mqtt_id(self, site_id):
        site = self.get_records_dict(f"""SELECT client.\"mqttTopic\" from site 
                    JOIN client on site.client_id = client.id
                    WHERE site.id = '{self.site_id}'""")
        
        return site[0]['mqttTopic']
 

    def node_params(self, node_id):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT  node_public_id, board_type, device_type, network_id, network_key
                    FROM node
                    INNER JOIN network ON network.id = node.network_id
                    WHERE node.node_public_id = %s AND network.site_id = '%s'
                    LIMIT 2"""
                    %(node_id, self.site_id)
                    )
        # print(cur.query)
        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()
        if len(records_dict) == 1:
            logger.debug("Found device info by ID")
            node_params = records_dict[0]
            return node_params
        elif len(records_dict) == 0:
            logger.error("Device info not found {}".format(node_id))
            return None
        elif len(records_dict) > 1:
            logger.error("Duplicate device IDs")
            return None

    def get_gateway_by_id(self, gateway_id):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        if gateway_id[0:2] == 'rg':
            node_public_id = gateway_id[2:8]
        else:
            node_public_id = gateway_id.split('_')[2]
        cur.execute("""SELECT  node.node_public_id, node.board_type, node.device_type, network.id, network.network_key, gateway.thing_arn, access_point.wifi
                    FROM node
                    INNER JOIN network ON network.id = node.network_id
                    INNER JOIN gateway ON gateway.id = '%s'
                    INNER JOIN access_point on gateway.access_point_id = access_point.id
                    WHERE node.node_public_id = %s AND network.site_id = '%s'
                    LIMIT 2"""
                    %(gateway_id, node_public_id, self.site_id)
                    )
        logger.debug(cur.query)
        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()
        if len(records_dict) == 1:
            logger.debug("Found device info by ID")
            gateway_params = records_dict[0]
            return gateway_params
        elif len(records_dict) == 0:
            logger.error("Device info not found {}".format(gateway_id))
            return None
        elif len(records_dict) > 1:
            logger.error("Duplicate device IDs")
            return None
    
    def site_networks(self):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT network.id, network.network_key, network.master_size, network.size FROM public.network
                    WHERE network.site_id = '%s'
                    GROUP BY network.id
                    ORDER BY id asc
                    """
                    %(self.site_id)
                    )
        # print(cur.query)
        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()
        
        return records_dict

    def site_nodes(self):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT node.id, node.node_public_id, node.serial_number, node.serial_number_index, node.network_id, network.online, node.free_out, geo_feature.location_id, geo_feature.building_id  FROM public.node
                       JOIN geo_feature ON node.id = geo_feature.node_id
                       INNER JOIN network ON network.id = node.network_id
                       WHERE network.site_id = '%s'"""
                    %(self.site_id)
                    )

        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()
        
        return records_dict
    
    def network_exists(self, network_id):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT id FROM public.network
                       WHERE id = %s AND network.site_id = '%s'
                       """
                    %(network_id, self.site_id)
                    )

        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()
        
        return records_dict

    def get_list_of_gateway2s(self):
        gateway2s = self.get_records_dict(f"""SELECT * from gateway 
                            INNER JOIN network on gateway.network_id = network.id
                            WHERE site_id = '{self.site_id}'
                            AND SUBSTRING(SPLIT_PART(gateway.id, '_', -1) FROM 2 FOR 1) = '2'
                            ORDER BY (gateway.id) ASC""")
        return gateway2s
    
    def current_network_size(self, network_id):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT size FROM public.network
                       WHERE id = %s AND network.site_id = '%s'
                       """
                    %(network_id, self.site_id)
                    )

        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()
    
        return records_dict[0]['size']

    def confirmed_nodes_list(self, site_id, node_list):
        cur= self.conn.cursor() #cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT node_public_id FROM node
                       JOIN network ON network.id = node.network_id
                       WHERE network.site_id = '%s' AND device_type = 1 AND node.last_report IS NOT NULL AND node_public_id in %s
                       """
                    %(self.site_id, tuple(node_list)))
        # print(cur.query)
        # confirmed_nodes_list = self.cursor_fetchall_to_dict(cur)
        results = cur.fetchall()
        confirmed_nodes_list = [node[0] for node in results]
        cur.close()
        
        return confirmed_nodes_list

    def network_master_count(self, network_id):
        cur= self.conn.cursor() #cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT DISTINCT geo_feature.building_id, geo_feature.level_id, geo_feature.location_id, geo_feature.description
                        FROM geo_feature
                        INNER JOIN geo_space ON (geo_space.site_id = geo_feature.site_id)
                        AND (geo_space.building_id = geo_feature.building_id) 
                        AND (geo_space.level_id = geo_feature.level_id) 
                        WHERE geo_feature.node_id IS NOT NULL AND geo_space.location_id = '%s'
                       """
                    %(network_id))
        # print(cur.query)
        # confirmed_nodes_list = self.cursor_fetchall_to_dict(cur)
        results = cur.fetchall()
        geofeature_list = [geofeature[0] for geofeature in results]
        cur.close()
        
        return len(geofeature_list)

    def uninstalled_bay_count(self, network_id):
        cur= self.conn.cursor() #cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT DISTINCT geo_feature.building_id, geo_feature.level_id, geo_feature.location_id, geo_feature.description
                        FROM geo_feature
                        INNER JOIN geo_space ON (geo_space.site_id = geo_feature.site_id)
                        AND (geo_space.building_id = geo_feature.building_id) 
                        AND (geo_space.level_id = geo_feature.level_id) 
                        WHERE node_id is NULL AND asset_id is NULL  AND geo_space.location_id = '%s'
                       """
                    %(network_id))
        # print(cur.query)
        # confirmed_nodes_list = self.cursor_fetchall_to_dict(cur)
        results = cur.fetchall()
        geofeature_list = [geofeature[0] for geofeature in results]
        cur.close()
        
        return len(geofeature_list)
    
    def list_uninstalled_rooms(self, network_id):
        cur= self.conn.cursor() #cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT DISTINCT geo_feature.building_id, geo_feature.level_id, geo_feature.location_id
                        FROM geo_feature
                        INNER JOIN geo_space ON (geo_space.site_id = geo_feature.site_id)
                        AND (geo_space.building_id = geo_feature.building_id) 
                        AND (geo_space.level_id = geo_feature.level_id) 
                        WHERE node_id is NULL AND asset_id is NULL AND geo_space.location_id = '%s'
                       """
                    %(network_id))
        # print(cur.query)
        # confirmed_nodes_list = self.cursor_fetchall_to_dict(cur)
        results = cur.fetchall()
        cur.close()
        
        return results

    def beacons_with_mismatched_networks_and_geofetures(self):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT client.id, site.id, site.name, geo_feature.building_id, geo_feature.level_id, geo_feature.location_type, geo_feature.location_id, geo_feature.description,  node.id, node.node_public_id, node.serial_number_index, network.id FROM public.geo_feature
                        inner join node on geo_feature.node_id = node.id
                        inner join network on node.network_id = network.id
                        inner join site on site.id = geo_feature.site_id
                        inner join client on client.id = site.client_id
                        where network.site_id <> geo_feature.site_id
                        and geo_feature.site_id = '%s'
                        ORDER BY geo_feature.site_id
                       """
                    %(self.site_id)
                    )

        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()

        return records_dict
    def beacons_to_decommision_no_geofeature(self):
        cur= self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("""SELECT geo_feature.id, node.id, node.node_public_id, node.serial_number_index, node.network_id, node.decommissioned FROM public.node
                        INNER JOIN network ON node.network_id = network.id
                        LEFT JOIN geo_feature ON geo_feature.node_id = node.id
                        WHERE network.site_id = '%s'
			            AND device_type = 1
                        AND geo_feature.id IS NULL
                        AND node.decommissioned = false
                        ORDER BY node_public_id
                       """
                    %(self.site_id)
                    )

        records_dict = self.cursor_fetchall_to_dict(cur)
        cur.close()
    
        return records_dict

    def decommision_by_node_id(self, node_id):
        cur= self.conn.cursor()
        cur.execute("""UPDATE node SET decommissioned = 'true' 
                        WHERE node.id = '%s';
                       """
                    %(node_id)
                    )
        
        rowcount = cur.rowcount
        if rowcount == 1:
            self.conn.commit()
            logger.info(f"decommisioned node.id: {node_id}")
        else:
            logger.error(f"Error row count: {rowcount}, for decommissioning, it should only be 1.")
        cur.close()
        
        return #results
    
    def update_node_public_id(self, node_id, serial_number_index, db_node_public_id, hw_node_public_id):
        cur= self.conn.cursor()
        query = f"""UPDATE node SET node_public_id = {hw_node_public_id}
                    WHERE node.id = '{node_id}'
                    AND node.serial_number_index = {serial_number_index}
                    AND node.node_public_id = {db_node_public_id};
                    """
        logger.debug(query)
        cur.execute(query)
        
        rowcount = cur.rowcount
        if rowcount == 1:
            self.conn.commit()
            logger.info(f"Successfully updated node with serial number index:{serial_number_index} & db public id:{db_node_public_id} "
                f"to match hw public id:{hw_node_public_id}")
        else:
            logger.error(f"Error updating node with serial number index:{serial_number_index} - row count: {rowcount}, when updating, it should only be 1.")
        cur.close()
        
        return #results





if __name__ == '__main__':
    TestDb = PurplePostgres(server = 'tfprod',
                            site_id = '1y8rAybumasW7OJL3t3JRPJOkUY')

    site_networks = TestDb.site_networks()
    print(site_networks)
    site_nodes = TestDb.site_nodes()
    print(site_nodes)
    # for network in site_networks:
    #     network_master_size = TestDb.network_master_count(network_id=network['id'])
    #     uninstalled_bays = TestDb.uninstalled_bay_count(network_id=network['id'])
    #     print(f'Network: {network["id"]} Size: {network_master_size} Uninstalled Bays: {uninstalled_bays}')

    # beacons_with_geofeature_error = TestDb.beacons_with_mismatched_networks_and_geofetures()
    # print(beacons_with_geofeature_error)