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
from database import database
from tests import unittest_helper


class ConfirmDatabaseSetup(TestCase):

    def setUp(self):
        self.required_tables_and_columns = {'Sensor Readings': ['ID', 'Timestamp_UTC', 'Sensor_ID', 'Reading', ],
                                            'Sensors': ['ID', 'Node_ID', 'Quantity', 'Name', ],
                                            'Nodes': ['ID', 'Name', 'Location', ],
                                            }
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

    def test_add_node_adds_unique_data_that_it_is_called_with(self):
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
        self.assertIn('Node not created, node ID and name must be unique', dm.exception.args)

    def test_max_node_id_is_0xfe(self):
        test_data = [[0xff, 'Test node name', 'Dummy location'], ]
        with self.assertRaises(ValueError) as dm:
            [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        self.assertIn('Node not created, node ID must be in range 0 - 254', dm.exception.args)

    def test_min_node_id_is_0x00(self):
        test_data = [[-1, 'Test node name', 'Dummy location'], ]
        with self.assertRaises(ValueError) as dm:
            [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        self.assertIn('Node not created, node ID must be in range 0 - 254', dm.exception.args)

    def test_node_id_not_int_raises_typeerror(self):
        test_data = [[None, 'Test node name', 'Dummy location'], ]
        with self.assertRaises(TypeError) as dm:
            [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        self.assertIn('Node not created, node ID must be an integer', dm.exception.args)

    def test_add_node_raises_valueerror_for_repeat_names(self):
        test_data = [[0x01, 'Test node name', 'Dummy location'],
                     [0x02, 'Test node name', 'Dummy location'],
                     ]
        with self.assertRaises(ValueError) as dm:
            [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        database_records = get_all_nodes()
        expected_result = [test_data[0]]
        self.assertEqual(database_records, expected_result)
        self.assertIn('Node not created, node ID and name must be unique', dm.exception.args)

    def test_add_node_raises_typeerror_for_name_is_none(self):
        test_data = [[0x01, None, 'Dummy location']]
        with self.assertRaises(TypeError) as dm:
            [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        self.assertIn('Node not created -- name must be string', dm.exception.args)

    def test_add_node_raises_valueerror_for_name_is_empty_string(self):
        test_data = [[0x01, '', 'Dummy location']]
        with self.assertRaises(TypeError) as dm:
            [database.add_node(node_id=x[0], name=x[1], location=x[2]) for x in test_data]
        self.assertIn('Node not created -- name must be string', dm.exception.args)


def get_all_sensors():
    s = database.session()
    t = database.Sensors
    q = s.query(t).all()
    return [[x.ID, x.Node_ID, x.Name, x.Quantity] for x in q]


@patch('database.database.node_id_exists')
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
        self.assertIn('Sensor not created, Sensor ID and name must be unique', dm.exception.args)

    def test_max_sensor_id_is_0xfe(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0xff, 0x01, 'Dummy Sensor', 'Mass']]
        with self.assertRaises(ValueError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Sensor not created, sensor ID must be in range 0 - 254', dm.exception.args)

    def test_min_sensor_id_is_0x00(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[-1, 0x01, 'Dummy Sensor', 'Mass']]
        with self.assertRaises(ValueError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Sensor not created, sensor ID must be in range 0 - 254', dm.exception.args)

    def test_sensor_id_not_int_raises_typeerror(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[None, 0x01, 'Dummy Sensor', 'Mass']]
        with self.assertRaises(TypeError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Sensor not created, sensor ID must be an integer', dm.exception.args)

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
        self.assertIn('Sensor not created, Sensor ID and name must be unique', dm.exception.args)

    def test_add_sensor_raises_typeerror_for_name_is_none(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, None, 'Mass']]
        with self.assertRaises(TypeError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Sensor not created -- name must be string', dm.exception.args)

    def test_add_sensor_raises_valueerror_for_name_is_empty_string(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, '', 'Mass']]
        with self.assertRaises(TypeError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Sensor not created -- name must be string', dm.exception.args)

    def test_add_sensor_raises_valueerror_if_node_id_does_not_exist(self, mock_node_id_exists):
        mock_node_id_exists.return_value = False
        test_data = [[0x01, 0x01, 'Dummy Name', 'Mass']]
        with self.assertRaises(ValueError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Sensor not created -- node_id must already exist in the database', dm.exception.args)

    def test_add_sensor_only_raises_value_error_when_quantity_not_in_dict(self, mock_node_id_exists):
        mock_node_id_exists.return_value = True
        test_data = [[0x01, 0x01, 'Dummy Name', 'Temperature']]
        [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        test_data = [[0x02, 0x01, 'Other Name', 'Incorrect quantity']]
        with self.assertRaises(ValueError) as dm:
            [database.add_sensor(sensor_id=x[0], node_id=x[1], name=x[2], quantity=x[3]) for x in test_data]
        self.assertIn('Sensor not created -- unknown quantity supplied', dm.exception.args)
