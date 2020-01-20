#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 13:21:10 2019

@author: pi
"""
import logging
TESTING = True
RFM69_INTERRUPT_PIN = 24
DB_URL = 'postgresql://pi:blueberry@localhost:5432/housedata'
if TESTING:
    FILE_DEBUG_LEVEL = logging.DEBUG
    CONSOLE_DEBUG_LEVEL = logging.DEBUG
else:
    FILE_DEBUG_LEVEL = logging.INFO
    CONSOLE_DEBUG_LEVEL = logging.INFO

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
