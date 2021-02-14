#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import Mock
import pathlib
import logging
import queue
import sqlalchemy
import RPi.GPIO as rpigpio
import adafruit_rfm69
import adafruit_ssd1306
import database
from collections import deque
from tests import conftest
from helpers import radiohelper, display
from datarecorder import main, _dataprocessing 
from __config__ import FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL


class TestLoggingSetup:
    def test_log_file_exists_and_is_written_to(self):
        logging_file = pathlib.Path("/tmp/datarecorder.log")
        try:
            logging_file.unlink()
        except FileNotFoundError:
            pass
        main.initialize_logging(FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL)
        logger = logging.getLogger(__name__)
        logger.warning("test logging")
        assert logging_file.is_file()
        with open("/tmp/datarecorder.log") as f:
            assert "WARNING : test logging" in f.read()


class TestMainLoggingCalls:
    @pytest.mark.skip(reason="Don't know how to test this.")
    def test_rfm69callback(self):
        pass  # Not sure how to test this.
        # mock_irq = Mock()
        # with self.assertLogs(level='DEBUG') as lm:
        #     main.rfm69_callback(mock_irq)
        # self.assertIn('rfm69_callback called', lm.output[0])

    def test_initialize_rfm69(self, mocker, caplog):
        mock_rfm69 = mocker.patch.object(adafruit_rfm69, "RFM69", autospec=True)
        mock_rfm69.side_effect = [Mock(), RuntimeError]
        with caplog.at_level(logging.INFO, logger='Datarecorder.datarecorder.main'):
            main.initialize_rfm69()
        assert "RFM69 radio initialized successfully" in caplog.text
        with caplog.at_level(logging.CRITICAL, logger='Datarecorder.datarecorder.main'):
            with pytest.raises(RuntimeError) as error:
                main.initialize_rfm69()
        assert "RFM69 radio failed to initialize with RuntimeError" in caplog.text

    def test_start_up(self, mocker, caplog):
        _1 = mocker.patch.object(main, "initialize_gpio_interrupt", autospec=True)
        _2 = mocker.patch.object(main, "initialize_processing_thread", autospec=True)
        _3 = mocker.patch.object(main, "initialize_database", autospec=True)
        _4 = mocker.patch.object(main, "initialize_logging", autospec=True)
        # TODO: Implement logging in new display module
        _5 = mocker.patch.object(display, "init", autospec=True)
        mock_rfm = mocker.patch.object(main, "initialize_rfm69", autospec=True)
        mock_rfm.return_value = Mock()
        with caplog.at_level(logging.INFO, logger='Datarecorder.datarecorder.main'):
            main.start_up()
        assert "Listening for radio data…" in caplog.text

    def test_shutdown(self, mocker, caplog):
        _1 = mocker.patch.object(rpigpio, "remove_event_detect", autospec=True)
        _2 = mocker.patch.object(_dataprocessing.radio_q, "join", autospec=True)
        _3 = mocker.patch.object(main.display, "shutdown", autospec=True)
        with caplog.at_level(logging.INFO, logger='Datarecorder.datarecorder.main'):
            main.shut_down(0)
        assert "shut_down_called" in caplog.text


class TestDatabase:
    
    def test_initialize_database(self, caplog):
        with caplog.at_level(logging.INFO, logger="Datarecorder.datarecorder.database"):
            database.initialize_database("sqlite://")
        assert "Database initialized" in caplog.text
        with caplog.at_level(logging.CRITICAL, logger="Datarecorder.datarecorder.database"):
            try:
                database.initialize_database("")
            except:
                pass
        assert"Database initialization failed:" in caplog.text        


