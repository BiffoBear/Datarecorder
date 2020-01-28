#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 14:25:40 2019

@author: martinstephens
"""
from datetime import datetime
from database import database_setup

global_test_time = datetime(2019, 12, 10, 21, 45, 56)
dummy_data = (0x0a, 0x0a, 0x0a0a, 0xf0f0, 0xaa, 0xbb,
              0x00, 0.1234, 0x01, 1.2345, 0x02, 2.3456, 0x03, 3.4567, 0x04, 4.5678,
              0x05, -5.6789, 0x06, 0.0, 0x07, 7891, 0x08, -999, 0xff, 0,
              )
rx_data_CRC_good = b'\n\n\n\n\xf0\xf0\xaa\xbb\x00=\xfc\xb9$\x01?\x9e\x04\x19\x02@\x16' \
                   b'\x1eO\x03@]:\x93\x04@\x92+k\x05\xc0\xb5\xb9\x8c\x06\x00\x00\x00' \
                   b'\x00\x07E\xf6\x98\x00\x08\xc4y\xc0\x00\xff\x00\x00\x00\x00\x94\x1b'
node_keys = ['node_id', 'pkt_serial', 'status_register', 'unused_1', 'unused_2', ]


def initialize_database(db_in_memory=True):
    if db_in_memory:
        db_url = 'sqlite://'
    else:
        db_url = 'postgresql://pi:blueberry@localhost:5432/housedata'
#        db_url = 'sqlite:////Users/martinstephens/database.db'
    database_setup.initialize_database(db_url)
            

def kill_database():
    database_setup.Base.metadata.drop_all(database_setup.engine)
    database_setup.engine.dispose()


def count_all_records():
    s = database_setup.session()
    t = database_setup.SensorData
    r = s.query(t).count()
    s.close()   
    return r
