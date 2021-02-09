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
engine = None
session = None

# Classes defined for database ORM and thus have no public methods.
class SensorData(Base):
    # pylint: disable=too-few-public-methods
    """ORM for the database Sensor Readings table."""

    __tablename__ = "Sensor Readings"

    ID = Column(Integer, primary_key=True)
    Timestamp_UTC = Column(DateTime)
    Sensor_ID = Column(Integer)
    Reading = Column(Float)


class NodeEvents(Base):
    # pylint: disable=too-few-public-methods
    """ORM for the database Events table."""

    __tablename__ = "Events"

    ID = Column(Integer, primary_key=True)
    Timestamp_UTC = Column(DateTime)
    Node_ID = Column(Integer, ForeignKey("Nodes.ID"))
    Event_Code = Column(Integer)


class Nodes(Base):
    # pylint: disable=too-few-public-methods
    """ORM for the database Nodes table."""

    __tablename__ = "Nodes"

    ID = Column(Integer, primary_key=True)
    Name = Column(String, unique=True)
    Location = Column(String)


class Sensors(Base):
    # pylint: disable=too-few-public-methods
    """ORM for the database Sensors table."""

    __tablename__ = "Sensors"

    ID = Column(Integer, primary_key=True)
    Node_ID = Column(Integer, ForeignKey("Nodes.ID"))
    Name = Column(String, unique=True)
    Quantity = Column(String)
    node = relationship(Nodes, backref=backref("node_sensors", uselist=True))


def initialize_database(db_url):
    """Initialize the database connection."""
    logger.debug("initialize_database called")
    global Base, engine, session
    try:
        engine = create_engine(db_url)
        session = sessionmaker()
        session.configure(bind=engine)
        Base.metadata.create_all(engine)
    except Exception as error:
        logger.critical(f"Database initialization failed: {error}")
        raise error
    else:
        logger.info("Database initialized")


def write_sensor_reading_to_db(data):
    """Take a dict with timestamp and a list of tuples of sensor_readings and write
    it out to the database."""
    logger.debug("write_sensor_reading_to_db called")
    try:
        # noinspection PyCallingNonCallable
        create_session = session()
        [
            create_session.add(
                SensorData(
                    Timestamp_UTC=data["timestamp"], Sensor_ID=reading[0], Reading=reading[1]
                )
            )
            for reading in data["sensor_readings"]
        ]
        create_session.commit()
    except Exception as error:
        logger.critical(f"IOError writing to database")
        raise error


def write_events_to_db(data):
    """Take a dict with timestamp, node and a list of event codes and write
    it to the database."""
    logger.debug("write_event_to_db called")
    try:
        # noinspection PyCallingNonCallable
        create_session = session()
        [
            create_session.add(
                NodeEvents(
                    Timestamp_UTC=data["timestamp"],
                    node_ID=data["node_id"],
                    Event_Code=code,
                )
            )
            for code in data["event_codes"]
        ]
        create_session.commit()
    except Exception as error:
        logger.critical("IOError writing to database")
        raise error


