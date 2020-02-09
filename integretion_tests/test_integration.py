from unittest import TestCase
from unittest.mock import Mock, patch
from database import database
from tests import unittest_helper
from commandline.commandlinetools import setup_node_argparse, setup_sensor_argparse


class IntegrationTesting(TestCase):

    def setUp(self):
        unittest_helper.initialize_database(db_in_memory=True)

    def tearDown(self):
        database.engine.dispose()

    def test_user_adds_a_node_with_correct_input_data(self):
        node_parser = setup_node_argparse()
        args = node_parser.parse_args(['add', '1', 'Test Node Name', 'Some location'])
        args.func(args)
        self.assertEqual(1, unittest_helper.count_all_node_records())

    def test_user_adds_a_sensor_with_correct_input_data(self):
        node_parser = setup_node_argparse()
        args = node_parser.parse_args(['add', '3', 'Test Node Name', 'Some location'])
        args.func(args)
        sensor_parser = setup_sensor_argparse()
        args = sensor_parser.parse_args(['add', '2', '3', 'Test Sensor Name', 'Mass'])
        args.func(args)
        self.assertEqual(1, unittest_helper.count_all_sensor_records())

    @patch('builtins.print')
    def test_user_adds_two_correct_nodes_then_one_with_bad_data(self, mock_print):
        node_parser = setup_node_argparse()
        args = node_parser.parse_args(['add', '1', 'Test Node Name', 'Some location'])
        args.func(args)
        args = node_parser.parse_args(['add', '233', 'Test Node Name 2', 'Some location 2'])
        args.func(args)
        self.assertEqual(2, unittest_helper.count_all_node_records())
        # duplicate node ID
        args = node_parser.parse_args(['add', '233', 'Test Node Name 3', 'Some location 3'])
        args.func(args)
        mock_print.assert_called_with('Unable to create node ID 0xe9 -- Record not created, node ID and name must be '
                                      'unique\n')

    @patch('builtins.print')
    def test_user_adds_two_correct_sensors_then_one_with_bad_data(self, mock_print):
        node_parser = setup_node_argparse()
        args = node_parser.parse_args(['add', '3', 'Test Node Name', 'Some location'])
        args.func(args)
        sensor_parser = setup_sensor_argparse()
        args = sensor_parser.parse_args(['add', '24', '3', 'Test Sensor Name', 'Mass'])
        args.func(args)
        args = sensor_parser.parse_args(['add', '2', '3', 'Test Sensor Name 2', 'Length'])
        args.func(args)
        self.assertEqual(2, unittest_helper.count_all_sensor_records())
        # duplicate sensor ID
        args = sensor_parser.parse_args(['add', '2', '3', 'Test Sensor Name 3', 'Length'])
        args.func(args)
        mock_print.assert_called_with('Unable to create sensor ID 0x02 -- Record not created, Sensor ID and name must '
                                      'be unique\n')

    @patch('builtins.print')
    def test_show_details_for_node(self, mock_print):
        node_parser = setup_node_argparse()
        args = node_parser.parse_args(['add', '3', 'Test Node Name', 'Some location'])
        args.func(args)
        args = node_parser.parse_args(['show', '3'])
        args.func(args)
        mock_print.assert_called_with('Details for node ID 3:\n\nNode_ID -- 0x03\nName -- Test Node Name\nLocation -- '
                                      'Some location\n\n')

    @patch('builtins.print')
    def test_show_details_for_sensors(self, mock_print):
        node_parser = setup_node_argparse()
        args = node_parser.parse_args(['add', '3', 'Test Node Name', 'Some location'])
        args.func(args)
        sensor_parser = setup_sensor_argparse()
        args = sensor_parser.parse_args(['add', '24', '3', 'Test Sensor Name', 'Mass'])
        args.func(args)
        args = sensor_parser.parse_args(['show', '24'])
        args.func(args)
        mock_print.assert_called_with('Details for sensor ID 24:\n\nSensor_ID -- 0x18\nNode_ID -- 0x03\nName -- Test '
                                      'Sensor Name\nQuantity -- Mass\n\n')

    @patch('builtins.print')
    def test_list_for_nodes(self, mock_print):
        node_parser = setup_node_argparse()
        args = node_parser.parse_args(['add', '1', 'Test Node Name', 'Some location'])
        args.func(args)
        args = node_parser.parse_args(['add', '5', 'Test Node Name 2', 'Some location 2'])
        args.func(args)
        args = node_parser.parse_args(['list'])
        args.func(args)
        mock_print.call_args.contains('[1mExisting Nodes[0m\n\n[90m00 [0m[1m01 [0m[90m02 [0m[90m03 [0m[90m04')

    @patch('builtins.print')
    def test_list_for_sensors(self, mock_print):
        node_parser = setup_node_argparse()
        args = node_parser.parse_args(['add', '1', 'Test Node Name', 'Some location'])
        args.func(args)
        sensor_parser = setup_sensor_argparse()
        args = sensor_parser.parse_args(['add', '1', '1', 'Test Sensor Name', 'Mass'])
        args.func(args)
        args = sensor_parser.parse_args(['list'])
        args.func(args)
        mock_print.call_args.contains('[1mExistimg Sensors[0m\n\n[90m00 [0m[1m01 [0m[90m02 [0m[90m03 [0m[90m04')
