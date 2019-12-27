#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 12:30:25 2019

@author: martinstephens
"""
import logging
import board
import time
import busio
import digitalio
import adafruit_rfm69
import adafruit_ssd1306

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


class Radio:
    '''Connects to an Adafruit RFM69 radio and has methods to check for data and return stats.'''

    def __init__(self):
        self._cs = digitalio.DigitalInOut(board.CE1)
        self._reset = digitalio.DigitalInOut(board.D25)
        self._spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        try:
            self._rfm69 = adafruit_rfm69.RFM69(self._spi, self._cs, self._reset, 433.0)
            logger.info(f'RFM69 radio initialized successfully')
        except RuntimeError as error:
            logger.critical(f'RFM69 radio failed to initialize with RuntimeError')
            raise error
        # TODO: Refactor encryption key to __config.py__ and then possibly an envirionment variable
        self._rfm69.encryption_key = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        self._packets_returned = 0
        self._buffer_read_count = 0

    def get_buffer(self):
        '''Returns the content of the radio buffer, increments counters for reads and packets.'''
        logger.debug('Radio.get_buffer called')
        try:
            buffer_content = self._rfm69.receive()
        except Exception as error:
            logger.critical(f'Unable to read RFM69 buffer')
            raise error
        self._buffer_read_count += 1
        if buffer_content is not None:
            self._packets_returned += 1
        return buffer_content

    def get_stats(self):
        '''Returns the radio buffer reads and packets received since the radio started up.'''
        logger.debug(f'Radio.get_stats called')
        return {'reads': self._buffer_read_count, 'packets': self._packets_returned}


# class FakeRadio:
#     '''Dummy Radio with methods to check for data and return stats.'''
#
#     def __init__(self):
#         self.realism = False
#         self.packets_returned = 0
#         self.buffer_read_count = 0
#         self.packet_serial_number = 0
#
#     def get_buffer(self):
#         self.buffer_read_count += 1
#         if self.realism:
#             time.sleep(random.random())
#             if random.random() < 0.2:
#                 return None
#         self.packet_serial_number += 1
#         self.packets_returned += 1
#         return radiodata.append_crc(dummy_buffer_data_with_serial_number(self.packet_serial_number))
#
#     def set_realism(self, realistic=True):
#         self.realism = realistic
#
#     def get_stats(self):
#         return {'reads': self.buffer_read_count, 'packets': self.packets_returned}


# class Display:
#
#     def __init__(self):
#         self._reset_pin = digitalio.DigitalInOut(board.D4)
#         self._i2c = busio.I2C(board.SCL, board.SDA)
#         self._display = adafruit_ssd1306.SSD1306_I2C(128, 32, self._i2c, reset=self._reset_pin)
