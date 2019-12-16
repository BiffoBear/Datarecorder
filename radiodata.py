#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 10:23:09 2019

@author: martinstephens
"""

# 60 (0x3c) bytes are available, limited by the radio specs. The last two bytes are for the CRC leaving 58 for data.
# STRUCT_FORMAT 7 status bytes, 10 sensor ID + float pairs and two bytes for error checking
# Byte address    Code    Purpose
# 0x00            B       Node ID of Tx node
# 0x01            B       Tx node ID repeat (compared with byte 0x00 if CRC fails, gives confidence that ID is correct)
# 0x02 - 03       H       Reserved for packet serial number
# 0x04 - 06       H       Reserved for status bits
# 0x07 - 08       BB      Reserved
# 0x07 - 3a       Bf      Pairs of unisigned integer for sensor ID and 4 byte floats for sensor readings
# 0x3a - 3c               Not used in struct, 16 bit CRC is appended for Tx and stripped after Rx and CRC check

# sensor 0xff is sent as padding when no sensor exists and should not be recorded in the database.

import struct

radio_data_format = '>BBHHBBBfBfBfBfBfBfBfBfBfBf'
max_packet_length = 58  # Leaves two bytes for the CRC16
set_packet_length = struct.calcsize(radio_data_format)
sensor_count = radio_data_format.count('f')
sensor_offset = radio_data_format.find('Bf') - 1  # lists are zero indexed
last_packet_serial_number = {} # Stores the latest packet serial number from each node. Lock before updating!


def crc16(data):
    '''Takes a bytes object and calcuates the CRC-16/CCITT-FALSE.'''
    # Modifed from a stackoverflow answer at https://stackoverflow.com/a/55850496/7969814
    crc = 0xFFFF
    for i in range(len(data)):
        crc ^= data[i] << 8
        []
        for _ in range(8):
            if (crc & 0x8000) > 0:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF


def append_crc(data_packet):
    '''Appends the 16 bit CRC to the end of the datapacket.'''
    crc = crc16(data_packet)
    return bytes(data_packet + bytes([crc >> 8]) + bytes([crc & 0xff]))  # high byte + low byte


def check_crc(data_packet):
    '''Checks the CRC of a data_packet and reuturns True if it's 0 and False otherwise.'''
    return bool(crc16(data_packet) == 0)


def read_radio_buffer(radio):
    '''Returns the result of a Radio's get_buffer method after confirming and removing CRC.'''
    rx_packet = radio.get_buffer()
    if rx_packet is None:
        return None
    if check_crc(rx_packet):
        return rx_packet[:-2]
    # TODO: Log an error
    return None
