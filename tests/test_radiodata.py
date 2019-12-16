#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 10:23:09 2019

@author: martinstephens
"""
from unittest import TestCase, skip
from unittest.mock import Mock
import struct
from datarecorder import radiodata
from tests import unittest_helper


# @skip
class TestDataReading(TestCase):

    def setUp(self):
        self.radio = Mock()

    def test_radio_get_buffer_returns_none_if_buffer_empty(self):
        self.radio.get_buffer.return_value=None
        self.assertEqual(radiodata.read_radio_buffer(self.radio), None)

    def test_radio_data_returns_none_if_crc_is_bad(self):
        self.radio.get_buffer.return_value= unittest_helper.rx_data_CRC_bad
        self.assertEqual(radiodata.read_radio_buffer(self.radio), None)

    def test_radio_data_returns_correct_data_if_crc_is_good(self):
        self.radio.get_buffer.return_value= unittest_helper.rx_data_CRC_good
        self.assertEqual(radiodata.read_radio_buffer(self.radio), unittest_helper.dummy_radio_data())


# @skip
class TestDecodeData(TestCase):

    def split_crc_result_into_bytes(self, crc_result):
        return bytes([crc_result >> 8, crc_result & 0xff])

    def test_confirm_crc16_func_is_correct(self):
        crc_test_data = '123456789'
        valid_crc = 0x29b1  # CRC cacluated from https://crccalc.com
        self.assertEqual(radiodata.crc16(bytes(crc_test_data, encoding='UTF-8')), valid_crc)

    def test_data_format_string_is_valid(self):
        self.assertEqual(radiodata.radio_data_format, unittest_helper.current_format)
        self.assertLessEqual(radiodata.set_packet_length, radiodata.max_packet_length)
        self.assertEqual(radiodata.radio_data_format[0], '>')  # struct should be big-endian
        self.assertEqual(radiodata.radio_data_format[1:3], 'BB')  # first 2 bytes must be unsigned char
        self.assertEqual(radiodata.sensor_count, unittest_helper.sensor_count)
        self.assertEqual(radiodata.sensor_offset, unittest_helper.first_sensor_offset)

    def test_check_crc_returns_true_or_false(self):
        test_data = struct.pack('>HH', 0xaaaa, 0xbbbb)
        test_data_with_crc = bytearray(radiodata.append_crc(test_data))
        self.assertTrue(radiodata.check_crc(test_data_with_crc))
        test_data_with_crc[1] ^= test_data_with_crc[1]  # Change one bit in data
        self.assertFalse(radiodata.check_crc(test_data_with_crc))

    def test_append_crc_adds_correct_crc_to_data(self):
        test_data = struct.pack('>HH', 0xaaaa, 0xbbbb)
        crc = radiodata.crc16(test_data)
        test_data_with_crc = radiodata.append_crc(test_data)
        self.assertEqual(test_data_with_crc[-2:], self.split_crc_result_into_bytes(crc))
