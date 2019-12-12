#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 12:30:25 2019

@author: martinstephens
"""
import board
import busio
import digitalio
import adafruit_rfm69



class Radio():
    
    def __init__(self):
        CS = digitalio.DigitalInOut(board.CE1)
        reset = digitalio.DigitalInOut(board.D25)
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        try:
            self._rfm69 = adafruit_rfm69.RFM69(spi, CS, reset, 433.0)
            print(f'RFM detected')
        except RuntimeError:
            print(f'Oops')
        self._rfm69.encryption_key = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        self.packets_returned = 0
        self.buffer_read_count = 0
    
    def get_buffer(self):
        x = self._rfm69.receive()
        self.buffer_read_count += 1
        if x is not None:
            self.packets_returned +=1
        return self._rfm69.receive()
    
    def get_stats(self):
        return {'reads': self.buffer_read_count, 'packets': self.packets_returned}