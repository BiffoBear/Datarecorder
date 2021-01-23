import struct
import time
import random
import board
import digitalio
import adafruit_rfm69 as rfm_69

ENCRYPTION_KEY = b'\x16UT\xb6\x92FHaE\xb5B\xde\xbclYs'
DATA_FORMAT = '>BBHHBBBfBfBfBfBfBfBfBfBfBf'


def _extract_data_from_dict(raw_dicts):
    """Takes sensor id and values from a dict."""
    list_of_lists = [[item['id'], float(item['value'])] for item in raw_dicts]
    return list_of_lists


def _pad_data(extracted_data):
    """Extends a list to contain ten items."""
    for x in range(10 - len(extracted_data)):
        extracted_data.append([0xff, 0.0])
    return extracted_data


def _flatten_list(list_of_lists):
    """Makes a flat list out of a list of lists."""
    flat_list = [item for elem in list_of_lists for item in elem]
    return flat_list


def _crc16(data):
    """Takes a bytes object and calculates the CRC-16/CCITT-FALSE."""
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


def _append_crc(data_packet):
    """Appends the 16 bit CRC to the end of the datapacket."""
    crc = _crc16(data_packet)
    data_packet += bytes([crc >> 8])  # high byte
    data_packet += bytes([crc & 0xff])  # low byte
    return bytes(data_packet)


class Radio:
    """Creates an instance of an RFM69 radio and provides methods to repeatedly
    send data via the radio."""

    def __init__(self, *, cs_pin=None, reset_pin=None, led_pin=None,
                 node_id=None, send_period=None):
        self._cs_pin = digitalio.DigitalInOut(cs_pin)
        self._reset_pin = digitalio.DigitalInOut(reset_pin)
        self._rfm69 = rfm_69.RFM69(board.SPI(), self._cs_pin, self._reset_pin, 433.0)
        self._rfm69.encryption_key = ENCRYPTION_KEY
        self._node_id = node_id
        self._send_period = send_period  # in seconds
        self._status_led = digitalio.DigitalInOut(led_pin)
        self._status_led.direction = digitalio.Direction.OUTPUT
        self._status_led.value = False
        self._packet_id = 0
        self._timer = None

    def _led_on(self):
        self._status_led.value = True

    def _led_off(self):
        self._status_led.value = False

    def _increment_counter_with_wrap(self):
        """Increments a value and wraps to 0 when a maximum value is reached."""
        self._packet_id += 1
        self._packet_id %= 0x10000

    def _prepare_data(self, data):
        """Packs the list of data into the radio data format."""
        extracted_data = _extract_data_from_dict(data)
        padded_data = _pad_data(extracted_data)
        flat_data = _flatten_list(padded_data)
        data_packet = [self._node_id, self._node_id, self._packet_id % 65536,
                       0x0000, 0x00, 0x00]
        data_packet.extend(flat_data)
        packed_data = struct.pack(DATA_FORMAT, *data_packet)
        prepped_data = _append_crc(packed_data)
        return prepped_data

    def _send_cycle(self, packet):
        self._led_on()
        self._rfm69.send(packet)
        self._led_off()

    def send_data(self, sensor_data):
        """Sends sensor data."""
        data_packet = self._prepare_data(sensor_data)
        self._send_cycle(data_packet)
        time.sleep(self._node_id / 10 + random.random() * 0.1)
        self._send_cycle(data_packet)
        print(f'Data packet {self._packet_id:02x} sent from node {self._node_id:02x}')
        self._increment_counter_with_wrap()

    def timer_reset(self):
        self._timer = time.monotonic()

    @property
    def timer_expired(self):
        return time.monotonic() > self._timer + self._send_period

    @property
    def timer_remaining(self):
        _remaining_time = self._timer + self._send_period - time.monotonic()
        if _remaining_time < 0:
            return 0
        return _remaining_time

    def wait_for_timer(self):
        while not self.timer_expired:
            time.sleep(0.1)

    def initial_sleep(self):
        sleep_duration = self._node_id % 0xf0 * random.random() + 1
        print(f'Starting inital sleep of {sleep_duration} seconds...')
        time.sleep(sleep_duration)
