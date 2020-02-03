#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from database import database


def setup_node_argparse():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='commands to add nodes and display information about nodes')
    parser_list = subparsers.add_parser('list', help='list all existing nodes')
    parser_list.set_defaults(func=list_nodes)
    parser_get = subparsers.add_parser('show', help='display information for the node')
    parser_get.add_argument('id', type=int, help='id for the node to display, an integer in range 0-254')
    parser_get.set_defaults(func=show_node_details)
    parser_add = subparsers.add_parser('add', help='display information for the node')
    parser_add.set_defaults(func=add_node)
    parser_add.add_argument('id', type=int, help='id for the node to add, an integer in range 0-254')
    parser_add.add_argument('name', help='name for the node to add')
    parser_add.add_argument('location', help='location for the node to add')
    return parser


def list_nodes():
    nodes_to_list = database.get_all_node_ids()
    text_to_print = _layout_existing_things(thing_name='node', existing_things=nodes_to_list)
    print(text_to_print)

def show_node_details(node_id=None):
    # TODO: Dummy for testing argparse setup. Implement later
    pass


def add_node(node_id=None, name=None, location=None):
    # TODO: Dummy for testing argparse setup. Implement later
    pass


def _high_lite_existing_things(thing, existing_things):
    if thing in existing_things:
        return f'\x1b[1m{thing:02x} \x1b[0m'  # Bold text
    return f'\x1b[90m{thing:02x} \x1b[0m'  # Dim text


def _layout_existing_things(thing_name=None, existing_things=None):
    if not existing_things:
        return f'No existing {thing_name}s in database'
    print_items = [f'\x1b[1mExisting {thing_name.title()}s\x1b[0m\n']
    for i in range(255):
        if i % 16 == 0:
            print_items.append('\n')
        print_items.append(_high_lite_existing_things(i, existing_things))
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
    return ''.join(print_items)
