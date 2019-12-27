#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 20:12:30 2019

@author: pi
"""

from unittest import TestCase, skip
from unittest.mock import Mock, patch
import board
import hardware


@patch('adafruit_rfm69.RFM69')
@patch('busio.SPI')
class TestRadioSetup(TestCase):

    def test_radio_class_instantiation(self, mock_spi, mock_rfm69):
        with self.assertLogs() as cm:
            x = hardware.Radio()
        self.assertIn('RFM69 radio initialized successfully', cm.output[0])
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
        self.assertIn('RFM69 radio failed to initialize with RuntimeError', cm.output[0])

    def test_get_buffer_returns_correct_values_and_increments_counters(self, _x, _y):
        radio = hardware.Radio()
        radio._rfm69 = Mock()
        radio._rfm69.receive.return_value = None
        with self.assertLogs() as cm:
            y = radio.get_buffer()
        self.assertIn('Radio.get_buffer called', cm.output[0])
        self.assertEqual(y, None)
        self.assertEqual(radio._buffer_read_count, 1)
        self.assertEqual(radio._packets_returned, 0)
        radio._rfm69.receive.return_value = 'data'
        y = radio.get_buffer()
        self.assertEqual(y, 'data')
        self.assertEqual(radio._buffer_read_count, 2)
        self.assertEqual(radio._packets_returned, 1)
        
    # def test_radio_receive_failure_logs_a_critical_error(self, _x, _y):
    #     radio = hardware.Radio()
    #     radio._rfm69 = Mock()
    #     radio._rfm69.receive.side_effect = RuntimeError
    #     with self.assertLogs(level='CRITICAL') as cm:
    #         with self.assertRaises(RuntimeError):
    #             radio.get_buffer()
    #     self.assertIn('Unable to read RFM69 buffer', cm.output[-1])

    def test_get_stats_returns_correct_values(self, _x, _y):
        radio = hardware.Radio()
        radio._rfm69 = Mock()
        radio._rfm69.receive.return_value = None
        radio.get_buffer()
        radio._rfm69.receive.return_value = 'data'
        radio.get_buffer()
        self.assertEqual(radio.get_stats(), {'reads': radio._buffer_read_count, 'packets': radio._packets_returned})

    def test_logging_for_get_stats(self, _x, _y):
        # Keeps crashing Spyder unittest module, so I gave up.
        pass

@skip
class TestPiDisplay(TestCase):

    def test_initialization_of_display(self):
        display = hardware.Display()
        self.assertIsInstance(display, hardware.Display)
        self.assertEqual(display._reset_pin, board.D4)

    # @patch('busio.I2C')
    # def test_i2c_bus_initiated_with_correct_settings(self, mock_i2c):
    #     display = hardware.Display()
    #     mock_i2c.assert_called_once_with(board.SCL, board.SDA)
    #
    # @patch('adafruit_ssd1306.SSD1306_I2C')
    # def test_display_initiated_with_correct_settings(self, mock_ssd1306):
    #     display = hardware.Display()
    #     mock_ssd1306.assert_called_once_with(128, 32, display._i2c, reset=display._reset_pin)





