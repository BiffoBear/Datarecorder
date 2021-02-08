#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import pathlib
import logging
import queue
from collections import deque
import sqlalchemy
import RPi.GPIO as rpigpio 
from tests import conftest
from radiohelper import radiohelper
from datarecorder import main, _dataprocessing, _oleddisplay
import database
from __config__ import FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL


class TestLoggingSetup:

    def test_log_file_exists_and_is_written_to(self):
        logging_file = pathlib.Path('/tmp/datarecorder.log')
        try:
            logging_file.unlink()
        except FileNotFoundError:
            pass
        main.initialize_logging(FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL)
        logger = logging.getLogger(__name__)
        logger.warning('test logging')
        assert logging_file.is_file()
        with open('/tmp/datarecorder.log') as f:
            assert "WARNING : test logging" in f.read()


class TestMainLoggingCalls:

    @pytest.mark.skip(reason="Don't know how to test this.")
    def test_rfm69callback(self):
        pass  # Not sure how to test this.
        # mock_irq = Mock()
        # with self.assertLogs(level='DEBUG') as lm:
        #     main.rfm69_callback(mock_irq)
        # self.assertIn('rfm69_callback called', lm.output[0])


    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_initialize_gpio_interrupt(self, mocker, caplog):
        _1 = mocker.patch.object(rpigpio, "add_event_callback", autospec=True)
        _2 = mocker.patch.object(rpigpio, "add_event_detect", autospec=True)
        _3 = mocker.patch.object(rpigpio, "remove_event_detect", autospec=True)
        _4 = mocker.patch.object(rpigpio, "setup", autospec=True)
        with caplog.at_level(logging.DEBUG):
            main.initialize_gpio_interrupt("dummy gpio_pin")
        assert "DEBUG: initialize_gpio_interrupt called" in caplog.text

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_initialize_rfm69(self, mocker):
        mock_rfm69 = mocker.patch.object(adafruit_rfm69, "RFM69", autospec=True)
        mock_rfm69.side_effect = [Mock(), Mock(), RuntimeError]
        with caplog.at_level(logging.DEBUG):
            main.initialize_rfm69()
        assert "initialize_rfm69 called" in caplog.text
        with caplog.at_level(logging.INFO):
            main.initialize_rfm69()
        assert "RFM69 radio initialized successfully" in caplog.text
        with caplog.at_level(logging.CRITICAL):
            with self.assertRaises(RuntimeError):
                main.initialize_rfm69()
        assert "RFM69 radio failed to initialize with RuntimeError" in caplog.text

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_initialize_database(self, mocker):
        _ = mocker.patch.object(database.database, "initialize_database", autospec=True)
        with self.assertLogs(level='DEBUG') as lm:
            main.initialize_database('dummy URL')
        self.assertIn('initialize_database called', lm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_initialize_processing_thread(self, mocker):
        _ = mocker.patch.object(datarecorder._dataprocessing, "init_data_processing_thread", autospec=True)
        with self.assertLogs(level='DEBUG') as lm:
            main.initialize_processing_thread()
        self.assertIn('initialize_processing_thread called', lm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_start_up(self, mocker):
        _1 = mocker.patch.object(datarecorder.main, "initialize_gpio_interrupt", autospec=True)
        _2 = mocker.patch.object(datarecorder.main, "initialize_processing_thread", autospec=True)
        _3 = mocker.patch.object(datarecorder.main, "initialize_database", autospec=True)
        _4 = mocker.patch.object(datarecorder.main, "initialize_logging", autospec=True)
        _5 = mocker.patch.object(datarecorder._oleddisplay, "init_display_thread", autospec=True)
        mock_rfm = mocker.patch.object(datarecorder.main, "initialize_rfm69", autospec=True)
        mock_rfm.return_value = Mock()
        with self.assertLogs(level='DEBUG') as lm:
            main.start_up()
        self.assertIn('start_up called', lm.output[0])
        with self.assertLogs(level='CRITICAL') as lm:
            main.start_up()
        self.assertIn('Listening for radio data…', lm.output[-1])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_shutdown(self, mocker):
        _1 = mocker.patch.object(rpigpio, "remove_event_detect", autospec=True)
        _2 = mocker.patch.object(datarecorder._dataprocessing, "radio_q.join", autospec=True)
        _3 = mocker.patch.object(datarecorder._oleddisplay, "shut_down", autospec=True)
        with self.assertLogs(level='INFO') as lm:
            main.shut_down(0)
        self.assertIn('shut_down_called', lm.output[0])


class TestDatabase:

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_write_sensor_reading_to_db(self):
        conftest.initialize_database()
        test_time = conftest.global_test_time
        test_data = {'timestamp': test_time, 'sensor_readings': [(0x01, 1.2345), (0x02, 2.3456)]}
        with self.assertLogs() as cm:
            database.database.write_sensor_reading_to_db(test_data)
        self.assertIn('write_sensor_reading_to_db called', cm.output[0])
        database.database.engine.dispose()

    @pytest.mark.skip(reason="Cant't make caplog work.")
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


class TestDataProcessing:

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_unpack_data_packet(self, mocker):
        _ = mocker.patch.object(struct, "unpack", autospec=True)
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.unpack_data_packet(radiohelper.RADIO_DATA_FORMAT,
                                               {'timestamp': conftest.global_test_time,
                                                'radio_data': conftest.rx_data_CRC_good,
                                                })
        self.assertIn('unpack_data_packet called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_expand_radio_data_into_dict(self):
        test_data = {'timestamp': conftest.global_test_time,
                     'radio_data': conftest.dummy_data}
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.expand_radio_data_into_dict(test_data)
        self.assertIn('expand_radio_data_into_dict called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_packet_missing_or_duplicate(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1011}
        _dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x1010, 'timestamp': None}}
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIn('check_for_duplicate_packet called', cm.output[0])
        self.assertIn('Rx from node 0x01, packet serial 0x1011', cm.output[-2])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_packet_missing_or_duplicate_logs_a_warning_for_a_missing_packet(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1012}
        _dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x0101, 'timestamp': None}}
        with self.assertLogs(level='WARNING') as cm:
            _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIn('Data packet missing from node 0x01', cm.output[-2])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_packet_missing_or_duplicate_logs_first_data_from_node(self):
        test_data = {'node_id': 0x01, 'pkt_serial': 0x1010}
        _dataprocessing.last_packet_info = {0x02: {'pkt_serial': 0xffff, 'timestamp': None}}
        with self.assertLogs(level='INFO') as cm:
            _dataprocessing.packet_missing_or_duplicate(test_data)
        self.assertIn('First data packet from node 0x01', cm.output[-2])
        self.assertIn('Rx from node 0x01, packet serial 0x1010', cm.output[-1])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_process_radio_data(self, mocker):
        mock_packet_missing_or_duplicate = mocker.patch.object(datarecorder._dataprocessing, "packet_missing_or_duplicate", autospec=True)
        mock_expand_radio_data_into_dict = mocker.patch.object(datarecorder._dataprocessing, "expand_radio_data_into_dict", autospec=True)
        mock_unpack_data_packet = mocker.patch.object(datarecorder._dataprocessing, "unpack_data_packet", autospec=True)
        mock_radio_q = mocker.patch.object(datarecorder._dataprocessing, "radio_q", autospec=True)
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

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_init_data_processing_thread(self, mocker):
        mock_thread = mocker.patch.object(threading, "Thread", autospec=True)
        mock_thread.return_value = Mock()
        with self.assertLogs(level='DEBUG') as cm:
            _dataprocessing.init_data_processing_thread()
        self.assertIn('init_data_processing_thread called', cm.output[0])


