#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from sqlalchemy.orm.exc import NoResultFound
from database import database
from __config__ import DB_URL


def _layout_existing_things(thing_name=None, existing_things=None):
    if not existing_things:
        return f"No existing {thing_name}s in database"
    print_items = [f"Existing {thing_name.title()}s\n"]
    for index, thing in enumerate(existing_things):
        if index % 16 == 0:
            print_items.append('\n')
        print_items.append(f"{thing:02x} ")
    print_items.append('\n\n')
    string_to_print = ''.join(print_items)
    return string_to_print


def _convert_value_to_string(value):
    if type(value) is int:
        return f'0x{value:02x}'
    return value


def _layout_thing_details(thing_name=None, thing_id=None, thing_data=None):
    print_items = [f'Details for {thing_name} ID {thing_id}:\n\n']
    for key, value in thing_data.items():
        print_items.append(f'{key} -- {_convert_value_to_string(value)}\n')
    print_items.append('\n')
    x = ''.join(print_items)
    return x


def list_nodes(_):
    nodes_to_list = database.get_all_node_ids()
    text_to_print = _layout_existing_things(thing_name='node', existing_things=nodes_to_list)
    print(text_to_print)


def list_sensors(_):
    sensors_to_list = database.get_all_sensor_ids()
    text_to_print = _layout_existing_things(thing_name='sensor', existing_things=sensors_to_list)
    print(text_to_print)


def show_node_details(parsed_args=None):
    try:
        node_details = database.get_node_data(parsed_args.id)
        text_to_print = _layout_thing_details(thing_name='node', thing_id=parsed_args.id, thing_data=node_details)
    except NoResultFound as e:
        text_to_print = e.args[0].capitalize()
    print(text_to_print)


def show_sensor_details(parsed_args=None):
    try:
        sensor_details = database.get_sensor_data(parsed_args.id)
        text_to_print = _layout_thing_details(thing_name='sensor', thing_id=parsed_args.id, thing_data=sensor_details)
    except NoResultFound as e:
        text_to_print = e.args[0].capitalize()
    print(text_to_print)


def add_node_to_database(parsed_args):
    try:
        database.add_node(node_id=parsed_args.id, name=parsed_args.name, location=parsed_args.location)
        print(f'Node ID 0x{parsed_args.id:02x} created in database\n')
    except ValueError as e:
        print(f'Unable to create node ID 0x{parsed_args.id:02x} -- {e.args[0]}\n')
    except TypeError as e:
        print(f'Unable to create node ID 0x{parsed_args.id:02x} -- {e.args[0]}\n')


def add_sensor_to_database(parsed_args):
    try:
        database.add_sensor(sensor_id=parsed_args.id,
                            node_id=parsed_args.node,
                            name=parsed_args.name,
                            quantity=parsed_args.quantity)
        print(f'Sensor ID 0x{parsed_args.id:02x} created in database\n')
    except ValueError as e:
        print(f'Unable to create sensor ID 0x{parsed_args.id:02x} -- {e.args[0]}\n')
    except TypeError as e:
        print(f'Unable to create sensor ID 0x{parsed_args.id:02x} -- {e.args[0]}\n')


def setup_node_argparse():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='commands to add nodes and display information about nodes')
    parser_list = subparsers.add_parser('list', help='list all existing nodes')
    parser_list.set_defaults(func=list_nodes)
    parser_get = subparsers.add_parser('show', help='display information for the node')
    parser_get.add_argument('id', type=int, help='id for the node to display, an integer in range 0-254')
    parser_get.set_defaults(func=show_node_details)
    parser_add = subparsers.add_parser('add', help='add a node to the database')
    parser_add.set_defaults(func=add_node_to_database)
    parser_add.add_argument('id', type=int, help='id for the node to add, an integer in range 0-254')
    parser_add.add_argument('name', help='name for the node to add')
    parser_add.add_argument('location', help='location for the node to add')
    return parser


def setup_sensor_argparse():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='commands to add sensors and display information about sensors')
    parser_list = subparsers.add_parser('list', help='list all existing sensors')
    parser_list.set_defaults(func=list_sensors)
    parser_get = subparsers.add_parser('show', help='display information for the sensor')
    parser_get.add_argument('id', type=int, help='id for the sensor to display, an integer in range 0-254')
    parser_get.set_defaults(func=show_sensor_details)
    parser_add = subparsers.add_parser('add', help='add a sensor to the database')
    parser_add.set_defaults(func=add_sensor_to_database)
    parser_add.add_argument('id', type=int, help='id for the sensor to add, an integer in range 0-254')
    parser_add.add_argument('node', type = int,
                            help='id for the node of sensor to add, an integer in range 0-254'),
    parser_add.add_argument('name', help='name for the sensor to add')
    parser_add.add_argument('quantity', help='quantity for the sensor to add')
    return parser
