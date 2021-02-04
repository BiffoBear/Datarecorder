#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:39:49 2019

@author: martinstephens
"""
import logging
import threading
from collections import deque
import queue
import board
import busio
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from __config__ import DISPLAY_WIDTH, DISPLAY_HEIGHT

logger = logging.getLogger(__name__)

message_queue = queue.Queue()

# Required for multithreading, not a constant.
global_display = None  # pylint: disable=invalid-name


def initialize_i2c():
    """Initialize the I2C bus for RTC and display."""
    try:
        logger.debug("initialize_i2c called")
        return busio.I2C(board.SCL, board.SDA)
    except ValueError:
        logger.error("I2C bus failed to initialize. Check that I2C is enabled")
        return None


def initialize_oled(i2c_bus, reset_pin=None):
    """Attempt to initialize the OLED display."""
    logger.debug("initialize_oled called")
    try:
        oled = adafruit_ssd1306.SSD1306_I2C(
            DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c_bus, addr=0x3D, reset=reset_pin
        )
        logger.info("OLED display initialized successfully")
        return oled
    except ValueError:
        logger.error("OLED display failed to initialize. Check that wiring is correct")
    except AttributeError:
        logger.error("OLED display failed to initialize. No I2C bus found")
    return None


def setup_hardware_oled():
    """Create an instance of the OLED display."""
    logger.debug("setup_hardware_oled called")
    i2c = initialize_i2c()
    reset = digitalio.DigitalInOut(board.D17)
    return initialize_oled(i2c, reset_pin=reset)


def setup_display_dict():
    """Setup everything needed to write to an OLED display."""
    logger.debug("setup_display_dict called")
    oled = setup_hardware_oled()
    image = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    lines = deque([])
    return {"oled": oled, "image": image, "draw": draw, "font": font, "lines": lines}


def clear_display(display):
    """Clear the OLED display."""
    logger.debug("clear_display called")
    display["draw"].rectangle((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), outline=0, fill=0)
    return display


def write_text_to_display(display=None, coords=(0, 0), text=""):
    """Write a message to the OLED display."""
    logger.debug("write_text_to_display called")
    display["draw"].text(coords, text, font=display["font"], fill=255)
    return display


def show_display(display=None):
    """Update OLED display with latest output."""
    logger.debug("show_display called")
    display["oled"].image(display["image"])
    display["oled"].show()


def add_screen_line(display=None, text=""):
    """Add a line to the text buffer and remove the oldest line if required."""
    logger.debug("add_screen_line called")
    lines = display["lines"]
    lines.append(text)
    if len(lines) == 6:
        lines.popleft()
    return display


def draw_lines(display=None):
    """Write the lines of text from the buffer to the OLED display."""
    logger.debug("draw_lines called")
    line_coords = ((1, 1), (1, 13), (1, 25), (1, 37), (1, 49))
    display = clear_display(display)
    for line, coord in zip(display["lines"], line_coords):
        display = write_text_to_display(display=display, coords=coord, text=line)
    show_display(display)
    return display


def display_message_from_queue(display=None):
    """Take a message from the queue and write it to the display."""
    logger.debug("display_message_from_queue called")
    global message_queue  # pylint: disable=invalid-name
    try:
        text = message_queue.get()
        display = add_screen_line(display=display, text=text)
        if display["oled"] is not None:
            display = draw_lines(display=display)
    except queue.Empty:
        logger.error("Display thread called with empty queue")
    finally:
        message_queue.task_done()
    return display


def write_message_to_queue(message_text=""):
    """Called by the main thread to write a text message to the display queue."""
    logger.debug("write_message_to_queue called")
    try:
        message_queue.put_nowait(message_text)
    except queue.Full:
        pass


def shut_down():
    """Shuts down the OLED display and waits for the queue to clear."""
    logger.info("shut_down called")
    message_queue.join()
    try:
        clear_display(global_display)
        show_display(global_display)
    except AttributeError:
        pass
    logger.warning("Data recorder shutdown")


def init_display_thread():
    """Initialize the OLED display thread."""
    logger.debug("init_display_thread called")
    global global_display
    global_display = setup_display_dict()
    message_thread = threading.Thread(target=loop_read_message_queue)
    message_thread.daemon = True
    message_thread.start()
    return message_thread


def loop_read_message_queue():
    """Main loop monitors the OLED display queue."""
    logger.debug("loop_read_message_queue called")
    global global_display
    while True:
        global_display = display_message_from_queue(display=global_display)
