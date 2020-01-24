#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase, skip
from unittest.mock import Mock, patch
import pathlib
import logging
import sqlalchemy
from tests import unittest_helper
from radiohelper import radiohelper
from datarecorder import main, database, dataprocessing
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


class TestDataProcessing(TestCase):

    @patch('struct.unpack')
    def test_unpack_data_packet(self, _1):
        with self.assertLogs(level='DEBUG') as cm:
            dataprocessing.unpack_data_packet(radiohelper.RADIO_DATA_FORMAT,
                                              {'timestamp': unittest_helper.global_test_time,
                                               'radio_data': unittest_helper.rx_data_CRC_good
                                               })
        self.assertIn('unpack_data_packet called', cm.output[0])

    def test_expand_radio_data_into_dict(self):
        test_data = {'timestamp': unittest_helper.global_test_time,
                     'radio_data': unittest_helper.dummy_data}
        with self.assertLogs(level='DEBUG') as cm:
            dataprocessing.expand_radio_data_into_dict(test_data)
        self.assertIn('expand_radio_data_into_dict called', cm.output[0])

    def test_check_for_duplicate_or_missing_packet(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1011}
        dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x1010, 'timestamp': None}}
        with self.assertLogs(level='DEBUG') as cm:
            dataprocessing.check_for_duplicate_or_missing_packet(test_data)
        self.assertIn('check_for_duplicate_packet called', cm.output[0])
        self.assertIn('Rx from node 0x01, packet serial 0x1011', cm.output[-1])

    def test_check_for_duplicate_or_missing_packet_logs_a_warning_for_a_missing_packet(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1012}
        dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x0101, 'timestamp': None}}
        with self.assertLogs(level='WARNING') as cm:
            dataprocessing.check_for_duplicate_or_missing_packet(test_data)
        self.assertIn('Data packet missing from node 0x01', cm.output[-2])

    def test_check_for_duplicate_or_missing_packet_logs_first_data_from_node(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        dataprocessing.last_packet_info = {0x02: {'pkt_serial': 0xffff, 'timestamp': None}}
        with self.assertLogs(level='INFO') as cm:
            dataprocessing.check_for_duplicate_or_missing_packet(test_data)
        self.assertIn('First data packet from node 0x01', cm.output[-2])
        self.assertIn('Rx from node 0x01, packet serial 0x1010', cm.output[-1])

    @patch('datarecorder.dataprocessing.check_for_duplicate_or_missing_packet')
    @patch('datarecorder.dataprocessing.expand_radio_data_into_dict')
    @patch('datarecorder.dataprocessing.unpack_data_packet')
    @patch('datarecorder.dataprocessing.radio_q')
    def test_process_radio_data(self, mock_radio_q, mock_unpack_data_packet,
                                mock_expand_radio_data_into_dict, mock_check_for_duplicate_or_missing_packet,
                                ):
        mock_radio_q.get.return_value = None
        mock_unpack_data_packet.side_effect = ['Dummy data', ValueError]
        mock_expand_radio_data_into_dict.return_value = {'node': None, 'sensors': None}
        mock_check_for_duplicate_or_missing_packet.return_value = True
        with self.assertLogs(level='DEBUG') as cm:
            dataprocessing.process_radio_data()
        self.assertIn('process_radio_data called', cm.output[0])
        self.assertIn('Data packet = Dummy data', cm.output[1])
        with self.assertLogs(level='WARNING') as cm:
            dataprocessing.process_radio_data()
        self.assertIn('Bad data packet detected', cm.output[1])

    @patch('threading.Thread')
    def test_init_data_processing_thread(self, mock_thread):
        mock_thread.return_value = Mock()
        with self.assertLogs(level='DEBUG') as cm:
            dataprocessing.init_data_processing_thread()
        self.assertIn('init_data_processing_thread called', cm.output[0])