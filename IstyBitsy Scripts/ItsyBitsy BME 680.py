# Write your code here :-)
import time
import random
import struct
import board
import busio
import digitalio
import adafruit_rfm69
import adafruit_bme680
i2c = busio.I2C(board.SCL, board.SDA)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)


spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)
rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, 433.0)
rfm69.encryption_key = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
radio_data_format = '>BBHHBBBfBfBfBfBfBfBfBfBfBf'
NODE_ID = 0x02
SAMPLE_INTERVAL = 15  # seconds

def crc16(data):
    '''Takes a bytes object and calcuates the CRC-16/CCITT-FALSE.'''
    # Modifed from a stackoverflow answer at https://stackoverflow.com/a/55850496/7969814
    crc = 0xFFFF
    for i in range(len(data)):
        crc ^= data[i] << 8
        for j in range(0,8):
            if (crc & 0x8000) > 0:
                crc =(crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF


def append_crc(data_packet : (bytes, bytearray)):
    '''Appends the 16 bit CRC to the end of the datapacket.'''
    crc = crc16(data_packet)
    data_packet += bytes([crc >> 8])  # high byte
    data_packet += bytes([crc & 0xff])  # low byte
    return bytes(data_packet)


print('starting')
sleep_time = SAMPLE_INTERVAL
time.sleep(NODE_ID * random.random() + 1)
x = 0

while True:
    data = [NODE_ID, NODE_ID, x % 65536, 0x0000, 0x00, 0x00,
            0x01, bme680.temperature + 275, 0x02, bme680.gas,
            0x03, bme680.humidity, 0x04, bme680.pressure / 100, 0xff, 0.0,
            0xff, 0.0, 0xff, 0.0, 0xff, 0.0, 0xff, 0.0, 0xff, 0.0,
            ]
    packed_data = struct.pack(radio_data_format, *data)
    data_packet = append_crc(packed_data)
    rfm69.send(data_packet)
    time.sleep(NODE_ID / 10 + random.random() * 0.1)
    rfm69.send(data_packet)
    x += 1
    sleep_time = SAMPLE_INTERVAL + SAMPLE_INTERVAL / 20 * (random.random() - 0.5)
    time.sleep(sleep_time)
