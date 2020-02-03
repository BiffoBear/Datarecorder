#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 07:17:01 2019

@author: martinstephens
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.orm.exc import NoResultFound

from __config__ import FILE_DEBUG_LEVEL, SI_UNITS

logger = logging.getLogger(__name__)
logger.setLevel(FILE_DEBUG_LEVEL)

Base = declarative_base()

# For PostGreSQL on local machine (host is None for Unix path instead of TCP)
# postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]

engine = None
session = None


class SensorData(Base):

    __tablename__ = 'Sensor Readings'

    ID = Column(Integer, primary_key=True)
    Timestamp_UTC = Column(DateTime)
    Sensor_ID = Column(Integer)
    Reading = Column(Float)


class Nodes(Base):

    __tablename__ = 'Nodes'

    ID = Column(Integer, primary_key=True)
    Name = Column(String, unique=True)
    Location = Column(String)


class Sensors(Base):

    __tablename__ = 'Sensors'

    ID = Column(Integer, primary_key=True)
    Node_ID = Column(Integer, ForeignKey('Nodes.ID'))
    Name = Column(String, unique=True)
    Quantity = Column(String)
    node = relationship(Nodes, backref=backref('node_sensors', uselist=True))


def initialize_database(db_url):
    logger.debug(f'initialize_database called')
    global Base, engine, session
    try:
        engine = create_engine(db_url)
        session = sessionmaker()
        session.configure(bind=engine)
        Base.metadata.create_all(engine)
    except Exception as e:
        logger.critical(f'Database initialization failed: {e}')
        raise e
    else:
        logger.info('Database initialized')


def write_sensor_reading_to_db(data):
    """Takes a dict with timestamp and a list of tuples of sensor_readings and writes them out to the database."""
    logger.debug(f'write_sensor_reading_to_db called')
    try:
        # noinspection PyCallingNonCallable
        s = session()
        [s.add(SensorData(Timestamp_UTC=data['timestamp'],
                          Sensor_ID=r[0],
                          Reading=r[1])) for r in data['sensor_readings']]
        s.commit()
    except Exception as error:
        logger.critical(f'IOError writing to database')
        raise error


def _check_id_and_name_are_valid(id_to_check=None, name_to_check=None, record_type=None):
    try:
        assert type(id_to_check) == int
    except AssertionError as e:
        raise TypeError(f'Record not created, {record_type} ID must be an integer') from e
    try:
        assert 0 <= id_to_check <= 254
    except AssertionError as e:
        raise ValueError(f'Record not created, {record_type} ID must be in range 0 - 254 (0x00 - 0xfe)') from e
    try:
        assert type(name_to_check) == str
        assert name_to_check != ''
        assert name_to_check[0].isalpha()
    except AssertionError as e:
        raise TypeError(f'Record not created, {record_type} name must be a string beginning with a letter') from e
    return True


def add_node(node_id=None, name=None, location=None):
    """Adds a new node to the 'Nodes' table of the 'Sensor Readings' database.

    Checks that args are valid before writing the record to the database.

    Arguments:
        node_id -- the unique ID of the new node, an integer in range 0 - 254
        name -- the unique, human readable, name of the node, a str object
        location -- the description of the node's location, a str object

    Returns:
        None
    """
    assert _check_id_and_name_are_valid(id_to_check=node_id, name_to_check=name, record_type='node')
    s = session()
    try:
        s.add(Nodes(ID=node_id, Name=name, Location=location))
        s.commit()
    except IntegrityError as e:
        raise ValueError('Record not created, node ID and name must be unique') from e


def _node_id_exists(node_id=None):
    s = session()
    t = Nodes
    try:
        s.query(t).filter(t.ID == node_id).one()
    except NoResultFound:
        return False
    return True


def _sensor_id_exists(sensor_id=None):
    s = session()
    t = Sensors
    try:
        s.query(t).filter(t.ID == sensor_id).one()
    except NoResultFound:
        return False
    return True


