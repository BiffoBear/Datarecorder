#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 07:17:26 2019

@author: martinstephens
"""

from unittest import TestCase
from unittest.mock import patch
from sqlalchemy import inspect
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound
from database import database
from tests import unittest_helper


class ConfirmDatabaseSetup(TestCase):

    def setUp(self):
        self.required_tables_and_columns = {'Sensor Readings': ['ID', 'Timestamp_UTC', 'Sensor_ID', 'Reading', ],
                                            'Sensors': ['ID', 'Node_ID', 'Quantity', 'Name', ],
                                            'Nodes': ['ID', 'Name', 'Location', ],
                                            'Events': {'ID',  'Timestamp_UTC', 'Node_ID', 'Event_Code'}}
        unittest_helper.initialize_database()
        self.inspector = inspect(database.engine)

    def tearDown(self):
        database.engine.dispose()

    def test_database_tables_exist(self):
        self.assertCountEqual(self.inspector.get_table_names(), self.required_tables_and_columns.keys())

    def test_database_table_columns_exist(self):
        for table in self.required_tables_and_columns.keys():
            required_columns = self.required_tables_and_columns[table]
            existing_columns = [x['name'] for x in self.inspector.get_columns(table)]
            self.assertCountEqual(existing_columns, required_columns)


class TestDataBaseInitialization(TestCase):

    def test_database_initialized(self):
        database.engine.dispose()
        database.initialize_database('sqlite://')
        self.assertNotEqual(database.engine, None)
        database.engine.dispose()

    def test_failure_to_initialize_database_raises_critical_error(self):
        database.engine.dispose()
        with self.assertRaises(sqlalchemy.exc.ArgumentError):
            database.initialize_database('')


class TestWriteSensorDataToDataBase(TestCase):

    def setUp(self):
        unittest_helper.initialize_database()

    def tearDown(self):
        database.engine.dispose()

    def test_write_sensor_data_to_database(self):
        test_time = unittest_helper.global_test_time
        test_data = {'timestamp': test_time, 'sensor_readings': [(0x01, 1.2345), (0x02, 2.3456)]}
        database.write_sensor_reading_to_db(test_data)
        s = database.session()
        t = database.SensorData
        q = s.query(t).all()
        database_records = [[x.Timestamp_UTC, x.Sensor_ID, x.Reading] for x in q]
        expected_result = [[test_time, x[0], x[1]] for x in test_data['sensor_readings']]
        self.assertEqual(database_records, expected_result)


def get_all_nodes():
    s = database.session()
    t = database.Nodes
    q = s.query(t).all()
    return [[x.ID, x.Name, x.Location] for x in q]


class TestAddNodeToDataBase(TestCase):

    def setUp(self):
        unittest_helper.initialize_database()

    def tearDown(self):
        database.engine.dispose()

    def test_check_id_and_name_is_valid_raises_typeerror_if_id_not_int(self):
        node_error_message = 'Record not created, node ID must be an integer'
        sensor_error_message = 'Record not created, sensor ID must be an integer'
        test_data = ({'id': 'a', 'name': 'A Name', 'type': 'node', 'error': node_error_message},
                     {'id': 'a', 'name': 'A Name', 'type': 'sensor', 'error': sensor_error_message},
                     {'id': None, 'name': 'A Name', 'type': 'sensor', 'error': sensor_error_message},
                     )
        for data in test_data:
            with self.assertRaises(TypeError) as dm:
                database._check_id_and_name_are_valid(id_to_check=data['id'],
                                                      name_to_check=data['name'],
                                                      record_type=data['type'],
                                                      )
            self.assertIn(data['error'], dm.exception.args)

    def test_check_id_and_name_is_valid_raises_valueerror_if_id_not_in_range(self):
        node_error_message = 'Record not created, node ID must be in range 0 - 254 (0x00 - 0xfe)'
        sensor_error_message = 'Record not created, sensor ID must be in range 0 - 254 (0x00 - 0xfe)'
        test_data = ({'id': 0xff, 'name': 'A Name', 'type': 'node', 'error': node_error_message},
                     {'id': 0xff, 'name': 'A Name', 'type': 'sensor', 'error': sensor_error_message},
                     {'id': -1, 'name': 'A Name', 'type': 'sensor', 'error': sensor_error_message},
                     )
        for data in test_data:
            with self.assertRaises(ValueError) as dm:
                database._check_id_and_name_are_valid(id_to_check=data['id'],
                                                      name_to_check=data['name'],
                                                      record_type=data['type'],
                                                      )
            self.assertIn(data['error'], dm.exception.args)

    def test_check_id_and_name_is_valid_raises_typeerror_if_name_not_string_starting_with_a_letter(self):
        node_error_message = 'Record not created, node name must be a string beginning with a letter'
        sensor_error_message = 'Record not created, sensor name must be a string beginning with a letter'
        test_data = ({'id': 0x05, 'name': 2, 'type': 'node', 'error': node_error_message},
                     {'id': 0x05, 'name': None, 'type': 'sensor', 'error': sensor_error_message},
                     {'id': 0x05, 'name': '', 'type': 'sensor', 'error': sensor_error_message},
                     {'id': 0x05, 'name': ' ', 'type': 'sensor', 'error': sensor_error_message},
                     {'id': 0x05, 'name': '.', 'type': 'sensor', 'error': sensor_error_message},
                     {'id': 0x05, 'name': '2', 'type': 'sensor', 'error': sensor_error_message},
                     )
        for data in test_data:
            with self.assertRaises(TypeError) as dm:
                database._check_id_and_name_are_valid(id_to_check=data['id'],
                                                      name_to_check=data['name'],
                                                      record_type=data['type'],
                                                      )
            self.assertIn(data['error'], dm.exception.args)

    def test_check_id_and_name_is_valid_returns_true_if_data_is_valid(self):
        self.assertTrue(database._check_id_and_name_are_valid(id_to_check=0x03,
                                                              name_to_check='Valid Name',
                                                              record_type='sensor',
                                                              ))

    def test_add_node_adds_unique_valid_data_that_it_is_called_with(self):
        test_data = [[0x01, 'Test node name', 'Dummy location'],
                     [0x02, 'Other node name', 'Dummy location'],
                     ]
        [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        database_records = get_all_nodes()
        self.assertEqual(database_records, test_data)

    def test_add_node_raises_valueerror_for_repeat_id(self):
        test_data = [[0x01, 'Test node name', 'Dummy location'],
                     [0x01, 'Other node name', 'Dummy location'],
                     ]
        with self.assertRaises(ValueError) as dm:
            [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        database_records = get_all_nodes()
        expected_result = [test_data[0]]
        self.assertEqual(database_records, expected_result)
        self.assertIn('Record not created, node ID and name must be unique', dm.exception.args)

    def test_add_node_raises_valueerror_for_repeat_names(self):
        test_data = [[0x01, 'Test node name', 'Dummy location'],
                     [0x02, 'Test node name', 'Dummy location'],
                     ]
        with self.assertRaises(ValueError) as dm:
            [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        database_records = get_all_nodes()
        expected_result = [test_data[0]]
        self.assertEqual(database_records, expected_result)
        self.assertIn('Record not created, node ID and name must be unique', dm.exception.args)


def get_all_sensors():
    s = database.session()
    t = database.Sensors
    q = s.query(t).all()
    return [[x.ID, x.Node_ID, x.Name, x.Quantity] for x in q]


@patch('database.database._node_id_exists')
class TestAddSensorToDatabase(TestCase):

    def setUp(self):
        unittest_helper.initialize_database()

    def tearDown(self):
        database.engine.dispose()

    def test_add_sensor_adds_unique_data_that_it_is_called_with(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, 'Dummy Sensor', 'Mass'],
                     [0x02, 0x01, 'Another Sensor', 'Mass'],
                     ]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        database_records = get_all_sensors()
        self.assertEqual(database_records, test_data)

    def test_add_sensor_raises_valueerror_for_repeat_id(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, 'Dummy Sensor', 'Mass'],
                     [0x01, 0x01, 'Another Sensor', 'Mass'],
                     ]
        with self.assertRaises(ValueError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        database_records = get_all_sensors()
        expected_result = [test_data[0]]
        self.assertEqual(database_records, expected_result)
        self.assertIn('Record not created, Sensor ID and name must be unique', dm.exception.args)

    def test_add_sensor_raises_valueerror_for_repeat_names(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, 'Dummy Sensor', 'Mass'],
                     [0x02, 0x01, 'Dummy Sensor', 'Mass'],
                     ]
        with self.assertRaises(ValueError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        database_records = get_all_sensors()
        expected_result = [test_data[0]]
        self.assertEqual(database_records, expected_result)
        self.assertIn('Record not created, Sensor ID and name must be unique', dm.exception.args)

    def test_add_sensor_raises_valueerror_if_node_id_does_not_exist(self, mock_node_id_exists):
        mock_node_id_exists.return_value = False
        test_data = [[0x01, 0x01, 'Dummy Name', 'Mass']]
        with self.assertRaises(ValueError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Record not created -- node with id 1 (0x01) must already exist in the database',
                      dm.exception.args)

    def test_add_sensor_only_raises_value_error_when_quantity_not_in_dict(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, 'Dummy Name', 'Temperature']]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        test_data = [[0x02, 0x01, 'Other Name', 'Incorrect quantity']]
        with self.assertRaises(ValueError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Sensor not created -- unknown sensor data quantity supplied', dm.exception.args)


class TestReadFromDatabaseFunctions(TestCase):

    def setUp(self):
        unittest_helper.initialize_database()

    def tearDown(self):
        database.engine.dispose()

    def test_node_id_exists_returns_true_if_node_exists_false_if_not(self):
        test_data = [[0x01, 'Test node name', 'Dummy location']]
        [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        self.assertTrue(database._node_id_exists(node_id=1))
        self.assertFalse(database._node_id_exists(node_id=2))

    @patch('database.database._node_id_exists')
    def test_sensor_id_exists_returns_true_if_sensor_exists_false_if_not(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, 'Dummy Sensor', 'Mass']]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertTrue(database._sensor_id_exists(sensor_id=1))
        self.assertFalse(database._sensor_id_exists(sensor_id=2))

    @patch('database.database._node_id_exists')
    def test_get_all_sensor_ids_returns_a_generator_with_all_sensor_ids(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, 'Sensor 1', 'Mass'],
                     [0x02, 0x01, 'Sensor 2', 'Mass'],
                     [0x03, 0x01, 'Sensor 3', 'Mass'],
                     ]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        returned_result = database.get_all_sensor_ids()
        self.assertListEqual([x[0] for x in test_data], [y for y in returned_result])

    def test_get_all_node_ids_returns_a_generator_with_all_node_ids(self):
        test_data = [[0x01, 'Node 1', 'Dummy location'],
                     [0x02, 'Node 2', 'Dummy lacation'],
                     ]
        [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        returned_result = database.get_all_node_ids()
        self.assertListEqual([x[0] for x in test_data], [y for y in returned_result])

    @patch('database.database._node_id_exists')
    def test_get_all_ids_returns_a_generator_with_correct_values(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data_nodes = [[0x01, 'Node 1', 'Dummy location'],
                     [0x02, 'Node 2', 'Dummy lacation'],
                     ]
        [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data_nodes]
        test_data_sensors = [[0x01, 0x01, 'Sensor 1', 'Mass'],
                     [0x02, 0x01, 'Sensor 2', 'Mass'],
                     [0x03, 0x01, 'Sensor 3', 'Mass'],
                     ]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data_sensors]
        returned_result = database._get_all_ids(table='node')
        self.assertListEqual([x[0] for x in test_data_nodes], [y for y in returned_result])
        returned_result = database._get_all_ids(table='sensor')
        self.assertListEqual([x[0] for x in test_data_sensors], [y for y in returned_result])

    def test_get_all_ids_returns_an_empty_generator_if_no_records(self):
        returned_result = database._get_all_ids(table='node')
        self.assertListEqual([], [y for y in returned_result])

    @patch('database.database._node_id_exists')
    def test_get_sensors_for_a_node(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data_nodes = [[0x01, 'Node 1', 'Dummy location'],
                     [0x02, 'Node 2', 'Dummy lacation'],
                     ]
        [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data_nodes]
        test_data_sensors = [[0x01, 0x01, 'Sensor 1', 'Mass'],
                     [0x02, 0x01, 'Sensor 2', 'Mass'],
                     [0x03, 0x01, 'Sensor 3', 'Mass'],
                     [0x04, 0x02, 'Sensor 4', 'Mass'],
                     ]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data_sensors]
        returned_result = database.get_all_sensor_ids_for_a_node(node=1)
        self.assertListEqual([x[0] for x in test_data_sensors[0:3]], [y for y in returned_result])

    def test_get_sensors_for_a_node_returns_empty_list_if_no_sensors_on_node(self):
        test_data = [[0x01, 'Node 1', 'Dummy location']]
        [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        returned_result = database.get_all_sensor_ids_for_a_node(node=1)
        self.assertListEqual([], [y for y in returned_result])

    def test_get_sensors_for_a_node_raises_noresultfound_exception_if_node_does_not_exist(self):
        with self.assertRaises(NoResultFound) as dm:
            database.get_all_sensor_ids_for_a_node(node=1)
        self.assertIn('node ID 0x01 not found in the database', dm.exception.args)

    def test_get_sensors_for_a_node_raises_typeerror_if_not_called_with_int(self):
        with self.assertRaises(TypeError) as dm:
            database.get_all_sensor_ids_for_a_node(node='a')
        self.assertIn("node must be an integer (not <class 'str'>)", dm.exception.args)

    def test_get_node_or_sensor_returns_all_data_for_the_query(self):
        test_data = [[0x01, 'Node 1', 'Dummy location'],
                     [0x02, 'Node 2', 'Other location'],
                     ]
        [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        test_data = [[0x01, 0x01, 'Sensor 1', 'Mass'],
                     [0x02, 0x01, 'Sensor 2', 'Mass'],
                     [0x03, 0x01, 'Sensor 3', 'Mass'],
                     ]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        returned_result = database._get_node_or_sensor(search_term=1, table='sensor')
        self.assertListEqual(test_data[0], [returned_result.ID, returned_result.Node_ID,
                                            returned_result.Name, returned_result.Quantity
                                            ])

    def test_get_node_or_sensor_raises_typeerror_if_not_called_with_int(self):
        with self.assertRaises(TypeError) as dm:
            database._get_node_or_sensor(search_term='a', table='node')
        self.assertIn("node must be an integer (not <class 'str'>)", dm.exception.args)
        with self.assertRaises(TypeError) as dm:
            database._get_node_or_sensor(search_term='a', table='sensor')
        self.assertIn("sensor must be an integer (not <class 'str'>)", dm.exception.args)

    def test_get_node_or_sensor_raises_noresultfound_exception_if_record_does_not_exist(self):
        with self.assertRaises(NoResultFound) as dm:
            database._get_node_or_sensor(search_term=1, table='sensor')
        self.assertIn('node ID 0x01 not found in the database', dm.exception.args)

    def test_get_node_data_returns_a_dict(self):
        test_data = [[0x01, 'Node 1', 'Dummy location'],
                     [0x02, 'Node 2', 'Other location'],
                     ]
        [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        expected_result = {'Node_ID': test_data[0][0], 'Name': test_data[0][1], 'Location': test_data[0][2]}
        returned_result = database.get_node_data(node=1)
        self.assertDictEqual(expected_result, returned_result)

    @patch('database.database._node_id_exists')
    def test_get_sensor_data_returns_a_dict(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, 'Sensor 1', 'Mass'],
                     [0x02, 0x01, 'Sensor 2', 'Mass'],
                     [0x03, 0x01, 'Sensor 3', 'Mass'],
                     ]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        expected_result = {'Sensor_ID': test_data[0][0], 'Node_ID': test_data[0][1],
                           'Name': test_data[0][2], 'Quantity': test_data[0][3],
                           }
        returned_result = database.get_sensor_data(sensor=1)
        self.assertDictEqual(expected_result, returned_result)