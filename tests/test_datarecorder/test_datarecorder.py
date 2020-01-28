#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 20:12:30 2019

@author: pi
"""
from unittest import TestCase
from unittest.mock import Mock, patch, call
# noinspection PyPackageRequirements
import board
# noinspection PyPep8Naming
import RPi.GPIO as rpigpio
# noinspection PyProtectedMember
from datarecorder import main, _dataprocessing
from __config__ import RFM69_INTERRUPT_PIN, DB_URL, FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL
from radiohelper.radiohelper import RFM69_ENCRYPTION_KEY


class TestInterruptSetup(TestCase):

    def test_interrupt_pin_is_24(self):
        self.assertEqual(RFM69_INTERRUPT_PIN, 24)

    def test_gpio_setmode_called_with_correct_args(self):
        with patch('RPi.GPIO.setmode') as mock_gpio_setmode:
            main.initialize_gpio_interrupt(RFM69_INTERRUPT_PIN)
        mock_gpio_setmode.assert_called_with(rpigpio.BCM)

    def test_gpio_setup_called_with_correct_args(self):
        with patch('RPi.GPIO.setup') as mock_gpio_setup:
            main.initialize_gpio_interrupt(RFM69_INTERRUPT_PIN)
        mock_gpio_setup.assert_called_with(RFM69_INTERRUPT_PIN, rpigpio.IN, pull_up_down=rpigpio.PUD_DOWN)

    def test_gpio_event_setup_called_with_correct_args(self):
        with patch('RPi.GPIO.add_event_callback'):
            with patch('RPi.GPIO.add_event_detect') as mock_add_event_detect:
                main.initialize_gpio_interrupt(RFM69_INTERRUPT_PIN)
        mock_add_event_detect.assert_called_with(RFM69_INTERRUPT_PIN, rpigpio.RISING)

    def test_gpio_event_callback_called_with_correct_args(self):
        with patch('RPi.GPIO.add_event_callback') as mock_add_event_callback:
            main.initialize_gpio_interrupt(RFM69_INTERRUPT_PIN)
        mock_add_event_callback.assert_called_with(RFM69_INTERRUPT_PIN, main.rfm69_callback)


class TestRadioSetup(TestCase):

    def test_correct_gpio_pins_are_set_for_radio(self):
        with patch('adafruit_rfm69.RFM69'):
            with patch('digitalio.DigitalInOut') as mock_digi_io:
                main.initialize_rfm69()
        mock_digi_io.assert_has_calls([call(board.CE1), call(board.D25)])

    def test_spi_bus_is_set_to_correct_gpio_pins(self):
        with patch('adafruit_rfm69.RFM69'):
            with patch('busio.SPI') as mock_spi:
                main.initialize_rfm69()
        mock_spi.assert_called_once_with(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    @patch('busio.SPI')
    @patch('digitalio.DigitalInOut')
    @patch('adafruit_rfm69.RFM69')
    def test_radio_initialization(self, mock_rfm69, mock_digitalinout, mock_spi):
        mock_digitalinout.side_effect = ['cs', 'reset']
        mock_spi.return_value = 'spi'
        returned_radio = mock_rfm69.return_value = Mock()
        main.initialize_rfm69()
        mock_rfm69.assert_called_once_with('spi', 'cs', 'reset', 433)
        self.assertEqual(RFM69_ENCRYPTION_KEY, returned_radio.encryption_key)

    def test_rfm69_fails_to_initialize_logged_as_critical_and_raised(self):
        with patch('adafruit_rfm69.RFM69') as mock_rfm69:
            mock_rfm69.side_effect = RuntimeError
            with self.assertRaises(RuntimeError):
                main.initialize_rfm69()


class TestInitializeDataBase(TestCase):

    def test_database_initialize_database_is_called(self):
        with patch('database.database_setup.initialize_database') as mock_db_init:
            main.initialize_database(DB_URL)
        mock_db_init.assert_called_once_with(DB_URL)


class TestIrqCallbackFunc(TestCase):

    def test_payload_not_ready_does_not_write_to_queue(self):
        main.radio = Mock()
        _dataprocessing.radio_q = Mock()
        main.radio.payload_ready = False
        main.rfm69_callback(None)
        main.radio.receive.assert_not_called()
        _dataprocessing.radio_q.put.assert_not_called()

    def test_empty_buffer_does_not_write_to_queue(self):
        main.radio = Mock()
        _dataprocessing.radio_q = Mock()
        main.radio.payload_ready = True
        main.radio.receive.return_value = None
        main.rfm69_callback(None)
        main.radio.receive.assert_called()
        _dataprocessing.radio_q.put.assert_not_called()

    def test_data_in_buffer_written_to_queue(self):
        main.radio = Mock()
        _dataprocessing.radio_q = Mock()
        main.radio.payload_ready = True
        main.radio.receive.return_value = 'Hello World!'
        main.rfm69_callback(None)
        main.radio.receive.assert_called()
        _dataprocessing.radio_q.put.assert_called_once_with('Hello World!')


@patch('datarecorder._oleddisplay.init_display_thread')
@patch('datarecorder.main.initialize_gpio_interrupt')
@patch('datarecorder.main.initialize_rfm69')
@patch('datarecorder.main.initialize_processing_thread')
@patch('datarecorder.main.initialize_database')
@patch('datarecorder.main.initialize_logging')
class TestStartUpFunc(TestCase):

    def test_start_up_calls_all_init_functions(self, mock_init_logging,
                                               mock_init_db,
                                               mock_init_thread,
                                               mock_init_rfm69,
                                               mock_init_irq,
                                               mock_init_display_thread,
                                               ):
        main.start_up(db_url='Fake_URL', pi_irq_pin=6)
        mock_init_logging.assert_called_once()
        mock_init_logging.assert_called_once_with(FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL)
        mock_init_db.assert_called_once_with('Fake_URL')
        mock_init_thread.assert_called_once()
        mock_init_rfm69.assert_called_once()
        mock_init_irq.assert_called_once_with(6)
        mock_init_display_thread.assert_called_once()