class TestOledDisplay:

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_initialize_i2c(self, mocker):
        _ = mocker.patch.object(busio, "I2C", autospec=True)
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.initialize_i2c()
        self.assertIn('initialize_i2c called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_initialize_oled(self, mocker):
        mock_ssd1306 = mocker.patch.object(adafruit_ssd1306, "SSD1306_I2C")
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

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_setup_hardware_oled(self, mocker):
        _1 = mocker.patch.object(datarecorder._oleddisplay, "initialize_oled", autospec=True)
        _2 = mocker.patch.object(datarecorder._oleddisplay, "initialize_i2c", autospec=True)
        _3 = mocker.patch.object(digitalio, "DigitalInOut", autospec=True)
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.setup_hardware_oled()
        self.assertIn('setup_hardware_oled called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_setup_display_dict(self, mocker):
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.setup_display_dict()
        self.assertIn('setup_display_dict called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_clear_display(self, mocker):
        mock_image_draw = mocker.patch.object(PIL, "ImageDraw", autospec=True)
        dummy_display = {'draw': mock_image_draw()}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.clear_display(dummy_display)
        self.assertIn('_oleddisplay:clear_display called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_write_text_to_display(self, mocker):
        mock_image_draw = mocker.patch.object(PIL, "ImageDraw", autospec=True)
        dummy_display = {'draw': mock_image_draw(), 'font': None}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.write_text_to_display(display=dummy_display, coords=(0, 0), text='')
        self.assertIn('write_text_to_display called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_show_display(self, mocker):
        mock_image_draw = mocker.patch.object(PIL, "ImageDraw", autospec=True)
        dummy_display = {'draw': mock_image_draw(), 'oled': Mock(), 'image': Mock()}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.show_display(dummy_display)
        self.assertIn('show_display called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_add_screen_line(self):
        dummy_display = {'lines': deque([])}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.add_screen_line(display=dummy_display, text='')
        self.assertIn('add_screen_line called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_draw_lines(self, mocker):
        _1 = mocker.patch.object(datarecorder._oleddisplay, "clear_display", autospec=True)
        _2 = mocker.patch.object(datarecorder._oleddisplay, "write_text_to_display", autospec=True)
        _3 = mocker.patch.object(datarecorder._oleddisplay, "show_display", autospec=True)
        dummy_display = {'lines': deque([])}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.draw_lines(display=dummy_display)
        self.assertIn('draw_lines called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_display_message_from_queue(self, mocker):
        _1 = mocker.patch.object(datarecorder._oleddisplay, "clear_display")
        mock_message_queue = mocker.patch.object(datarecorder._oleddisplay, "message_queue")
        mock_message_queue.get.side_effect = [None, queue.Empty]
        dummy_display = {'oled': Mock(), 'lines': deque([])}
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.display_message_from_queue(display=dummy_display)
        self.assertIn('display_message_from_queue called', cm.output[0])
        with self.assertLogs(level='ERROR') as cm:
            _oleddisplay.display_message_from_queue(display=dummy_display)
        self.assertIn('Display thread called with empty queue', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_write_message_to_queue(self):
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.write_message_to_queue(message_text='dummy message')
        self.assertIn('write_message_to_queue called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_shut_down(self, mocker):
        _1 = mocker.patch.object(datarecorder._oleddisplay, "show_display", autospec=True)
        _2 = mocker.patch.object(datarecorder._oleddisplay, "clear_display", autospec=True)
        _3 = mocker.patch.object(datarecorder._oleddisplay, "message_queue", autospec=True)
        with self.assertLogs(level='INFO') as cm:
            _oleddisplay.shut_down()
        self.assertIn('shut_down called', cm.output[0])

    @pytest.mark.skip(reason="Cant't make caplog work.")
    def test_init_display_thread(self, mocker):
        _1 = mocker.patch.object(datarecorder._oleddisplay, "setup_display_dict", autospec=True)
        mock_thread = mocker.patch.object(threading, "Thread", autospec=True)
        mock_thread.return_value = Mock()
        with self.assertLogs(level='DEBUG') as cm:
            _oleddisplay.init_display_thread()
        self.assertIn('init_display_thread called', cm.output[0])
