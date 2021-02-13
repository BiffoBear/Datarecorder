#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import call
import adafruit_rfm69
import busio
import digitalio
from helpers import display
from datarecorder import _dataprocessing, main


class TestIntegrationWithDataProcessing:
    def test_message_from_init_radio(self, mocker):
        mock_write_message_to_queue = mocker.patch.object(main, "oled_message")
        _1 = mocker.patch.object(adafruit_rfm69, "RFM69")
        _2 = mocker.patch.object(digitalio, "DigitalInOut")
        _3 = mocker.patch.object(busio, "SPI")
        main.initialize_rfm69()
        mock_write_message_to_queue.assert_called_once_with("Radio initialized OK")

    def test_message_sent_when_packet_written(self, mocker):
        mock_write_message_to_queue = mocker.patch.object(_dataprocessing, "oled_message")
        _dataprocessing.last_packet_info = {0x02: {"pkt_serial": 0x0000}}
        node_data = {"node_id": 0x02, "pkt_serial": 0x0001}
        _dataprocessing.packet_missing_or_duplicate(node_data)
        mock_write_message_to_queue.assert_called_with("Rx 0x02 sn 0x0001")

    def test_message_sent_when_first_packet_received(self, mocker):
        mock_write_message_to_queue = mocker.patch.object(_dataprocessing, "oled_message")
        _dataprocessing.last_packet_info = {}
        node_data = {"node_id": 0x01, "pkt_serial": 0x0001}
        _dataprocessing.packet_missing_or_duplicate(node_data)
        calls = [call("First data node 0x01"), call("Rx 0x01 sn 0x0001")]
        mock_write_message_to_queue.assert_has_calls(calls)

    def test_message_sent_when_packet_missing(self, mocker):
        mock_write_message_to_queue = mocker.patch.object(_dataprocessing, "oled_message")
        _dataprocessing.last_packet_info = {0x01: {"pkt_serial": 0x0000}}
        node_data = {"node_id": 0x01, "pkt_serial": 0x0002}
        _dataprocessing.packet_missing_or_duplicate(node_data)
        calls = [call("*Data missing from node 0x01*"), call("Rx 0x01 sn 0x0002")]
        mock_write_message_to_queue.assert_has_calls(calls)

    def test_message_sent_when_bad_packet_received(self, mocker):
        mock_write_message_to_queue = mocker.patch.object(_dataprocessing, "oled_message")
        mock_unpack_data_packet = mocker.patch.object(
            _dataprocessing, "unpack_data_packet"
        )
        mock_radio_q = mocker.patch.object(_dataprocessing, "radio_q")
        mock_radio_q.get.return_value = None
        mock_unpack_data_packet.side_effect = [ValueError]
        _dataprocessing.process_radio_data()
        mock_write_message_to_queue.assert_called_once_with("*Bad data packet Rx*")
