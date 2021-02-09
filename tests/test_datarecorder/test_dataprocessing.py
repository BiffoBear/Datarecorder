#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:36:28 2019

@author: martinstephens
"""
from unittest import TestCase
import threading
import datetime

from Datarecorder.datarecorder import _dataprocessing
from Datarecorder.helpers import radiohelper
from tests import conftest


class TestDataPrep(TestCase):
    def test_struct_is_unpacked_correctly(self):
        decoded_data = _dataprocessing.unpack_data_packet(
            radiohelper.RADIO_DATA_FORMAT,
            {
                "timestamp": conftest.global_test_time,
                "radio_data": conftest.rx_data_CRC_good,
            },
        )
        self.assertEqual(len(decoded_data["radio_data"]), len(conftest.dummy_data))
        self.assertEqual(decoded_data["timestamp"], conftest.global_test_time)
        [
            self.assertAlmostEqual(x[0], x[1], places=2)
            for x in zip(decoded_data["radio_data"], conftest.dummy_data)
        ]

    def test_data_munged_correctly(self):
        test_data = {
            "timestamp": conftest.global_test_time,
            "radio_data": conftest.dummy_data,
        }
        data_returned = _dataprocessing.expand_radio_data_into_dict(test_data)
        self.assertIsInstance(data_returned, dict)
        self.assertIsInstance(data_returned["node"], dict)
        node_data = data_returned["node"]
        self.assertEqual(list(node_data.keys()), conftest.node_keys)
        self.assertEqual(node_data["node_id"], conftest.dummy_data[0])
        self.assertEqual(node_data["pkt_serial"], conftest.dummy_data[2])
        self.assertEqual(node_data["status_register"], conftest.dummy_data[3])
        self.assertEqual(node_data["unused_1"], conftest.dummy_data[4])
        self.assertEqual(node_data["unused_2"], conftest.dummy_data[5])
        self.assertEqual(
            data_returned["sensors"]["timestamp"], conftest.global_test_time
        )
        sensor_data = data_returned["sensors"]["sensor_readings"]
        self.assertIsInstance(data_returned, dict)
        self.assertEqual(
            len(sensor_data), radiohelper.SENSOR_COUNT - 1
        )  # One sensor is 0xff, thus ignored


class CheckForRepeatPacket(TestCase):
    def test_check_for_duplicate_packet_returns_true_and_dict_if_duplicate(self):
        test_data = {"node_id": 0x01, "pkt_serial": 0x1010}
        _dataprocessing.last_packet_info = {
            0x01: {"pkt_serial": 0x1010, "timestamp": None}
        }
        x = _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIsInstance(x, bool)
        self.assertTrue(x)
        self.assertEqual(_dataprocessing.last_packet_info[0x01]["pkt_serial"], 0x1010)

    def test_check_for_duplicate_returns_false_and_updates_dict_if_not_duplicate(self):
        test_data = {"node_id": 0x01, "pkt_serial": 0x1010}
        _dataprocessing.last_packet_info = {
            0x01: {"pkt_serial": 0x1011, "timestamp": None}
        }
        x = _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIsInstance(x, bool)
        self.assertFalse(x)
        self.assertEqual(_dataprocessing.last_packet_info[0x01]["pkt_serial"], 0x1010)

    def test_check_for_duplicate_handles_wrap_around_of_serial_numbers(self):
        test_data = {"node_id": 0x02, "pkt_serial": 0x0001}
        _dataprocessing.last_packet_info = {
            0x02: {"pkt_serial": 0xFFFE, "timestamp": None}
        }
        _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertEqual(_dataprocessing.last_packet_info[0x02]["pkt_serial"], 0x0001)
        test_data = {"node_id": 0x01, "pkt_serial": 0x0000}
        _dataprocessing.last_packet_info = {
            0x01: 0xFFFE,
        }
        _dataprocessing.packet_missing_or_duplicate(test_data)

    def test_new_node_added_to_dict(self):
        test_data = {"node_id": 0x01, "pkt_serial": 0x1010}
        _dataprocessing.last_packet_info = {
            0x02: {"pkt_serial": 0xFFFF, "timestamp": None}
        }
        x = _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIsInstance(x, bool)
        self.assertFalse(x)
        self.assertEqual(_dataprocessing.last_packet_info[0x01]["pkt_serial"], 0x1010)
        self.assertIsInstance(
            _dataprocessing.last_packet_info[0x01]["timestamp"], datetime.datetime
        )


class TestReadRadioAndWriteDataToDataBase(TestCase):
    def test_read_radio_process_data_write_to_db(self):
        conftest.initialize_database(db_in_memory=True)
        initial = conftest.count_all_sensor_reading_records()
        test_data = [conftest.rx_data_CRC_good, conftest.rx_data_CRC_good]
        [_dataprocessing.radio_q.put(x) for x in test_data]
        _dataprocessing.process_radio_data()
        final = conftest.count_all_sensor_reading_records()
        self.assertEqual(final, initial + 9)
        # shouldn't write twice with duplicate data packets
        _dataprocessing.process_radio_data()
        final = conftest.count_all_sensor_reading_records()
        self.assertEqual(final, initial + 9)
        conftest.kill_database()

    def test_bad_data_packet_logs_a_warning_and_continues_without_writing_to_db(self):
        conftest.initialize_database(db_in_memory=True)
        initial = conftest.count_all_sensor_reading_records()
        test_data = [
            b"bad_data",
        ]
        [_dataprocessing.radio_q.put(x) for x in test_data]
        _dataprocessing.process_radio_data()
        final = conftest.count_all_sensor_reading_records()
        self.assertEqual(final, initial)


class TestThreadingWithQueue(TestCase):
    def test_thread_spawned(self):
        thread = _dataprocessing.init_data_processing_thread()
        self.assertIsInstance(thread, threading.Thread)
        self.assertTrue(thread.daemon)
        self.assertTrue(thread.ident)
