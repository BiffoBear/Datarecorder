#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import patch, call
from datarecorder import _dataprocessing, main


@patch('datarecorder._oleddisplay.write_message_to_queue')
class TestIntegrationWithDataProcessing(TestCase):

    @patch('digitalio.DigitalInOut')
    @patch('adafruit_rfm69.RFM69')
    @patch('busio.SPI')
    def test_message_from_init_radio(self, _1, _2, _3, mock_write_message_to_queue):
        main.initialize_rfm69()
        mock_write_message_to_queue.assert_called_once_with(f'Radio initialized OK')

    def test_message_sent_when_packet_written(self, mock_write_message_to_queue):
        _dataprocessing.last_packet_info = {0x02: {'pkt_serial': 0x0000}}
        node_data = {'node_id': 0x02, 'pkt_serial': 0x0001}
        _dataprocessing.check_for_duplicate_or_missing_packet(node_data)
        mock_write_message_to_queue.assert_called_with('Rx 0x02 sn 0x0001')

    def test_message_sent_when_first_packet_received(self, mock_write_message_to_queue):
        _dataprocessing.last_packet_info = {}
        node_data = {'node_id': 0x01, 'pkt_serial': 0x0001}
        _dataprocessing.check_for_duplicate_or_missing_packet(node_data)
        calls = [call('First data node 0x01'), call('Rx 0x01 sn 0x0001')]
        mock_write_message_to_queue.assert_has_calls(calls)

    def test_message_sent_when_packet_missing(self, mock_write_message_to_queue):
        _dataprocessing.last_packet_info = {0x01: {'pkt_serial': 0x0000}}
        node_data = {'node_id': 0x01, 'pkt_serial': 0x0002}
        _dataprocessing.check_for_duplicate_or_missing_packet(node_data)
        calls = [call('*Data missing from node 0x01*'), call('Rx 0x01 sn 0x0002')]
        mock_write_message_to_queue.assert_has_calls(calls)

    @patch('datarecorder._dataprocessing.unpack_data_packet')
    @patch('datarecorder._dataprocessing.radio_q')
    def test_message_sent_when_bad_packet_received(self, mock_radio_q,
                                                   mock_unpack_data_packet,
                                                   mock_write_message_to_queue,
                                                   ):
        mock_radio_q.get.return_value = None
        mock_unpack_data_packet.side_effect = [ValueError]
        _dataprocessing.process_radio_data()
        mock_write_message_to_queue.assert_called_once_with('*Bad data packet Rx*')
