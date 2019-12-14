#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 07:17:26 2019

@author: martinstephens
"""

from unittest import TestCase, skip
from unittest.mock import Mock, patch
from sqlalchemy import inspect
import database
import unittest_helper


#@skip
class ConfirmDatabaseSetup(TestCase):

    def setUp(self):
        self.required_tables_and_columns = {'Sensor Readings': ['ID', 'Timestamp_UTC', 'Sensor_ID', 'Reading',],
                                            'Sensors': ['ID', 'Node_ID', 'Unit', 'Name',],
                                            'Nodes': ['ID', 'Name', 'Location',],
                                            'Conversions': ['ID',],
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

    def test_database_initalized(self):
        database.engine.dispose()
        database.engine = None
        with self.assertLogs() as cm:
            database.initialize_database('sqlite://')
        self.assertEqual(cm.output, ['DEBUG:database:initialize_database called'])
        self.assertNotEqual(database.engine, None)
        
    def test_failure_to_initialize_database_raises_critical_error(self):
        pass
        # TODO: Work out how to test this

#@skip
class TestWriteDataToDataBase(TestCase):

    def setUp(self):
        unittest_helper.initialize_database()

    def tearDown(self):
        database.engine.dispose()

    def test_write_sensor_data_to_database(self):
        test_time = unittest_helper.global_test_time
        test_data = {'timestamp': test_time, 'sensor_readings':[(0x01, 1.2345), (0x02, 2.3456)]}
        with self.assertLogs() as cm:
            database.write_sensor_reading_to_db(test_data)
        self.assertEqual(cm.output, ['DEBUG:database:write_sensor_reading_to_db called'])
        s = database.session()
        t = database.SensorData
        q = s.query(t).all()
        database_records = [[t.Timestamp_UTC, t.Sensor_ID, t.Reading] for t in q]
        expected_result = [[test_time, x[0], x[1]] for x in test_data['sensor_readings']]
        self.assertEqual(database_records, expected_result)
    

    def test_db_write_failure_logs_critical_error_and_raises_error(self):
        pass
        # TODO: Work out how to mock this out properly
#        mock_session.side_effect = IOError
#        with self.assertLogs(level='CRITICAL') as cm:
#            with self.assertRaises(IOError):
#                database.write_sensor_reading_to_db('data')
#        self.assertEqual(cm.output, 'blah')
