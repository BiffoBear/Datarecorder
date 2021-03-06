#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
global_display = None


def initialize_i2c():
    try:
        logger.debug('initialize_i2c called')
        return busio.I2C(board.SCL, board.SDA)
    except ValueError:
        logger.error('I2C bus failed to initialize. Check that I2C is enabled')
        return None


def initialize_oled(i2c_bus, reset_pin=None):
    logger.debug('initialize_oled called')
    try:
        oled = adafruit_ssd1306.SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c_bus, addr=0x3d, reset=reset_pin)
        logger.info('OLED display initialized successfully')
        return oled
    except ValueError:
        logger.error('OLED display failed to initialize. Check that wiring is correct')
    except AttributeError:
        logger.error('OLED display failed to initialize. No I2C bus found')
    return None


def setup_hardware_oled():
    logger.debug('setup_hardware_oled called')
    i2c = initialize_i2c()
    reset = digitalio.DigitalInOut(board.D17)
    return initialize_oled(i2c, reset_pin=reset)


def setup_display_dict():
    logger.debug('setup_display_dict called')
    oled = setup_hardware_oled()
    image = Image.new('1', (DISPLAY_WIDTH, DISPLAY_HEIGHT))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    lines = deque([])
    return {'oled': oled, 'image': image, 'draw': draw, 'font': font, 'lines': lines}


def clear_display(display):
    logger.debug('clear_display called')
    display['draw'].rectangle((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), outline=0, fill=0)
    return display


def write_text_to_display(display=None, coords=(0, 0), text=''):
    logger.debug('write_text_to_display called')
    display['draw'].text(coords, text, font=display['font'], fill=255)
    return display


def show_display(display=None):
    logger.debug('show_display called')
    display['oled'].image(display['image'])
    display['oled'].show()


def add_screen_line(display=None, text=''):
    logger.debug('add_screen_line called')
    lines = display['lines']
    lines.append(text)
    if len(lines) == 6:
        lines.popleft()
    return display


def draw_lines(display=None):
    logger.debug('draw_lines called')
    line_coords = ((1, 1), (1, 13), (1, 25), (1, 37), (1, 49))
    display = clear_display(display)
    for line, coord in zip(display['lines'], line_coords):
        display = write_text_to_display(display=display, coords=coord, text=line)
    show_display(display)
    return display


def read_message_queue_write_to_display(display=None):
    logger.debug('read_message_queue_write_to_display called')
    global message_queue
    try:
        text = message_queue.get()
        display = add_screen_line(display=display, text=text)
        if display['oled'] is not None:
            display = draw_lines(display=display)
    except queue.Empty:
        logger.error('Display thread called with empty queue')
    finally:
        message_queue.task_done()
    return display


def write_message_to_queue(message_text=''):
    logger.debug('write_message_to_queue called')
    try:
        message_queue.put_nowait(message_text)
    except queue.Full:
        pass


# noinspection PyTypeChecker
def shut_down():
    logger.info(f'shut_down called')
    message_queue.join()
    try:
        clear_display(global_display)
        show_display(global_display)
    except AttributeError:
        pass
    logger.warning('Data recorder shutdown')


def init_display_thread():
    logger.debug(f'init_display_thread called')
    global global_display
    global_display = setup_display_dict()
    message_thread = threading.Thread(target=loop_read_message_queue)
    message_thread.daemon = True
    message_thread.start()
    return message_thread


def loop_read_message_queue():
    logger.debug(f'loop_read_message_queue called')
    global global_display
    while True:
        global_display = read_message_queue_write_to_display(display=global_display)
