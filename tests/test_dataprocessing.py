#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:36:28 2019

@author: martinstephens
"""
from unittest import TestCase
import threading
import datetime
from datarecorder import dataprocessing
from radiohelper import radiohelper
from tests import unittest_helper


class TestDataPrep(TestCase):

    def test_struct_is_unpacked_correctly(self):
        decoded_data = dataprocessing.unpack_data_packet(radiohelper.RADIO_DATA_FORMAT,
                                                         {'timestamp': unittest_helper.global_test_time,
                                                          'radio_data': unittest_helper.rx_data_CRC_good
                                                          })
        self.assertEqual(len(decoded_data['radio_data']), len(unittest_helper.dummy_data))
        self.assertEqual(decoded_data['timestamp'], unittest_helper.global_test_time)
        [self.assertAlmostEqual(x[0], x[1], places=2) for x in zip(decoded_data['radio_data'],
                                                                   unittest_helper.dummy_data)]

    def test_data_munged_correctly(self):
        test_data = {'timestamp': unittest_helper.global_test_time,
                     'radio_data': unittest_helper.dummy_data}
        data_returned = dataprocessing.expand_radio_data_into_dict(test_data)
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
        self.assertEqual(len(sensor_data), radiohelper.sensor_count - 1)  # One sensor is 0xff, thus ignored


class CheckForRepeatPacket(TestCase):

    def test_check_for_duplicate_packet_returns_true_and_dict_if_duplicate(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x1010, 'timestamp': None}}
        x = dataprocessing.check_for_duplicate_or_missing_packet(test_data)
        self.assertIsInstance(x, bool)
        self.assertTrue(x)
        self.assertEqual(dataprocessing.last_packet_info[0x01]['pkt_serial'], 0x1010)

    def test_check_for_duplicate_returns_false_and_updates_dict_if_not_duplicate(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x1011, 'timestamp': None}}
        x = dataprocessing.check_for_duplicate_or_missing_packet(test_data)
        self.assertIsInstance(x, bool)
        self.assertFalse(x)
        self.assertEqual(dataprocessing.last_packet_info[0x01]['pkt_serial'], 0x1010)

    def test_check_for_duplicate_handles_wrap_around_of_serial_numbers(self):
        test_data = {'node_id': 0x02, 'pkt_serial': 0x0001}
        dataprocessing.last_packet_info = {0x02: {'pkt_serial': 0xfffe, 'timestamp': None}}
        dataprocessing.check_for_duplicate_or_missing_packet(test_data)
        self.assertEqual(dataprocessing.last_packet_info[0x02]['pkt_serial'], 0x0001)
        test_data = {'node_id': 0x01, 'pkt_serial': 0x0000}
        dataprocessing.last_packet_info = {0x01: 0xfffe, }
        dataprocessing.check_for_duplicate_or_missing_packet(test_data)

    def test_new_node_added_to_dict(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        dataprocessing.last_packet_info = {0x02: {'pkt_serial': 0xffff, 'timestamp': None}}
        x = dataprocessing.check_for_duplicate_or_missing_packet(test_data)
        self.assertIsInstance(x, bool)
        self.assertFalse(x)
        self.assertEqual(dataprocessing.last_packet_info[0x01]['pkt_serial'], 0x1010)
        self.assertIsInstance(dataprocessing.last_packet_info[0x01]['timestamp'], datetime.datetime)


class TestReadRadioAndWriteDataToDataBase(TestCase):

    def test_read_radio_process_data_write_to_db(self):
        unittest_helper.initialize_database(db_in_memory=True)
        initial = unittest_helper.count_all_records()
        test_data = [unittest_helper.rx_data_CRC_good,
                     unittest_helper.rx_data_CRC_good]
        [dataprocessing.radio_q.put(x) for x in test_data]
        dataprocessing.process_radio_data()
        final = unittest_helper.count_all_records()
        self.assertEqual(final, initial + 9)
        # shouldn't write twice with duplicate data packets
        dataprocessing.process_radio_data()
        final = unittest_helper.count_all_records()
        self.assertEqual(final, initial + 9)
        unittest_helper.kill_database()

    def test_bad_data_packet_logs_a_warning_and_continues_without_writing_to_db(self):
        unittest_helper.initialize_database(db_in_memory=True)
        initial = unittest_helper.count_all_records()
        test_data = [b'bad_data', ]
        [dataprocessing.radio_q.put(x) for x in test_data]
        dataprocessing.process_radio_data()
        final = unittest_helper.count_all_records()
        self.assertEqual(final, initial)


class TestThreadingWithQueue(TestCase):

    def test_thread_spawned(self):
        thread = dataprocessing.init_data_processing_thread()
        self.assertIsInstance(thread, threading.Thread)
        self.assertTrue(thread.daemon)
        self.assertTrue(thread.ident)
