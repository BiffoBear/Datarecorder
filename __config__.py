#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 13:21:10 2019

@author: pi
"""
import logging
import os

RFM69_INTERRUPT_PIN = 24
DB_URL = 'postgresql://pi:redcurrantdata@localhost:5432/housedata'

try:
    testing = int(os.environ['TESTING'])
except KeyError:
    testing = False

if testing:
    TESTING = True
    FILE_DEBUG_LEVEL = logging.DEBUG
    CONSOLE_DEBUG_LEVEL = logging.DEBUG
    DB_URL = 'postgresql://pi:gooseberry@localhost:5432/housedata'
else:
    TESTING = False
    FILE_DEBUG_LEVEL = logging.WARNING
    CONSOLE_DEBUG_LEVEL = logging.INFO

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64

SI_UNITS = {'Length': {'unit': 'meter', 'symbol': 'm'},
            'Volume': {'unit': 'cubic meter', 'symbol': 'm3'},
            'Mass': {'unit': 'kilogram', 'symbol': 'kg'},
            'Force': {'unit': 'newton', 'symbol': 'N'},
            'Pressure': {'unit': 'pascal', 'symbol': 'Pa'},
            'Temperature': {'unit': 'kelvin', 'symbol': 'K'},
            'Time': {'unit': 'second', 'symbol': 's'},
            'Potential': {'unit': 'volt', 'symbol': 'V'},
            'Current': {'unit': 'ampere', 'symbol': 'A'},
            'Power': {'unit': 'watt', 'symbol': 'W'},
            'Resistance': {'unit': 'ohm', 'symbol': 'Ω'},
            'Frequency': {'unit': 'hertz', 'symbol': 'Hz'},
            'Energy': {'unit': 'joule', 'symbol': 'J'},
            'Luminosity': {'unit': 'candle', 'symbol': 'cd'},
            'Illuminance': {'unit': 'lux', 'symbol': 'lx'},
            'Percentage': {'unit': 'percent', 'symbol': '%'},
            'Velocity': {'unit': 'meters per second', 'symbol': 'm/s'},
            'Acceleration': {'unit': 'meters per second squared', 'symbol': 'm/s^2'},
            'Flow': {'unit': 'cubic meters per second', 'symbol': 'm3/s'},
            }
