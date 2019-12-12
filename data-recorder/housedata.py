#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:39:49 2019

@author: martinstephens
"""
import threading
import queue
import time
from datetime import datetime
import struct
import hardware
import database
import radiodata
import unittest_helper
from __config__ import TESTING

radio_q = queue.Queue()

def check_for_radio_data(radio_to_check):
    """Returns the result of a Radio's get_buffer method as a dict with a timestamp.

    Arguments:
        radio -- an instance of class Radio.
        """
    return radiodata.read_radio_buffer(radio_to_check)
#    if buffer_data is not None:
#        return {'timestamp': datetime.utcnow(), 'radio_data': buffer_data}
#    return None


def unpack_data_packet(format_string, data_packet):
    '''Unpacks data using the supplied format string and returns it in a dict with the timestamp.'''
    data_packet['radio_data'] = struct.unpack(format_string, data_packet['radio_data'])
    return data_packet


def expand_radio_data_into_dict(data):
    '''Takes a tuple of unpacked radio data and splits it out into dictionaries.'''
    readings = data['radio_data']
    munged_data = {'node': {'node_id': readings[0],
                            'pkt_serial': readings[2],
                            'status_register': readings[3],
                            'unused_1': readings[4],
                            'unused_2': readings[5],
                            }
                   }
    munged_data['sensors'] = {'timestamp': data['timestamp']}
    zipped_sensor_readings = list(zip(readings[radiodata.sensor_offset::2],
                                      readings[radiodata.sensor_offset+1::2]))
    munged_data['sensors']['sensor_readings'] = [x for x in zipped_sensor_readings if x[0] != 0xff]
    return munged_data


def check_for_duplicate_packet(node_data):
    '''Takes a data packet and checks whether the serial number exists already.'''
    node_id = node_data['node_id']
    new_packet_serial_number = node_data['pkt_serial']
    if radiodata.last_packet_serial_number.get(node_id) != new_packet_serial_number:
        radiodata.last_packet_serial_number[node_id] = new_packet_serial_number
        return False
    return True


def process_radio_data():
    '''Gets a data packet, checks that it is new, then writes it to the database.'''
    global radio_q
    received_data = {'timestamp': datetime.utcnow(), 'radio_data': radio_q.get()}
    unpacked_data = unpack_data_packet(radiodata.radio_data_format, received_data)
    expanded_data = expand_radio_data_into_dict(unpacked_data)
    if not check_for_duplicate_packet(expanded_data['node']):
        database.write_sensor_reading_to_db(expanded_data['sensors'])
    radio_q.task_done()


def add_data_to_queue(data_packet):
    global radio_q
    radio_q.put(data_packet)


def init_data_processing_thread():
    thread = threading.Thread(target=loop_process_radio_data)
    thread.daemon = True
    thread.start()
    return thread


def loop_process_radio_data():
    while True:
        process_radio_data()


if __name__ == '__main__':
    DB_URL = 'postgresql://pi:blueberry@localhost:5432/housedata'
    database.initialize_database(DB_URL)
    if not TESTING:
        radio = hardware.Radio()
    else:
        radio = unittest_helper.Radio()
    thread = init_data_processing_thread()
    for x in range(10):
        radio_q.put(unittest_helper.dummy_radio_data)
    radio_q.join()
    print(unittest_helper.count_all_records() // 9)
    print(unittest_helper.count_all_records() % 9)
#    print(f'Missing Packets: {unittest_helper.check_for_gaps()}')
    unittest_helper.kill_database()
