# Write your code here :-)
import time
import random
import struct
import board
import busio
import digitalio
import adafruit_rfm69

NODE_ID = 0x01

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)
rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, 433.0)
rfm69.encryption_key = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
radio_data_format = '>BBHHBBBfBfBfBfBfBfBfBfBfBf'
max_packet_length = 58
sensor_count = radio_data_format.count('f')
sensor_offset = radio_data_format.find('Bf') - 1  # lists are zero indexed

dummy_data = [NODE_ID, NODE_ID, 0x0000, 0xf0f0, 0xaa, 0xbb,
              0x00, 0.1234, 0x01, 1.2345, 0x02, 2.3456, 0x03, 3.4567, 0x04, 4.5678,
              0x05, -5.6789, 0x06, 0.0, 0x07, 7891, 0x08, -999, 0xff, 0,
              ]

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
start_time = time.time()
end_time = start_time + 57600
#x = 0
for x in range(3600):
#while time.time() < end_time:
    z = x % 65536
    dummy_data[2] = z
    packed_data = struct.pack(radio_data_format, *dummy_data)
    data_packet = append_crc(packed_data)
    rfm69.send(data_packet)
    time.sleep(0.2)
    rfm69.send(data_packet)
    x += 1
    print(x)
    time.sleep(random.random())
print('{} packets sent'.format(x))
print('Time = {} seconds.'.format(time.time() - start_time))