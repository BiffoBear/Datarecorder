#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 07:17:01 2019

@author: martinstephens
"""
# TODO: Add a get all nodes query that returns the nodes and associated sensors
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from __config__ import FILE_DEBUG_LEVEL

logger = logging.getLogger(__name__)
logger.setLevel(FILE_DEBUG_LEVEL)

Base = declarative_base()

# For PoatGreSQL on local machine (host is None for Unix path instead of TCP)
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
    Unit = Column(String)


class Nodes(Base):

    __tablename__ = 'Nodes'

    ID = Column(Integer, primary_key=True)
    Name = Column(String, unique=True)
    Location = Column(String)


class Conversions(Base):

    __tablename__ = 'Conversions'

    ID = Column(Integer, primary_key=True)


def write_sensor_reading_to_db(data):
    '''Takes a dict with timestamp and a list of tuples of sensor_readings and writes them out to the database.'''
    logger.debug(f'write_sensor_reading_to_db called')
    try:
        s = session()
        [s.add(SensorData(Timestamp_UTC=data['timestamp'], Sensor_ID=r[0], Reading=r[1])) for r in data['sensor_readings']]
        s.commit()
    except Exception as error:
        logger.critical(f'IOError writing to database')
        raise error


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
