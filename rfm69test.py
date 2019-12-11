# -*- coding: utf-8 -*-

import board
import busio
import digitalio
import adafruit_rfm69


CS = digitalio.DigitalInOut(board.CE1)
reset = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
#spi.configure(baudrate=100000)
try:
    rfm69 = adafruit_rfm69.RFM69(spi, CS, reset, 433.0)
    print(f'RFM dected')
except RuntimeError:
    print(f'Oops')