class TestDataProcessing:

    def test_packet_missing_or_duplicate_logs_a_warning_for_a_missing_packet(self, caplog):
        test_data = {"node_id": 0x01, "pkt_serial": 0x1012}
        _dataprocessing.last_packet_info = {
            0x01: {"pkt_serial": 0x0101, "timestamp": None}
        }
        with caplog.at_level(logging.WARNING, logger="Datarecorder.datarecorder._dataprocessing"):
            _dataprocessing.packet_missing_or_duplicate(test_data)
        assert "Data packet missing from node 0x01" in caplog.text

    def test_packet_missing_or_duplicate_logs_first_data_from_node(self, caplog):
        test_data = {"node_id": 0x01, "pkt_serial": 0x1010}
        _dataprocessing.last_packet_info = {
            0x02: {"pkt_serial": 0xFFFF, "timestamp": None}
        }
        with caplog.at_level(logging.INFO, logger="Datarecorder.datarecorder._dataprocessing"):
            _dataprocessing.packet_missing_or_duplicate(test_data)
        assert "First data packet from node 0x01" in caplog.text
        assert "Rx from node 0x01, packet serial 0x1010" in caplog.text

    def test_process_radio_data(self, mocker, caplog):
        mock_packet_missing_or_duplicate = mocker.patch.object(
            _dataprocessing, "packet_missing_or_duplicate", autospec=True
        )
        mock_expand_radio_data_into_dict = mocker.patch.object(
            _dataprocessing, "expand_radio_data_into_dict", autospec=True
        )
        mock_unpack_data_packet = mocker.patch.object(
            _dataprocessing, "unpack_data_packet", autospec=True
        )
        mock_radio_q = mocker.patch.object(
            _dataprocessing, "radio_q", autospec=True
        )
        mock_radio_q.get.return_value = None
        mock_unpack_data_packet.side_effect = [ValueError]
        mock_expand_radio_data_into_dict.return_value = {"node": None, "sensors": None}
        mock_packet_missing_or_duplicate.return_value = True
        with caplog.at_level(logging.WARNING, logger="Datarecorder.datarecorder._dataprocessing"):
            _dataprocessing.process_radio_data()
        assert "Bad data packet detected" in caplog.text


class TestOledDisplay:

    @pytest.mark.skip(reason="Logging not implemented in new display")
    def test_initialize_oled(self, mocker, caplog):
        mock_ssd1306 = mocker.patch.object(adafruit_ssd1306, "SSD1306_I2C")
        mock_ssd1306.side_effect = [ValueError, AttributeError]
        with caplog.at_level(logging.ERROR, logger="Datarecorder.helpers.oled_display"):
            oled_display.initialize_oled(None, None)
        assert "OLED display failed to initialize. Check that wiring is correct" in caplog.text
        with caplog.at_level(logging.ERROR, logger="Datarecorder.helpers.oled_display"):
            oled_display.initialize_oled(None, None)
        assert "OLED display failed to initialize. No I2C bus found" in caplog.text

    @pytest.mark.skip(reason="Logging not implemented in new display")
    def test_display_message_from_queue(self, mocker, caplog):
        _1 = mocker.patch.object(oled_display, "clear_display")
        mock_message_queue = mocker.patch.object(oled_display, "message_queue")
        mock_message_queue.get.side_effect = [queue.Empty]
        dummy_display = {"oled": Mock(), "lines": deque([])}
        with caplog.at_level(logging.ERROR, logger="Datarecorder.helpers.oled_display"):
            oled_display.display_message_from_queue(display=dummy_display)
        assert "Display thread called with empty queue" in caplog.text

    @pytest.mark.skip(reason="Logging not implemented in new display")
    def test_shut_down(self, mocker, caplog):
        _1 = mocker.patch.object(oled_display, "show_display", autospec=True)
        _2 = mocker.patch.object(oled_display, "clear_display", autospec=True)
        _3 = mocker.patch.object(oled_display, "message_queue", autospec=True)
        with caplog.at_level(logging.WARNING, logger="Datarecorder.helpers.oled_display"):
            oled_display.shut_down()
        assert "OLED display shutdown" in caplog.text
