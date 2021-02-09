#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A library of functions that are used by radio Rx scripts.

Increment_with_wrap(serial_number, wrap_at=0x10000) -- increment and modulo a number
crc16(data) -- return a 16 bit CRC for a byte object
"""


# 60 (0x3c) bytes are available, limited by the radio specs.
# STRUCT_FORMAT 7 status bytes, 10 sensor ID + float pairs and two bytes for error checking
# Byte address    Code    Purpose
# 0x00            B       Node ID of Tx node
# 0x01            B       Tx node ID repeat (If CRC fails and both ID's match, helps id the node)
# 0x02 - 03       H       Packet serial number
# 0x04 - 05       H       Status bits
# 0x05 - 06       BB      Reserved
# 0x07 - 3a       Bf      Pairs of unsigned int for sensor ID and 4 byte float for sensor reading
# 0x3b - 3c               CRC. Not used in struct, 16 bit CRC is appended after struct created

# sensor 0xff is sent as padding when no sensor exists and should not be recorded in the database.

import struct
import logging
from __config__ import FILE_DEBUG_LEVEL

logger = logging.getLogger(__name__)
logger.setLevel(FILE_DEBUG_LEVEL)

RFM69_ENCRYPTION_KEY = b"\x16UT\xb6\x92FHaE\xb5B\xde\xbclYs"
# RFM69_ENCRYPTION_KEY = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
RADIO_DATA_FORMAT = ">BBHHBBBfBfBfBfBfBfBfBfBfBf"
MAX_PACKET_LENGTH = (
    58  # Leaves two bytes for the CRC16 as RFM69 max packet size is 60 bytes
)
PACKET_LENGTH = struct.calcsize(RADIO_DATA_FORMAT)
SENSOR_COUNT = RADIO_DATA_FORMAT.count("f")
SENSOR_OFFSET = RADIO_DATA_FORMAT.find("Bf") - 1  # lists are zero indexed


def _try_to_log(log_message):
    # Logging not used on micro-controllers so handle the error
    try:
        logger.debug(log_message)
    except NameError:
        pass


def crc16(bytes_data):
    """Takes a bytes object and returns the CRC-16/CCITT-FALSE."""
    # Modified from a stackoverflow answer at https://stackoverflow.com/a/55850496/7969814
    _try_to_log("crc16 called")
    crc = 0xFFFF
    for byte in bytes_data:
        crc ^= byte << 8
        for _ in range(8):
            if (crc & 0x8000) > 0:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF


def append_crc(data_packet):
    """Appends the 16 bit CRC to the end of the datapacket."""
    _try_to_log("append_crc called")
    crc = crc16(data_packet)
    return bytes(
        data_packet + bytes([crc >> 8]) + bytes([crc & 0xFF])
    )  # high byte + low byte


def check_crc(data_packet):
    """Checks the CRC of a data_packet and returns True if it's 0 and False otherwise."""
    _try_to_log("check_crc called")
    return bool(crc16(data_packet) == 0)


def confirm_and_strip_crc(rx_packet):
    """Returns the result of a Radio's get_buffer method after confirming and removing CRC."""
    _try_to_log("confirm_and_strip_crc called")
    if check_crc(rx_packet):
        _try_to_log("Good data packet")
        return rx_packet[:-2]
    _try_to_log("Bad data packet")
    raise ValueError("Bad data packet")


def increment_with_wrap(number: int, wrap_at=0x10000):
    """Increments an number and returns the modulo of the result.

    Arguments:
    serial_number -- An number to be incremented

    Keyword Arguments:
    wrap_at -- Used to take the modulo of the incremented number (default 0x10000)
    """
    _try_to_log("Increment_with_wrap called")
    try:
        return (number + 1) % wrap_at
    except (ValueError, TypeError) as error:
        raise TypeError("number and wrap_at must be numbers") from error
