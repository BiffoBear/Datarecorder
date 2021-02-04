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
import urllib.error.HTTPError as HTTPError

logger = logging.getLogger(__name__)

event_queue = queue.Queue()
event_actions = {0x05: {0x00: {"url": "http://google.com", "delay": 0}}}


def read_event_queue_handle_event():
    """Take events from the queue and act on them."""
    logger.debug("read_event_queue_handle_event called")
    global event_queue
    try:
        event = event_queue.get()
        event_action = event_actions[event["node"]["code"]]
        if event_action["delay"]:
            time.sleep(event_action["delay"])
        with urllib.request.urlopen(event_action["url"]) as response:
            if response.status != 200:
                raise HTTPError("Bad response from server")
    except queue.Empty:
        logger.error("Event thread called with empty queue")
    except KeyError:
        logger.error(
            "Event 0x%02x from node 0x%02X} does not exist",
            event["code"],
            event["node"],
        )
    except HTTPError:
        logger.error("Bad response from server")
    finally:
        event_queue.task_done()


def write_event_to_queue(event=None):
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
