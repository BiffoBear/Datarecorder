#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 10:23:09 2019

@author: martinstephens
"""
from unittest import TestCase
import struct
import radiodata
from tests import unittest_helper


def split_crc_result_into_bytes(crc_result):
    return bytes([crc_result >> 8, crc_result & 0xff])


class TestCrcChecking(TestCase):

    def test_radio_data_raises_valueerror_if_crc_is_bad(self):
        with self.assertRaises(ValueError):
            self.assertEqual(radiodata.confirm_and_strip_crc(unittest_helper.rx_data_CRC_bad), None)

    def test_radio_data_returns_correct_data_if_crc_is_good(self):
        self.assertEqual(radiodata.confirm_and_strip_crc(unittest_helper.rx_data_CRC_good),
                         unittest_helper.dummy_radio_data())


class TestDecodeData(TestCase):

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
        self.assertEqual(test_data_with_crc[-2:], split_crc_result_into_bytes(crc))
