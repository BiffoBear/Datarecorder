#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adds, lists and shows details of nodes

usage: nodes.py [-h] {list,show,add} ...

    positional arguments:
      {list,show,add}  commands to add nodes and display information about nodes
        list           list all existing nodes
        show           display information for the node
        add            add a node to the database

    optional arguments:
      -h, --help       show this help message and exit

usage: nodes.py list [-h]

    optional arguments:
      -h, --help  show this help message and exit

usage: nodes.py show [-h] id

    positional arguments:
      id          id for the node to display, an integer in range 0-254

    optional arguments:
      -h, --help  show this help message and exit

usage: nodes.py add [-h] id name location

    positional arguments:
      id          id for the node to add, an integer in range 0-254
      name        name for the node to add
      location    location for the node to add

    optional arguments:
      -h, --help  show this help message and exit

Returns:
    Writes the result of the operation to stdout
"""

# Apparently unused imports are called by args.func(args)
from commandline import setup_node_argparse, list_nodes, add_node_to_database, show_node_details
parser = setup_node_argparse()
args = parser.parse_args()
args.func(args)
