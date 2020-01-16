#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:36:28 2019

@author: martinstephens
"""
from unittest import TestCase, skip
from unittest.mock import patch
import threading
import datetime
import radiodata
import dataprocessing
from tests import unittest_helper


#@skip
class TestDataPrep(TestCase):

    def test_struct_is_unpacked_correctly(self):
        with self.assertLogs() as cm:
            decoded_data = dataprocessing.unpack_data_packet(radiodata.radio_data_format,
                                                             {'timestamp': unittest_helper.global_test_time,
                                                              'radio_data': unittest_helper.rx_data_CRC_good
                                                              })
        self.assertIn('unpack_data_packet called', cm.output[0])
        self.assertEqual(len(decoded_data['radio_data']), len(unittest_helper.dummy_data))
        self.assertEqual(decoded_data['timestamp'], unittest_helper.global_test_time)
        [self.assertAlmostEqual(x[0], x[1], places=2) for x in zip(decoded_data['radio_data'],
                                                                   unittest_helper.dummy_data)]

    def test_data_munged_correctly(self):
        test_data = {'timestamp': unittest_helper.global_test_time,
                     'radio_data': unittest_helper.dummy_data}
        with self.assertLogs() as cm:
            data_returned = dataprocessing.expand_radio_data_into_dict(test_data)
        self.assertIn('expand_radio_data_into_dict called', cm.output[0])
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
        dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x1010, 'timestamp': None}}
        with self.assertLogs() as cm:
            x = dataprocessing.check_for_duplicate_packet(test_data)
        self.assertIn('check_for_duplicate_packet called', cm.output[0])
        self.assertIsInstance(x, bool)
        self.assertTrue(x)
        self.assertEqual(dataprocessing.last_packet_info[0x01]['pkt_serial'], 0x1010)

    def test_check_for_duplicate_returns_false_and_updates_dict_if_not_duplicate(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x1011, 'timestamp': None}}
        x = dataprocessing.check_for_duplicate_packet(test_data)
        self.assertIsInstance(x, bool)
        self.assertFalse(x)
        self.assertEqual(dataprocessing.last_packet_info[0x01]['pkt_serial'], 0x1010)

    def test_check_for_duplicate_logs_a_warning_for_a_missing_packet(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1012}
        dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x0101, 'timestamp': None}}
        with self.assertLogs() as cm:
            dataprocessing.check_for_duplicate_packet(test_data)
        self.assertIn('Data packet missing from node 0x01', cm.output[-1])

    def test_check_for_duplicate_handles_wrap_around_of_serial_numbers(self):
        test_data = {'node_id': 0x02, 'pkt_serial': 0x0001}
        dataprocessing.last_packet_info = {0x02: {'pkt_serial': 0xfffe, 'timestamp': None}}
        with self.assertLogs(level='CRITICAL') as cm:
            dataprocessing.check_for_duplicate_packet(test_data)
        self.assertIn('Data packet missing from node 0x02', cm.output[-1])
        self.assertEqual(dataprocessing.last_packet_info[0x02]['pkt_serial'], 0x0001)
        test_data = {'node_id': 0x01, 'pkt_serial': 0x0000}
        dataprocessing.last_packet_info = {0x01: 0xfffe, }
        with self.assertLogs() as cm:
            dataprocessing.check_for_duplicate_packet(test_data)
        self.assertNotIn('Data packet missing from node 0x01', cm.output[-1])

    def test_new_node_added_to_dict(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        dataprocessing.last_packet_info = {0x02: {'pkt_serial': 0xffff, 'timestamp': None}}
        x = dataprocessing.check_for_duplicate_packet(test_data)
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
        with self.assertLogs() as cm:
            dataprocessing.process_radio_data()
        self.assertIn('process_radio_data called', cm.output[0])
        final = unittest_helper.count_all_records()
        self.assertEqual(final, initial + 9)
        # shouldn't write twice with duplicate data packets
        dataprocessing.process_radio_data()
        final = unittest_helper.count_all_records()
        self.assertEqual(final, initial + 9)
        unittest_helper.kill_database()

    def test_first_packet_from_node_logs_to_info(self):
        dataprocessing.last_packet_info = {}
        with self.assertLogs() as cm:
            dataprocessing.check_for_duplicate_packet({'node_id': 0x01, 'pkt_serial': 9999})
        self.assertIn('First data packet from node 0x01', cm.output[1])

    def test_bad_data_packet_logs_a_warning_and_continues_without_writing_to_db(self):
        unittest_helper.initialize_database(db_in_memory=True)
        initial = unittest_helper.count_all_records()
        test_data = [b'bad_data', ]
        [dataprocessing.radio_q.put(x) for x in test_data]
        with self.assertLogs() as cm:
            dataprocessing.process_radio_data()
        self.assertIn('Bad data packet detected', cm.output[-1])
        final = unittest_helper.count_all_records()
        self.assertEqual(final, initial)


class TestThreadingWithQueue(TestCase):

    def test_thread_spawned(self):
        with self.assertLogs() as cm:
            thread = dataprocessing.init_data_processing_thread()
        self.assertIn('init_data_processing_thread called', cm.output[0])
        self.assertIsInstance(thread, threading.Thread)
        self.assertTrue(thread.daemon)
        self.assertTrue(thread.ident)
        

@skip        
class TestLoggingInitialization(TestCase):
    # TODO: Implement when I've worked out how to mock it all.
    pass
#    housedata.initialize_logging()
