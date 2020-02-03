#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adds a node to the datadase Nodes table.

Dependencies:
    database.database.py

Postional Arguments:
    id -- id of the new node, an unique integer in range 0-254
    name -- name of the new node, an unique string'
    location -- location of the node, a string
    -h --help -- displays help for the command

Returns:
    Writes the result of the operation to stdout"""

import argparse


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='commands to add nodes and display information about nodes')
parser_list = subparsers.add_parser('list', help='list all nodes')
parser_list.set_defaults(func=list_nodes)
parser_get = subparsers.add_parser('get', help='display information for the node')
parser_get.add_argument('id', type=int, help='id for the node to display, an integer in range 0-254')

parser.parse_args(['list'])