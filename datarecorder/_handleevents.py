#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  3 09:00:00 2021

@author: martinstephens
"""
import logging
import threading
import time
import queue
import urllib.request
from urllib.error import HTTPError

logger = logging.getLogger(__name__)

event_queue = queue.Queue()
event_actions = {0x05: {0x00: {"url": "http://google.com", "delay": 0}}}


def _decode_register(register):
    status_codes = []
    for bit in range(16):
        if bit & 0x0001:
            status_codes.append(bit)
        register = register >> 1
    return status_codes


def read_event_queue_handle_event():
    """Take events from the queue and act on them."""
    logger.debug("read_event_queue_handle_event called")
    global event_queue
    try:
        events = event_queue.get()
    except queue.Empty:
        logger.error("Event thread called with empty queue")
        event_queue.task_done()
        return
    node_id = events["node_id"]
    decoded_events = _decode_register(events["status_register"])
    for event in decoded_events:
        try:
            event_action = event_actions[node_id][event]
            if event_action["delay"]:
                time.sleep(event_action["delay"])
            with urllib.request.urlopen(event_action["url"]) as response:
                if response.status != 200:
                    raise HTTPError("Bad response from server")
        except KeyError:
            logger.error(
                "Event 0x%02x from node 0x%02X} does not exist",
                event["code"],
                event["node"],
            )
        except HTTPError:
            logger.error("Bad response from server")
    event_queue.task_done()


def write_event_to_queue(events=None):
    """Add an event to the event queue."""
    logger.debug("write_event_to_queue called")
    try:
        event_queue.put_nowait(event)
    except queue.Full:
        pass


def init_event_thread():
    """Initialize the event processing thread."""
    logger.debug("init_event_thread called")
    event_thread = threading.Thread(target=loop_read_event_queue)
    event_thread.daemon = True
    event_thread.start()
    return event_thread


def loop_read_event_queue():
    """Main loop to monitor the event queue"""
    logger.debug("loop_read_event_queue called")
    while True:
        read_event_queue_handle_event()
