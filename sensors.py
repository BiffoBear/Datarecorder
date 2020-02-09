#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adds, lists and shows details of sensors

usage: sensors.py [-h] {list,show,add} ...

    positional arguments:
      {list,show,add}  commands to add sensors and display information about
                       sensors
        list           list all existing sensors
        show           display information for the sensor
        add            add a sensor to the database

    optional arguments:
      -h, --help       show this help message and exit

usage: sensors.py list [-h]

    optional arguments:
      -h, --help  show this help message and exit

usage: sensors.py show [-h] id

    positional arguments:
      id          id for the sensor to display, an integer in range 0-254

    optional arguments:
      -h, --help  show this help message and exit

usage: sensors.py add [-h] id node name quantity

    positional arguments:
      id          id for the sensor to add, an integer in range 0-254
      node        id for the node of sensor to add, an integer in range 0-254
      name        name for the sensor to add
      quantity    quantity for the sensor to add

    optional arguments:
     -h, --help  show this help message and exit

Returns:
    Writes the result of the operation to stdout
"""

# Apparently unused imports are called by args.func(args)
from commandline import setup_sensor_argparse, list_sensors, add_sensor_to_database, show_sensor_details
parser = setup_sensor_argparse()
args = parser.parse_args()
args.func(args)
