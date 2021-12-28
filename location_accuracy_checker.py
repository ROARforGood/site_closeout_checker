from time import sleep
import sys
import os
from datetime import datetime
import logging
import csv
import datetime, time
from tkinter import filedialog
from tkinter import *
from modules.purple_postgres_db import PurplePostgres


class LocationAccuracyTest:
    def __init__(self, alert_id = None):
        self.PurpleDb = PurplePostgres(server = 'tfdevelop', analytics_db = True)

        if alert_id:
            self.alert_id = alert_id
        else:
            self.alert_id = input("Enter alert id: ")

        self.alert_location_history = self.alert_location_history()
        self.alert_length_s = self.alert_length_s()
        self.alert_locations = self.alert_locations()
        self.alert_percentages()
        pass

    def alert_location_history(self):
        
        alert_locations = self.PurpleDb.get_locations_by_alert_id(self.alert_id)

        return alert_locations   
    
    def alert_length_s(self):
        alert_start = self.alert_location_history[0]['inserted_at']
        alert_end = self.alert_location_history[-1]['inserted_at']
        alert_length = alert_end - alert_start
        alert_length_s = alert_length.total_seconds()
        return alert_length_s

    def alert_locations(self):
        locations = {}
        for i, location in enumerate(self.alert_location_history):
            if i != len(self.alert_location_history)-1:
                location_name = f"{location['building_id']} {location['level_id']} {location['location_type']} {location['location_id']}"
                location_start_time = location['inserted_at']
                location_end_time = self.alert_location_history[i+1]['inserted_at']
                time_s = (location_end_time - location_start_time).total_seconds()
                self.alert_location_history[i]['location_name'] = location_name
                self.alert_location_history[i]['time_at_location_s'] = time_s
                if location_name not in locations:
                    locations[location_name] = {}
                if 'time' in locations[location_name]:
                    locations[location_name]['time'] += time_s
                else:
                    locations[location_name]['time'] = time_s
        
        return locations

    def alert_percentages(self):
        added_time = 0.0
        for location in self.alert_locations:
            self.alert_locations[location]['percentage'] = self.alert_locations[location]['time']/self.alert_length_s
            added_time += self.alert_locations[location]['time']

        print(added_time, self.alert_length_s)
        
    
def main():
    accuracy_test = LocationAccuracyTest(alert_id = '22HuH6GBYfadp7ClImPimYhCKWO')

    

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    input(f"Critical Error, see info above. Press Enter to close the window...")

if __name__ == '__main__':
    #Initiate logging settings
    from logging.config import fileConfig
    logging.config.fileConfig('logs/logging.conf' , disable_existing_loggers=False, defaults={ 'logfilename' : 'location_accuracy_checker.log' } )
    logger = logging.getLogger('location_accuracy_checker')
    
    #Keep window open during error so the user can see the error.
    sys.excepthook = handle_exception

    main()




