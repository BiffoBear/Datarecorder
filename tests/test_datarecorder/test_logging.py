#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import Mock, patch
import pathlib
import logging
import queue
from collections import deque
import sqlalchemy
from tests import unittest_helper
from radiohelper import radiohelper
# noinspection PyProtectedMember
from datarecorder import main, _dataprocessing, _oleddisplay
import database
from __config__ import FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL


class TestLoggingSetup(TestCase):

    def test_log_file_exists_and_is_written_to(self):
        logging_file = pathlib.Path('/tmp/datarecorder.log')
        try:
            logging_file.unlink()
        except FileNotFoundError:
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
    def test_initialize_rfm69(self, mock_rfm69):
        mock_rfm69.side_effect = [Mock(), Mock(), RuntimeError]
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

    @patch('database.database.initialize_database')
    def test_initialize_database(self, _1):
        with self.assertLogs(level='DEBUG') as lm:
            main.initialize_database('dummy URL')
        self.assertIn('initialize_database called', lm.output[0])

    @patch('datarecorder._dataprocessing.init_data_processing_thread')
    def test_initialize_processing_thread(self, _1):
        with self.assertLogs(level='DEBUG') as lm:
            main.initialize_processing_thread()
        self.assertIn('initialize_processing_thread called', lm.output[0])

    @patch('datarecorder._oleddisplay.init_display_thread')
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
    @patch('datarecorder._dataprocessing.radio_q.join')
    @patch('datarecorder._oleddisplay.shut_down')
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
            database.database.write_sensor_reading_to_db(test_data)
        self.assertIn('write_sensor_reading_to_db called', cm.output[0])
        database.database.engine.dispose()

    def test_initialize_database(self):
        with self.assertLogs(level='DEBUG') as cm:
            database.database.initialize_database('sqlite://')
        self.assertIn('initialize_database called', cm.output[0])
        database.database.engine.dispose()
        with self.assertLogs(level='INFO') as cm:
            database.database.initialize_database('sqlite://')
        self.assertIn('Database initialized', cm.output[1])
        database.database.engine.dispose()
        with self.assertRaises(sqlalchemy.exc.ArgumentError):
            with self.assertLogs(level='CRITICAL') as cm:
                database.database.initialize_database('')
        self.assertIn('Database initialization failed:', cm.output[-1])
        database.database.engine.dispose()


