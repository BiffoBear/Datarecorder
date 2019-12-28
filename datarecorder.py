#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:39:49 2019

@author: martinstephens
"""
import threading
import logging
import queue
import time
from datetime import datetime
import struct
import database
import hardware
import radiodata
from tests import unittest_helper
from __config__ import HAS_RADIO

radio_q = queue.Queue()

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')  # TODO: Refactor log level into __config.py__


def check_for_radio_data(radio_to_check):
    """Returns the result of a Radio's get_buffer method as a dict with a timestamp.

    Arguments:
        radio -- an instance of class Radio.
        """
    logger.debug(f'check_for_radio_data called')
    return radiodata.read_radio_buffer(radio_to_check)


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


def add_data_to_queue(data_packet):
    logger.debug(f'add_data_to_queue called')
    global radio_q
    radio_q.put(data_packet)


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


def initialize_logging():
    # create file handler which logs even debug messages
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s: %(name)-12s: %(levelname)-8s: %(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        filename='testing.log',  # '/temp/myapp.log',
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    

initialize_logging()


if __name__ == '__main__':
    DB_URL = 'postgresql://pi:blueberry@localhost:5432/housedata'
    database.initialize_database(DB_URL)
    if HAS_RADIO:
        radio = hardware.Radio()
    else:
        radio = hardware.FakeRadio()
        radio.set_realism()
    thread = init_data_processing_thread()
    finish_time = time.time() + 30
    try:
        # for x in range(100):
        while time.time() < finish_time:
            y = check_for_radio_data(radio)
            if y is not None:
                radio_q.put(y)
        radio_q.join()
        z = radio.get_stats()
        print(f'Packets written: {unittest_helper.count_all_records() // 9}')
        print(f"Packets sent   : {radio.get_stats()['packets']}")
    #    print(f'Missing Packets: {unittest_helper.check_for_gaps()}')
    except Exception as e:
        raise e
    finally:
        unittest_helper.kill_database()
