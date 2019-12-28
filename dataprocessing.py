#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:39:49 2019

@author: martinstephens
"""
import threading
import logging
import queue
from datetime import datetime
import struct
import database
import radiodata

radio_q = queue.Queue()

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')  # TODO: Refactor log level into __config.py__


def unpack_data_packet(format_string, data_packet):
    '''Unpacks data using the supplied format string and returns it in a dict with the timestamp.'''
    logger.debug(f'unpack_data_packet called')
    data_packet['radio_data'] = struct.unpack(format_string, data_packet['radio_data'])
    return data_packet


def expand_radio_data_into_dict(data):
    '''Takes a tuple of unpacked radio data and splits it out into dictionaries.'''
    logger.debug(f'expand_radio_data_into_dict called')
    readings = data['radio_data']
    munged_data = {'node': {'node_id': readings[0],
                            'pkt_serial': readings[2],
                            'status_register': readings[3],
                            'unused_1': readings[4],
                            'unused_2': readings[5],
                            }, 'sensors': {'timestamp': data['timestamp']}}
    zipped_sensor_readings = list(zip(readings[radiodata.sensor_offset::2],
                                      readings[radiodata.sensor_offset + 1::2]))
    munged_data['sensors']['sensor_readings'] = [x for x in zipped_sensor_readings if x[0] != 0xff]
    return munged_data


def check_for_duplicate_packet(node_data):
    '''Takes a data packet and checks whether the serial number exists already.'''
    logger.debug(f'check_for_duplicate_packet called')
    node_id = node_data['node_id']
    new_packet_serial_number = node_data['pkt_serial']
    old_packet_serial_number = radiodata.last_packet_serial_number.get(node_id)
    if new_packet_serial_number != old_packet_serial_number:
        try:
            if new_packet_serial_number != (old_packet_serial_number + 1) % 0xffff:
                logger.warning(f'Data packet missing from node 0x{node_id:02x}')
        except TypeError:  # This is the first packet from this node, so there is nothing to compare.
            pass
        radiodata.last_packet_serial_number[node_id] = new_packet_serial_number
        return False
    return True


def process_radio_data():
    '''Gets a data packet, checks that it is new, then writes it to the database.'''
    logger.debug(f'process_radio_data called')
    global radio_q
    received_data = {'timestamp': datetime.utcnow(), 'radio_data': radio_q.get()}
    unpacked_data = unpack_data_packet(radiodata.radio_data_format, received_data)
    expanded_data = expand_radio_data_into_dict(unpacked_data)
    if not check_for_duplicate_packet(expanded_data['node']):
        database.write_sensor_reading_to_db(expanded_data['sensors'])
    radio_q.task_done()


def init_data_processing_thread():
    logger.debug(f'init_data_processing_thread called')
    data_thread = threading.Thread(target=loop_process_radio_data)
    data_thread.daemon = True
    data_thread.start()
    return data_thread


def loop_process_radio_data():
    logger.debug(f'loop_process_radio_data called')
    while True:
        process_radio_data()