def add_sensor(sensor_id=None, node_id=None, name=None, quantity=None):
    """Adds a new sensor to the 'Sensors' table of the 'Sensor Readings' database.

    Checks that args are valid before writing the record to the database.

    Arguments:
        sensor_id -- the unique ID of the new sensor, an integer in range 0 - 254
        node_id -- the node that the sensor is attached to (node must already exist)
        name -- the unique, human readable, name of the node, a str object
        quantity -- the SI quantity that the sensor measures. Checked against SI_UNITS dict

    Returns:
        None
    """
    assert _check_id_and_name_are_valid(id_to_check=sensor_id, name_to_check=name, record_type='sensor')
    try:
        assert _node_id_exists(node_id)
    except AssertionError as e:
        raise ValueError(f'Record not created -- node with id {node_id} (0x{node_id:02x}) must already exist in the '
                         f'database')
    try:
        SI_UNITS[quantity]
    except KeyError:
        raise ValueError('Sensor not created -- unknown sensor data quantity supplied')
    s = session()
    try:
        s.add(Sensors(ID=sensor_id, Node_ID=node_id, Name=name, Quantity=quantity))
        s.commit()
    except IntegrityError as e:
        raise ValueError('Record not created, Sensor ID and name must be unique') from e


def _get_all_ids(table=None):
    db_session = session()
    table_to_query = {'node': Nodes, 'sensor': Sensors}[table]
    query = db_session.query(table_to_query).all()
    return (x.ID for x in query)


def get_all_node_ids():
    """Returns a generator with all the node IDs."""
    return _get_all_ids(table='node')


def get_all_sensor_ids():
    """Returns a generator with all the sensor IDs."""
    return _get_all_ids(table='sensor')


def _get_node_or_sensor(search_term=None, table=None):
    try:
        assert type(search_term) == int
    except AssertionError as e:
        raise TypeError(f'{table} must be an integer (not {type(search_term)})') from e
    table_to_query = {'node': Nodes, 'sensor': Sensors}[table]
    db_session = session()
    try:
        query = db_session.query(table_to_query).filter(table_to_query.ID == search_term).one()
    except NoResultFound as e:
        raise NoResultFound(f'node ID 0x{search_term:02x} not found in the database') from e
    return query


def get_all_sensor_ids_for_a_node(node=None):
    """Returns a generator with all the sensor IDs attached to a node.

    Arguments:
        node -- the node ID to find sensors for, an integer.
    """
    try:
        assert type(node) == int
    except AssertionError as e:
        raise TypeError(f'node must be an integer (not {type(node)})') from e
    db_session = session()
    try:
        query = db_session.query(Nodes).filter(Nodes.ID == node).one()
    except NoResultFound as e:
        raise NoResultFound(f'node ID 0x{node:02x} not found in the database') from e
    return (x.ID for x in query.node_sensors)


def get_node_data(node=None):
    """Returns all the data for a given node ID.

    Arguments:
        node -- node ID whose data is to be returned, an integer
    Returns:
        dict {'Node_ID': node_data.ID, 'Name': node_data.Name, 'Location': node_data.Location}
        """
    node_data = _get_node_or_sensor(search_term=node, table='node')
    return {'Node_ID': node_data.ID, 'Name': node_data.Name, 'Location': node_data.Location}


def get_sensor_data(sensor=None):
    """Returns all the data for a given sensor ID

    Arguments:
        sensor -- sensor ID whose data is to be returned, an integer
    Returns:
        {'Sensor_ID': sensor_data.ID, 'Node_ID': sensor_data.Node_ID,
            'Name': sensor_data.Name, 'Quantity': sensor_data.Quantity}
    """
    sensor_data = _get_node_or_sensor(search_term=sensor, table='sensor')
    return {'Sensor_ID': sensor_data.ID, 'Node_ID': sensor_data.Node_ID,
            'Name': sensor_data.Name, 'Quantity': sensor_data.Quantity,
            }
