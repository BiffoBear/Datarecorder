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

logger = logging.getLogger(__name__)

GATE_OPEN = (
    "https://192.168.1.10:5001/webapi/entry.cgi?api=SYNO.SurveillanceStation."
    'Webhook&method="Incoming"&version=1&'
    "token=BQdC2UYiqxqP0zEUZ9UXh3uvhPFZCqLls8YcRzk1o5TFj6mx9FFPzm9Tm7LUxwhH"
)
GATE_CLOSE = (
    "https://192.168.1.10:5001/webapi/entry.cgi?api=SYNO.SurveillanceStation."
    'Webhook&method="Incoming"&version=1&'
    "token=A0Wngnir5CqVDnS8M1fDIgWTZviD2FjrJ2caEJZImqjXHqOGuZQz14OOOcn2wFXH"
)
event_queue = queue.Queue()
event_actions = {
    0x05: {0x00: {"url": GATE_OPEN, "delay": 0}, 0x01: {"url": GATE_CLOSE, "delay": 0}}
}


def _decode_register(register):
    """Splits the register bytes into a list of event codes."""
    logger.debug("_decode_register called")
    status_codes = []
    for bit in range(16):
        if register >> bit & 0x0001:
            status_codes.append(bit)
    return status_codes


def read_event_queue_handle_event():
    """Take events from the queue and act on them."""
    logger.debug("read_event_queue_handle_event called")
    global event_queue
    try:
        events = event_queue.get()
        logger.debug("Processing...")

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
                logger.debug("delaying...")
                time.sleep(event_action["delay"])
                logger.debug("continuing...")
            with urllib.request.urlopen(event_action["url"]) as response:
                if response.status != 200:
                    raise IOError("Bad response from server")
        except KeyError:
            logger.error(
                "Event 0x%02x from node 0x%02X} does not exist",
                event,
                node_id,
            )
        except IOError:
            logger.error("Bad response from server")
    event_queue.task_done()


def write_event_to_queue(events):
    """Add an event to the event queue."""
    logger.debug("write_event_to_queue called")
    try:
        event_queue.put_nowait(events)
        logger.debug(
            "Added events to queue. 0x%02x events in queue", event_queue.qsize()
        )
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
