#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:36:28 2019

@author: martinstephens
"""
from unittest import TestCase, skip
from unittest.mock import patch
from threading import Lock
from datetime import datetime
import threading
import housedata
import radiodata
import unittest_helper


#@skip
@patch('radiodata.read_radio_buffer')
class TestDataReading(TestCase):
    
    def test_when_radio_buffer_returns_none_then_check_radio_data_returns_none(self, _):
        radio = None
        radiodata.read_radio_buffer.return_value = None
        self.assertEqual(housedata.check_for_radio_data(radio), None)      

    def test_check_radio_data_returns_a_dict_with_correct_keys_and_data(self, _):
        radio = None
        radiodata.read_radio_buffer.return_value='Some radio data'
        x = housedata.check_for_radio_data(radio)
        self.assertIsInstance(x, dict)
        self.assertEqual(list(x), ['timestamp', 'radio_data'])
        self.assertIsInstance(x['timestamp'], type(unittest_helper.global_test_time))
        self.assertEqual(x['radio_data'], 'Some radio data')


#@skip
class TestDataPrep(TestCase):
    
    def test_struct_is_unpacked_correctly(self):
        decoded_data = housedata.unpack_data_packet(radiodata.radio_data_format,
                                                         unittest_helper.dummy_unpacked_data())
        self.assertEqual(len(decoded_data['radio_data']), len(unittest_helper.dummy_data))
        self.assertEqual(decoded_data['timestamp'], unittest_helper.global_test_time)
        for x in zip(decoded_data['radio_data'], unittest_helper.dummy_data):
            self.assertAlmostEqual(x[0], x[1], places=2)
                        
    def test_data_munged_correctly(self):
        test_data = {'timestamp': unittest_helper.global_test_time,
                     'radio_data': unittest_helper.dummy_data}
        data_returned = housedata.expand_radio_data_into_dict(test_data)
        self.assertIsInstance(data_returned, dict)
        self.assertIsInstance(data_returned['node'], dict)
        node_data = data_returned['node']
        self.assertEqual(list(node_data.keys()), unittest_helper.node_keys)
        self.assertEqual(node_data['node_id'], unittest_helper.dummy_data[0])
        self.assertEqual(node_data['pkt_serial'], unittest_helper.dummy_data[2])
        self.assertEqual(node_data['status_register'], unittest_helper.dummy_data[3])
        self.assertEqual(node_data['unused_1'], unittest_helper.dummy_data[4])
        self.assertEqual(node_data['unused_2'], unittest_helper.dummy_data[5])
        self.assertEqual(data_returned['sensors']['timestamp'], unittest_helper.global_test_time)
        sensor_data = data_returned['sensors']['sensor_readings']
        self.assertIsInstance(data_returned, dict)
        self.assertEqual(len(sensor_data), radiodata.sensor_count - 1)  # One sensor is 0xff, thus ignored


class CheckForRepeatPacket(TestCase):
    
    def test_check_for_duplicate_packet_returns_true_and_dict_if_duplicate(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        radiodata.last_packet_serial_number = {0x01: 0x1010,}
        x = housedata.check_for_duplicate_packet(test_data)
        self.assertIsInstance(x, bool)
        self.assertTrue(x)
        self.assertEqual(radiodata.last_packet_serial_number, {0x01: 0x1010,})

    def test_check_for_duplicate_returns_false_and_updates_dict_if_not_duplicate(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        radiodata.last_packet_serial_number = {0x01: 0x1011,}
        x  = housedata.check_for_duplicate_packet(test_data)
        self.assertIsInstance(x, bool)        
        self.assertFalse(x)
        self.assertEqual(radiodata.last_packet_serial_number, {0x01: 0x1010})
        
    def test_new_node_added_to_dict(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        radiodata.last_packet_serial_number = {0x02: 0xffff}
        x  = housedata.check_for_duplicate_packet(test_data)
        self.assertIsInstance(x, bool)        
        self.assertFalse(x)
        self.assertEqual(radiodata.last_packet_serial_number[0x01], 0x1010)
        
        
#@skip
class TestReadRadioAndWriteDataToDataBase(TestCase):
    
    def test_read_radio_process_data_write_to_db(self):
        unittest_helper.initialize_database(db_in_memory=True)
        lock = Lock()
        initial = unittest_helper.count_all_records()
        housedata.process_radio_data(unittest_helper.dummy_unpacked_data(), lock)
        final = unittest_helper.count_all_records()
        self.assertEqual(final, initial + 9)
        # shouldn't write twice with duplicate data packets
        housedata.process_radio_data(unittest_helper.dummy_unpacked_data(), lock)
        final = unittest_helper.count_all_records()
        self.assertEqual(final, initial + 9)
        unittest_helper.kill_database()

#@skip
@patch('housedata.check_for_radio_data')
@patch('threading.Thread')
class TestThreading(TestCase):
        
    def test_threading_not_called_if_radio_buffer_is_empty(self, _a, _b):
        radio = None
        lock = None
        housedata.check_for_radio_data.return_value = None
        housedata.check_radio_buffer_and_spawn_thread_if_required(radio, lock)
        threading.Thread.assert_not_called()
        
    def test_threading_called_with_correct_args_if_buffer_is_full(self, _a, _b):
        radio = None
        lock = None
        housedata.check_for_radio_data.return_value = 'Not None'
        housedata.check_radio_buffer_and_spawn_thread_if_required(radio, lock)
        threading.Thread.assert_called_once_with(target=housedata.process_radio_data, args=['Not None', lock],
                                 name='db_thread')
        # TODO: Work out how to confirm that the thread was started        
        