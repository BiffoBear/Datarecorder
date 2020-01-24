#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase, skip
from unittest.mock import Mock, patch
import pathlib
import logging
import sqlalchemy
from tests import unittest_helper
from datarecorder import main, database
from __config__ import FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL


class TestLoggingSetup(TestCase):

    def test_log_file_exists_and_is_written_to(self):
        logging_file = pathlib.Path('/tmp/datarecorder.log')
        try:
            logging_file.unlink()
        except:
            pass
        main.initialize_logging(FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL)
        logger = logging.getLogger(__name__)
        logger.warning('test logging')
        self.assertTrue(logging_file.is_file())
        with open('/tmp/datarecorder.log') as f:
            self.assertIn('test logging', f.read())


class TestMainLoggingCalls(TestCase):

    def test_rfm69callback(self):
        pass  # Not sure how to test this.
        # mock_irq = Mock()
        # with self.assertLogs(level='DEBUG') as lm:
        #     main.rfm69_callback(mock_irq)
        # self.assertIn('rfm69_callback called', lm.output[0])

    @patch('RPi.GPIO.add_event_callback')
    @patch('RPi.GPIO.add_event_detect')
    @patch('RPi.GPIO.remove_event_detect')
    @patch('RPi.GPIO.setup')
    def test_initialize_gpio_interrupt(self, _1, _2, _3, _4):
        with self.assertLogs(level='DEBUG') as lm:
            main.initialize_gpio_interrupt('dummy gpio_pin')
        self.assertIn('initialize_gpio_interrupt called', lm.output[0])

    @patch('adafruit_rfm69.RFM69')
    def test_initialize_rfm69(self, mock_RFM69):
        mock_RFM69.side_effect = [Mock(), Mock(), RuntimeError]
        with self.assertLogs(level='DEBUG') as lm:
            main.initialize_rfm69()
        self.assertIn('initialize_rfm69 called', lm.output[0])
        with self.assertLogs(level='INFO') as lm:
            main.initialize_rfm69()
        self.assertIn('RFM69 radio initialized successfully', lm.output[-1])
        with self.assertLogs(level='CRITICAL') as lm:
            with self.assertRaises(RuntimeError):
                main.initialize_rfm69()
        self.assertIn('RFM69 radio failed to initialize with RuntimeError', lm.output[-1])

    @patch('datarecorder.database.initialize_database')
    def test_initialize_database(self, _1):
        with self.assertLogs(level='DEBUG') as lm:
            main.initialize_database('dummy URL')
        self.assertIn('initialize_database called', lm.output[0])

    @patch('datarecorder.dataprocessing.init_data_processing_thread')
    def test_initialize_processing_thread(self, _1):
        with self.assertLogs(level='DEBUG') as lm:
            main.initialize_processing_thread()
        self.assertIn('initialize_processing_thread called', lm.output[0])

    @patch('datarecorder.oleddisplay.init_display_thread')
    @patch('datarecorder.main.initialize_gpio_interrupt')
    @patch('datarecorder.main.initialize_processing_thread')
    @patch('datarecorder.main.initialize_database')
    @patch('datarecorder.main.initialize_logging')
    @patch('datarecorder.main.initialize_rfm69')
    def test_start_up(self, mock_rfm, _2, _3, _4, _5, _6):
        mock_rfm.return_value = Mock()
        with self.assertLogs(level='DEBUG') as lm:
            main.start_up()
        self.assertIn('start_up called', lm.output[0])
        with self.assertLogs(level='CRITICAL') as lm:
            main.start_up()
        self.assertIn('Listening for radio data…', lm.output[-1])

    @patch('RPi.GPIO.remove_event_detect')
    @patch('datarecorder.dataprocessing.radio_q.join')
    @patch('datarecorder.oleddisplay.shutdown')
    def test_shutdown(self, _1, _2, _3):
        with self.assertLogs(level='INFO') as lm:
            main.shut_down(0)
        self.assertIn('shut_down_called', lm.output[0])


class TestDatabase(TestCase):

    def test_write_sensor_reading_to_db(self):
        unittest_helper.initialize_database()
        test_time = unittest_helper.global_test_time
        test_data = {'timestamp': test_time, 'sensor_readings': [(0x01, 1.2345), (0x02, 2.3456)]}
        with self.assertLogs() as cm:
            database.write_sensor_reading_to_db(test_data)
        self.assertIn('write_sensor_reading_to_db called', cm.output[0])
        database.engine.dispose()

    def test_initialize_database(self):
        with self.assertLogs(level='DEBUG') as cm:
            database.initialize_database('sqlite://')
        self.assertIn('initialize_database called', cm.output[0])
        database.engine.dispose()
        with self.assertLogs(level='INFO') as cm:
            database.initialize_database('sqlite://')
        self.assertIn('Database initialized', cm.output[1])
        database.engine.dispose()
        with self.assertRaises(sqlalchemy.exc.ArgumentError):
            with self.assertLogs(level='CRITICAL') as cm:
                database.initialize_database('')
        self.assertIn('Database initialization failed:', cm.output[-1])
        database.engine.dispose()