class TestDataProcessing(TestCase):

    @patch('struct.unpack')
    def test_unpack_data_packet(self, _1):
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.unpack_data_packet(radiohelper.RADIO_DATA_FORMAT,
                                               {'timestamp': unittest_helper.global_test_time,
                                                'radio_data': unittest_helper.rx_data_CRC_good,
                                                })
        self.assertIn('unpack_data_packet called', cm.output[0])

    def test_expand_radio_data_into_dict(self):
        test_data = {'timestamp': unittest_helper.global_test_time,
                     'radio_data': unittest_helper.dummy_data}
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.expand_radio_data_into_dict(test_data)
        self.assertIn('expand_radio_data_into_dict called', cm.output[0])

    def test_packet_missing_or_duplicate(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1011}
        _dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x1010, 'timestamp': None}}
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIn('check_for_duplicate_packet called', cm.output[0])
        self.assertIn('Rx from node 0x01, packet serial 0x1011', cm.output[-2])

    def test_packet_missing_or_duplicate_logs_a_warning_for_a_missing_packet(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1012}
        _dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x0101, 'timestamp': None}}
        with self.assertLogs(level='WARNING') as cm:
            _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIn('Data packet missing from node 0x01', cm.output[-2])

    def test_packet_missing_or_duplicate_logs_first_data_from_node(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        _dataprocessing.last_packet_info = {0x02: {'pkt_serial': 0xffff, 'timestamp': None}}
        with self.assertLogs(level='INFO') as cm:
            _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIn('First data packet from node 0x01', cm.output[-2])
        self.assertIn('Rx from node 0x01, packet serial 0x1010', cm.output[-1])

    @patch('datarecorder._dataprocessing.packet_missing_or_duplicate')
    @patch('datarecorder._dataprocessing.expand_radio_data_into_dict')
    @patch('datarecorder._dataprocessing.unpack_data_packet')
    @patch('datarecorder._dataprocessing.radio_q')
    def test_process_radio_data(self, mock_radio_q, mock_unpack_data_packet,
                                mock_expand_radio_data_into_dict, mock_packet_missing_or_duplicate,
                                ):
        mock_radio_q.get.return_value = None
        mock_unpack_data_packet.side_effect = ['Dummy data', ValueError]
        mock_expand_radio_data_into_dict.return_value = {'node': None, 'sensors': None}
        mock_packet_missing_or_duplicate.return_value = True
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.process_radio_data()
        self.assertIn('process_radio_data called', cm.output[0])
        self.assertIn('Data packet = Dummy data', cm.output[1])
        with self.assertLogs(level='WARNING') as cm:
            _dataprocessing.process_radio_data()
        self.assertIn('Bad data packet detected', cm.output[1])

    @patch('threading.Thread')
    def test_init_data_processing_thread(self, mock_thread):
        mock_thread.return_value = Mock()
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.init_data_processing_thread()
        self.assertIn('init_data_processing_thread called', cm.output[0])


class TestOledDisplay(TestCase):

    @patch('busio.I2C')
    def test_initialize_i2c(self, _1):
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.initialize_i2c()
        self.assertIn('initialize_i2c called', cm.output[0])

    @patch('adafruit_ssd1306.SSD1306_I2C')
    def test_initialize_oled(self, mock_ssd1306):
        mock_ssd1306.side_effect = [None, ValueError, AttributeError]
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.initialize_oled(None, None)
        self.assertIn('initialize_oled called', cm.output[0])
        with self.assertLogs(level='ERROR') as cm:
            _oleddisplay.initialize_oled(None, None)
        self.assertIn('OLED display failed to initialize. Check that wiring is correct', cm.output[0])
        with self.assertLogs(level='ERROR') as cm:
            _oleddisplay.initialize_oled(None, None)
        self.assertIn('OLED display failed to initialize. No I2C bus found', cm.output[0])

    @patch('datarecorder._oleddisplay.initialize_oled')
    @patch('digitalio.DigitalInOut')
    @patch('datarecorder._oleddisplay.initialize_i2c')
    def test_setup_hardware_oled(self, _1, _2, _3):
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.setup_hardware_oled()
        self.assertIn('setup_hardware_oled called', cm.output[0])

    def test_setup_display_dict(self):
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.setup_display_dict()
        self.assertIn('setup_display_dict called', cm.output[0])

    @patch('PIL.ImageDraw')
    def test_clear_display(self, mock_image_draw):
        dummy_display = {'draw': mock_image_draw()}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.clear_display(dummy_display)
        self.assertIn('_oleddisplay:clear_display called', cm.output[0])

    @patch('PIL.ImageDraw')
    def test_write_text_to_display(self, mock_image_draw):
        dummy_display = {'draw': mock_image_draw(), 'font': None}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.write_text_to_display(display=dummy_display, coords=(0, 0), text='')
        self.assertIn('write_text_to_display called', cm.output[0])

    @patch('PIL.ImageDraw')
    def test_show_display(self, mock_image_draw):
        dummy_display = {'draw': mock_image_draw(), 'oled': Mock(), 'image': Mock()}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.show_display(dummy_display)
        self.assertIn('show_display called', cm.output[0])

    def test_add_screen_line(self):
        dummy_display = {'lines': deque([])}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.add_screen_line(display=dummy_display, text='')
        self.assertIn('add_screen_line called', cm.output[0])

    @patch('datarecorder._oleddisplay.clear_display')
    @patch('datarecorder._oleddisplay.write_text_to_display')
    @patch('datarecorder._oleddisplay.show_display')
    def test_draw_lines(self, _1, _2, _3):
        dummy_display = {'lines': deque([])}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.draw_lines(display=dummy_display)
        self.assertIn('draw_lines called', cm.output[0])

    @patch('datarecorder._oleddisplay.message_queue')
    @patch('datarecorder._oleddisplay.clear_display')
    def test_display_message_from_queue(self, _1, mock_message_queue):
        mock_message_queue.get.side_effect = [None, queue.Empty]
        dummy_display = {'oled': Mock(), 'lines': deque([])}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.display_message_from_queue(display=dummy_display)
        self.assertIn('display_message_from_queue called', cm.output[0])
        with self.assertLogs(level='ERROR') as cm:
            _oleddisplay.display_message_from_queue(display=dummy_display)
        self.assertIn('Display thread called with empty queue', cm.output[0])

    def test_write_message_to_queue(self):
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.write_message_to_queue(message_text='dummy message')
        self.assertIn('write_message_to_queue called', cm.output[0])

    @patch('datarecorder._oleddisplay.show_display')
    @patch('datarecorder._oleddisplay.clear_display')
    @patch('datarecorder._oleddisplay.message_queue')
    def test_shut_down(self, _1, _2, _3):
        with self.assertLogs(level='INFO') as cm:
            _oleddisplay.shut_down()
        self.assertIn('shut_down called', cm.output[0])

    @patch('threading.Thread')
    @patch('datarecorder._oleddisplay.setup_display_dict')
    def test_init_display_thread(self, _1, mock_thread):
        mock_thread.return_value = Mock()
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.init_display_thread()
        self.assertIn('init_display_thread called', cm.output[0])
