#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 07:17:01 2019

@author: martinstephens
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
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


class Sensors(Base):

    __tablename__ = 'Sensors'

    ID = Column(Integer, primary_key=True)
    Node_ID = Column(Integer)
    Name = Column(String, unique=True)
    Quantity = Column(String)


class Nodes(Base):

    __tablename__ = 'Nodes'

    ID = Column(Integer, primary_key=True)
    Name = Column(String, unique=True)
    Location = Column(String)


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
    try:
        assert type(node_id) == int
    except AssertionError as e:
        raise TypeError('Node not created, node ID must be an integer') from e
    try:
        assert 0 <= node_id <= 254
    except AssertionError as e:
        raise ValueError('Node not created, node ID must be in range 0 - 254') from e
    try:
        assert name is not None
        assert name != ''
    except AssertionError as e:
        raise TypeError('Node not created -- name must be string') from e

    s = session()
    try:
        s.add(Nodes(ID=node_id, Name=name, Location=location))
        s.commit()
    except IntegrityError as e:
        raise ValueError('Node not created, node ID and name must be unique') from e


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

    try:
        assert _node_id_exists(node_id)
    except AssertionError as e:
        raise ValueError('Sensor not created -- node_id must already exist in the database') from e
    try:
        assert type(sensor_id) == int
    except AssertionError as e:
        raise TypeError('Sensor not created, sensor ID must be an integer') from e
    try:
        assert 0 <= sensor_id <= 254
    except AssertionError as e:
        raise ValueError('Sensor not created, sensor ID must be in range 0 - 254') from e
    try:
        assert name is not None
        assert name != ''
    except AssertionError as e:
        raise TypeError('Sensor not created -- name must be string') from e
    try:
        SI_UNITS[quantity]
    except KeyError:
        raise ValueError('Sensor not created -- unknown quantity supplied')
    s = session()
    try:
        s.add(Sensors(ID=sensor_id, Node_ID=node_id, Name=name, Quantity=quantity))
        s.commit()
    except IntegrityError as e:
        raise ValueError('Sensor not created, Sensor ID and name must be unique') from e


def get_all_node_ids():
    s = session()
    t = Nodes
    q = s.query(t).all()
    return (x.ID for x in q)


def get_all_sensor_ids():
    s = session()
    t = Sensors
    q = s.query(t).all()
    return (x.ID for x in q)
