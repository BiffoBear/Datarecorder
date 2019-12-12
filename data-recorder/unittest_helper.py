#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 14:25:40 2019

@author: martinstephens
"""
from datetime import datetime
import struct
import database
import radiodata
import random
import time

global_test_time  = datetime(2019, 12, 10, 21, 45, 56)
dummy_data = (0x0a, 0x0a, 0x0a0a, 0xf0f0, 0xaa, 0xbb,
              0x00, 0.1234, 0x01, 1.2345, 0x02, 2.3456, 0x03, 3.4567, 0x04, 4.5678,
              0x05, -5.6789, 0x06, 0.0, 0x07, 7891, 0x08, -999, 0xff, 0,
              )
current_format = '>BBHHBBBfBfBfBfBfBfBfBfBfBf'
rx_data_CRC_good = b'\n\n\n\n\xf0\xf0\xaa\xbb\x00=\xfc\xb9$\x01?\x9e\x04\x19\x02@\x16\x1eO\x03@]:\x93\x04@\x92+k\x05\xc0\xb5\xb9\x8c\x06\x00\x00\x00\x00\x07E\xf6\x98\x00\x08\xc4y\xc0\x00\xff\x00\x00\x00\x00\x94\x1b'
rx_data_CRC_bad = b'\m\n\n\n\xf0\xf0\xaa\xbb\x00=\xfc\xb9$\x01?\x9e\x04\x19\x02@\x16\x1eO\x03@]:\x93\x04@\x92+k\x05\xc0\xb5\xb9\x8c\x06\x00\x00\x00\x00\x07E\xf6\x98\x00\x08\xc4y\xc0\x00\xff\x00\x00\x00\x00\x94\x1b'
node_keys = ['node_id', 'pkt_serial', 'status_register', 'unused_1', 'unused_2',]
first_sensor_offset = 6
sensor_count = 10


class Radio():
    
    def __init__(self):
        self.realism = False
        self.packets_returned = 0
        self.buffer_read_count = 0
        self.packet_serial_number = 0
    
    def get_buffer(self):
        self.buffer_read_count += 1
        if self.realism:
            time.sleep(random.random())
            if random.random() < 0.2:
                return None
        self.packet_serial_number += 1    
        self.packets_returned += 1
        return radiodata.append_crc(dummy_buffer_data_with_serial_number(self.packet_serial_number))
    
    def set_realism(self, realistic=True):
        self.realism = realistic
        
    def get_stats(self):
        return {'reads': self.buffer_read_count, 'packets': self.packets_returned}

def dummy_buffer_data_with_serial_number(sn):
    x = list(dummy_data)
    x[2] = sn
    return struct.pack(radiodata.radio_data_format, *x)


def dummy_radio_data():
    return struct.pack(radiodata.radio_data_format, *dummy_data)
    # TODO: check where this is used and whether it is used as raw buffer data
    # TODO: refactor to dummy_radio_struct_data


def dummy_unpacked_data():    
    return {'timestamp': global_test_time,
            'radio_data': dummy_radio_data()}


def initialize_database(db_in_memory=True):
    if db_in_memory:
        db_url = 'sqlite://'
    else:
        db_url = 'postgresql://pi:blueberry@localhost:5432/housedata'
#        db_url = 'sqlite:////Users/martinstephens/database.db'
    database.initialize_database(db_url)
            

def kill_database():
    database.Base.metadata.drop_all(database.engine)
    database.engine.dispose()


def count_all_records():
    s = database.session()
    t = database.SensorData
    r = s.query(t).count()
    s.close()   
    return r


def return_first_record():
    s = database.session()
    t = database.SensorData
    r = s.query(t).first()
    s.close()   
    return r    

def check_for_gaps():
    s = database.session()
    t = database.Serial
    q = s.query(t).with_entities(t.Pkt_Serial).order_by(t.Pkt_Serial)
    m = [x[0] for x in list(q)]
    r = list(set(m))
    v = zip(r[:-2], r[1:])
    u = [x[0] + 1 for x in v if abs(x[1] - x[0]) > 1]
    s.close()
    return u
