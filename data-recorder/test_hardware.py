#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 20:12:30 2019

@author: pi
"""

from unittest import TestCase
from unittest.mock import Mock, patch
import board
import hardware


@patch('adafruit_rfm69.RFM69')
@patch('busio.SPI')  # A bug in busio seems to cause Spyder to crash
class TestRadioSetup(TestCase):

    def test_radio_class_instatiation(self, mock_spi, mock_rfm69):
        with self.assertLogs() as cm:
            x = hardware.Radio()
        self.assertEqual(cm.output, ['INFO:hardware:RFM69 radio initiated successfully'])
        self.assertIsInstance(x, hardware.Radio)

    def test_correct_gpio_pins_are_set_for_radio(self, _x, _y):
        x = hardware.Radio()
        self.assertEqual(x._cs._pin, board.CE1)
        self.assertEqual(x._reset._pin, board.D25)

    def test_spi_bus_is_set_to_correct_gpio_pins(self, mock_spi, _):
        hardware.Radio()
        mock_spi.assert_called_once_with(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    def test_rfm69_instantiated_with_correct_settings(self, _, mock_rfm69):
        x = hardware.Radio()
        mock_rfm69.assert_called_with(x._spi, x._cs, x._reset, 433.0)

    def test_rfm69_fails_to_initialize_logged_as_critical_and_raised(self, _, mock_rfm69):
        mock_rfm69.side_effect = RuntimeError
        with self.assertLogs() as cm:
            with self.assertRaises(RuntimeError):
                hardware.Radio()
        self.assertEqual(cm.output, ['CRITICAL:hardware:RFM69 radio failed to initialize'])

    def test_get_buffer_returns_correct_values_and_increments_counters(self, _x, _y):
        radio = hardware.Radio()
        radio._rfm69 = Mock()
        radio._rfm69.receive.return_value = None
        with self.assertLogs() as cm:
            y = radio.get_buffer()
        self.assertEqual(cm.output, ['DEBUG:hardware:Radio.get_buffer called'])
        self.assertEqual(y, None)
        self.assertEqual(radio._buffer_read_count, 1)
        self.assertEqual(radio._packets_returned, 0)
        radio._rfm69.receive.return_value = 'data'
        y = radio.get_buffer()
        self.assertEqual(y, 'data')
        self.assertEqual(radio._buffer_read_count, 2)
        self.assertEqual(radio._packets_returned, 1)

    def test_get_stats_returns_correct_values(self, _x, _y):
        radio = hardware.Radio()
        radio._rfm69 = Mock()
        radio._rfm69.receive.return_value = None
        radio.get_buffer()
        radio._rfm69.receive.return_value = 'data'
        radio.get_buffer()
        self.assertEqual(radio.get_stats(), {'reads': radio._buffer_read_count, 'packets': radio._packets_returned})

