import struct
import time
import random
import board
import digitalio
import adafruit_rfm69

ENCRYPTION_KEY = b'\x16UT\xb6\x92FHaE\xb5B\xde\xbclYs'
DATA_FORMAT = '>BBHHBBBfBfBfBfBfBfBfBfBfBf'


class Radio:

    def __init__(self, *, cs_pin=None, reset_pin=None, led_pin=None, node_id=None, send_freq=None):
        self._rfm69 = adafruit_rfm69.RFM69(board.spi(), cs_pin, reset_pin, 433.0)
        self._rfm69.encryption_key = ENCRYPTION_KEY
        self._node_id = node_id
        self._send_freq = send_freq
        self._status_led = digitalio.DigitalInOut(led_pin)
        self._status_led.direction = digitalio.Direction.OUTPUT
        self._status_led.value = False
        self._packet_id = 0
        self._timer = None

    def _crc16(self, data):
        """Takes a bytes object and calcuates the CRC-16/CCITT-FALSE."""
        # Modified from a stackoverflow answer at https://stackoverflow.com/a/55850496/7969814
        crc = 0xFFFF
        for i in range(len(data)):
            crc ^= data[i] << 8
            for j in range(0, 8):
                if (crc & 0x8000) > 0:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
        return crc & 0xFFFF

    def _append_crc(self, data_packet):
        """Appends the 16 bit CRC to the end of the datapacket."""
        crc = self._crc16(data_packet)
        data_packet += bytes([crc >> 8])  # high byte
        data_packet += bytes([crc & 0xff])  # low byte
        return bytes(data_packet)

    def _prepare_data(self, raw_data):
        """Packs the list of data into the radio data format."""
        packed_data = struct.pack(DATA_FORMAT, *raw_data)
        prepped_data = self.append_crc(packed_data)
        return prepped_data

    def send(self, data):
        """Sends sensor data."""
        data_packet = self._prepare_data(data)
        self._status_led.value = True
        self._rfm69.send(data_packet)
        self._status_led.value = False
        time.sleep(self._node_id / 10 + random.random() * 0.1)
        self._status_led.value = True
        self._rfm69.send(data_packet)
        self._status_led.value = False
        self._packet_id += 1

    def timer_reset(self):
        self._timer = time.monotonic()

    @property
    def timer_expired(self):
        return time.monotonic() > self._timer + self._send_freq

    @property
    def timer_remaining(self):
        _remaining_time = self.timer + self._send_freq - time.monotonic()
        if _remaining_time < 0:
            return 0
        return _remaining_time

