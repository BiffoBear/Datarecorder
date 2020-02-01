#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse


def high_lite_existing_things(thing, existing_things):
    if thing in existing_things:
        return f'\x1b[1m{thing:02x} \x1b[0m'  # Bold text
    return f'\x1b[90m{thing:02x} \x1b[0m'  # Dim text


def print_existing_things(thing_name='Your name here', existing_things=[]):
    if not existing_things:
        return f'No existing {thing_name}s in database'
    print_items = [f'\x1b[1mExisting {thing_name.title()}s\x1b[0m\n']
    for i in range(255):
        if i % 16 == 0:
            print_items.append('\n')
        print_items.append(high_lite_existing_things(i, existing_things))
    print_items.append('\n\n')
    string_to_print = ''.join(print_items)
    return string_to_print