def _check_id_and_name_are_valid(
    id_to_check=None, name_to_check=None, record_type=None
):
    """Check that the name and id are valid for the given database record type."""
    try:
        assert type(id_to_check) == int
    except AssertionError as error:
        raise TypeError(
            f"Record not created, {record_type} ID must be an integer"
        ) from error
    try:
        assert 0 <= id_to_check <= 254
    except AssertionError as error:
        raise ValueError(
            f"Record not created, {record_type} ID must be in range 0 - 254 (0x00 - 0xfe)"
        ) from error
    try:
        assert type(name_to_check) == str
        assert name_to_check != ""
        assert name_to_check[0].isalpha()
    except AssertionError as error:
        raise TypeError(
            f"Record not created, {record_type} name must be a string beginning with a letter"
        ) from error
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

    Exceptions:
        ValueError if name and or node_id are not unique (i.e. exist in the database)
    """
    assert _check_id_and_name_are_valid(
        id_to_check=node_id, name_to_check=name, record_type="node"
    )
    create_session = session()
    try:
        create_session.add(Nodes(ID=node_id, Name=name, Location=location))
        create_session.commit()
    except IntegrityError as error:
        raise ValueError("Record not created, node ID and name must be unique") from error

# TODO: Refactor existence checks
def _node_id_exists(node_id=None):
    """Check if the node id exists in the database."""
    query_session = session()
    query_table = Nodes
    try:
        query_session.query(query_table).filter(query_table.ID == node_id).one()
    except NoResultFound:
        return False
    return True


def _sensor_id_exists(sensor_id=None):
    """Check if the sensor id exists in the database."""
    query_session = session()
    query_table = Sensors
    try:
        query_session.query(query_table).filter(query_table.ID == sensor_id).one()
    except NoResultFound:
        return False
    return True


def add_sensor(sensor_id=None, node_id=None, name=None, quantity=None):
    """Add a new sensor to the 'Sensors' table of the 'Sensor Readings' database.

    Check that args are valid before writing the record to the database.

    Arguments:
        sensor_id -- the unique ID of the new sensor, an integer in range 0 - 254
        node_id -- the node that the sensor is attached to (node must already exist)
        name -- the unique, human readable, name of the node, a str object
        quantity -- the SI quantity that the sensor measures. Checked against SI_UNITS dict

    Returns:
        None
    """
    assert _check_id_and_name_are_valid(
        id_to_check=sensor_id, name_to_check=name, record_type="sensor"
    )
    try:
        assert _node_id_exists(node_id)
    except AssertionError as error:
        raise ValueError(
            f"Record not created -- node with id {node_id} (0x{node_id:02x}) must "
            "already exist in the database"
        )
    try:
        SI_UNITS[quantity]
    except KeyError:
        raise ValueError("Sensor not created -- unknown sensor data quantity supplied")
    create_session = session()
    try:
        create_session.add(Sensors(ID=sensor_id, Node_ID=node_id, Name=name, Quantity=quantity))
        create_session.commit()
    except IntegrityError as error:
        raise ValueError("Record not created, Sensor ID and name must be unique") from error


def _get_all_ids(table=None):
    """Get all IDs from the database for the given table."""
    db_session = session()
    table_to_query = {"node": Nodes, "sensor": Sensors}[table]
    query = db_session.query(table_to_query).all()
    return (result.ID for result in query)


# TODO refactor to call with the table object
def get_all_node_ids():
    """Generate all the node IDs."""
    return _get_all_ids(table="node")


# TODO refactor to call with the table object
def get_all_sensor_ids():
    """Generate all the sensor IDs."""
    return _get_all_ids(table="sensor")


def _get_node_or_sensor(search_term=None, table=None):
    try:
        assert isinstance(search_term, int)
    except AssertionError as error:
        raise TypeError(f"{table} must be an integer (not {type(search_term)})") from error
    table_to_query = {"node": Nodes, "sensor": Sensors}[table]
    db_session = session()
    try:
        query_result = (
            db_session.query(table_to_query)
            .filter(table_to_query.ID == search_term)
            .one()
        )
    except NoResultFound as error:
        raise NoResultFound(
            f"node ID 0x{search_term:02x} not found in the database"
        ) from error
    return query_result


def get_all_sensor_ids_for_a_node(node=None):
    """Return a generator with all the sensor IDs attached to a node.

    Arguments:
        node -- the node ID to find sensors for, an integer.
    """
    try:
        assert type(node) == int
    except AssertionError as e:
        raise TypeError(f"node must be an integer (not {type(node)})") from e
    db_session = session()
    try:
        query = db_session.query(Nodes).filter(Nodes.ID == node).one()
    except NoResultFound as e:
        raise NoResultFound(f"node ID 0x{node:02x} not found in the database") from e
    return (x.ID for x in query.node_sensors)


def get_node_data(node=None):
    """Return all the data for a given node ID.

    Arguments:
        node -- node ID whose data is to be returned, an integer
    Returns:
        dict {'Node_ID': node_data.ID, 'Name': node_data.Name, 'Location': node_data.Location}
    """
    node_data = _get_node_or_sensor(search_term=node, table="node")
    return {
        "Node_ID": node_data.ID,
        "Name": node_data.Name,
        "Location": node_data.Location,
    }


def get_sensor_data(sensor=None):
    """Return all the data for a given sensor ID

    Arguments:
        sensor -- sensor ID whose data is to be returned, an integer
    Returns:
        {'Sensor_ID': sensor_data.ID, 'Node_ID': sensor_data.Node_ID,
            'Name': sensor_data.Name, 'Quantity': sensor_data.Quantity}
    """
    sensor_data = _get_node_or_sensor(search_term=sensor, table="sensor")
    return {
        "Sensor_ID": sensor_data.ID,
        "Node_ID": sensor_data.Node_ID,
        "Name": sensor_data.Name,
        "Quantity": sensor_data.Quantity,
    }
