'''
    File name: mqtt_client.py
    Author: Rich Nelson
    Date created: 7.60/2023
    Python Version: 3.8.3

    Summary:
    Subcribe to test MQTT topic and log messages
    that come through from the gateway.
'''
import paho.mqtt.client as paho
import ssl
import logging
import time
import json
import sys
from configparser import ConfigParser
logger = logging.getLogger('mqtt_client')

config_file = 'config.ini'
CONFIG = ConfigParser()
CONFIG.read(config_file)

class MqttClient():
    def __init__(self):
        self.client = paho.Client()
        self.client.on_connect = self.on_connect
        # self.client.on_message = self.on_message
        
        self.is_connected = False
        # self.received_order = 1
        # self.mqtt_messages_received = []

        # self.pub_base_topic = f"cmd/version/2/gateway/{nerves_gateway_id}"
        # self.gw_sub_topic = f"+/+/+/{nerves_gateway_id}"

        awshost = CONFIG['MQTT']['HOST']
        awsport = 8883
        caPath = CONFIG['MQTT']['ROOT_CA_PATH']
        certPath = CONFIG['MQTT']['CERTIFICATE_PATH']
        keyPath = CONFIG['MQTT']['PRIVATE_KEY_PATH']

        self.client.tls_set(caPath,
                    certfile=certPath,
                    keyfile=keyPath,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1_2,
                    ciphers=None)

        self.client.connect(awshost,
                    awsport,
                    keepalive=60)
        
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        if rc == 0:
            logger.debug("MQTT Connection established")
            self.is_connected = True

    def on_message(self, client, userdata, msg):
        logger.debug(msg.payload)
        msg_decoded = self.json_parse_line(msg.payload)
        logger.debug(msg_decoded)
        # self.mqtt_messages_received.append({'timestamp_received_ms' : round(time.time()*1000),
        #                             'received_order' : self.received_order,
        #                             'message_number' : msg_decoded['msg_number']
        #                             })
        # self.received_order += 1

    def get_status(self):
        topic = f"{self.pub_base_topic}/status"
        self.client.publish(topic, "")
        logger.debug(f"Request Gateway Status from topic: {topic}")
    
    def disconnect(self):
        self.client.disconnect()
    
    def json_parse_line(self, line):
        utf_line = line.decode('utf-8')
        # print(utf_line)
        try:
            json_line = json.loads(utf_line)
            return json_line
        except:
            print("Json decode error);")
            sys.stdout.flush()
            return False

if __name__ == '__main__':
    from logging.config import fileConfig
    logging.config.fileConfig('logs/logging.conf' , disable_existing_loggers=False, defaults={ 'logfilename' : 'mqtt_gateway.log' } )
    logger = logging.getLogger('mqtt_subscriber')

    mqtt_client = MqttClient(nerves_gateway_id = 'gw2-dvt1-00004')
    while True:
        mqtt_client.get_status()
        time.sleep(10)
