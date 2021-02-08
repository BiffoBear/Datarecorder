#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase
import struct
from Datarecorder.radiohelper import radiohelper

RX_DATA_BAD_CRC = (
    b"\r\n\n\n\xf0\xf0\xaa\xbb\x00=\xfc\xb9$\x01?\x9e\x04\x19\x02@\x16"
    b"\x1eO\x03@]:\x93\x04@\x92+k\x05\xc0\xb5\xb9\x8c\x06\x00\x00\x00"
    b"\x00\x07E\xf6\x98\x00\x08\xc4y\xc0\x00\xff\x00\x00\x00\x00\x94\x1b"
)
RX_DATA_GOOD_CRC = (
    b"\n\n\n\n\xf0\xf0\xaa\xbb\x00=\xfc\xb9$\x01?\x9e\x04\x19\x02@\x16"
    b"\x1eO\x03@]:\x93\x04@\x92+k\x05\xc0\xb5\xb9\x8c\x06\x00\x00\x00"
    b"\x00\x07E\xf6\x98\x00\x08\xc4y\xc0\x00\xff\x00\x00\x00\x00\x94\x1b"
)
DUMMY_DATA = (
    0x0A,
    0x0A,
    0x0A0A,
    0xF0F0,
    0xAA,
    0xBB,
    0x00,
    0.1234,
    0x01,
    1.2345,
    0x02,
    2.3456,
    0x03,
    3.4567,
    0x04,
    4.5678,
    0x05,
    -5.6789,
    0x06,
    0.0,
    0x07,
    7891,
    0x08,
    -999,
    0xFF,
    0,
)
CURRENT_DATA_STRUCT_FORMAT = ">BBHHBBBfBfBfBfBfBfBfBfBfBf"
FIRST_SENSOR_OFFSET = 6
SENSOR_COUNT = 10


def split_crc_result_into_bytes(crc_result):
    return bytes([crc_result >> 8, crc_result & 0xFF])


class TestIncrementNumber(TestCase):
    def test_Increment_with_wrap_increments(self):
        self.assertEqual(0x02, radiohelper.Increment_with_wrap(0x01))

    def test_Increment_with_wrap_wraps(self):
        self.assertEqual(0x00, radiohelper.Increment_with_wrap(0xFFFF))

    def test_Increment_with_wrap_raises_typeerror_if_number_not_number(self):
        for incorrect_arg in ("x", []):
            with self.assertRaises(TypeError) as dm:
                # noinspection PyTypeChecker
                radiohelper.Increment_with_wrap(incorrect_arg)
            self.assertIn("number and wrap_at must be numbers", dm.exception.args)

    def test_Increment_with_wrap_raises_typeerror_if_wrap_at_is_not_number(self):
        for incorrect_arg in ("x", []):
            with self.assertRaises(TypeError) as dm:
                radiohelper.Increment_with_wrap(1, wrap_at=incorrect_arg)
            self.assertIn("number and wrap_at must be numbers", dm.exception.args)


class TestCrcChecking(TestCase):
    def test_radio_data_raises_valueerror_if_crc_is_bad(self):
        with self.assertRaises(ValueError):
            self.assertEqual(radiohelper.confirm_and_strip_crc(RX_DATA_BAD_CRC), None)

    def test_radio_data_returns_correct_data_if_crc_is_good(self):
        self.assertEqual(
            radiohelper.confirm_and_strip_crc(RX_DATA_GOOD_CRC),
            struct.pack(radiohelper.RADIO_DATA_FORMAT, *DUMMY_DATA),
        )


class TestDecodeData(TestCase):
    def test_confirm_crc16_func_is_correct(self):
        crc_test_data = "123456789"
        valid_crc = 0x29B1  # CRC calculated from https://crccalc.com
        self.assertEqual(
            radiohelper.crc16(bytes(crc_test_data, encoding="UTF-8")), valid_crc
        )

    def test_data_format_string_is_valid(self):
        self.assertEqual(radiohelper.RADIO_DATA_FORMAT, CURRENT_DATA_STRUCT_FORMAT)
        self.assertLessEqual(
            radiohelper.set_packet_length, radiohelper.MAX_PACKET_LENGTH
        )
        self.assertEqual(
            radiohelper.RADIO_DATA_FORMAT[0], ">"
        )  # struct should be big-endian
        self.assertEqual(
            radiohelper.RADIO_DATA_FORMAT[1:3], "BB"
        )  # first 2 bytes must be unsigned char
        self.assertEqual(radiohelper.sensor_count, SENSOR_COUNT)
        self.assertEqual(radiohelper.sensor_offset, FIRST_SENSOR_OFFSET)

    def test_check_crc_returns_true_or_false(self):
        test_data = struct.pack(">HH", 0xAAAA, 0xBBBB)
        test_data_with_crc = bytearray(radiohelper.append_crc(test_data))
        self.assertTrue(radiohelper.check_crc(test_data_with_crc))
        test_data_with_crc[1] ^= test_data_with_crc[1]  # Change one bit in data
        self.assertFalse(radiohelper.check_crc(test_data_with_crc))

    def test_append_crc_adds_correct_crc_to_data(self):
        test_data = struct.pack(">HH", 0xAAAA, 0xBBBB)
        crc = radiohelper.crc16(test_data)
        test_data_with_crc = radiohelper.append_crc(test_data)
        self.assertEqual(test_data_with_crc[-2:], split_crc_result_into_bytes(crc))
