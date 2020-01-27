#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 12:30:25 2019

@author: martinstephens
"""
import logging
import logging.handlers
# noinspection PyPackageRequirements
import board
import time
import busio
import digitalio
# noinspection PyPep8Naming
import RPi.GPIO as rpigpio
import adafruit_rfm69
from . import _oleddisplay, _dataprocessing, database
from __config__ import DB_URL, RFM69_INTERRUPT_PIN, FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL
from radiohelper.radiohelper import RFM69_ENCRYPTION_KEY

logger = logging.getLogger(__name__)
logger.setLevel(FILE_DEBUG_LEVEL)


# noinspection PyUnusedLocal
def rfm69_callback(rfm69_irq):
    logger.debug('rfm69_callback called')
    if radio.payload_ready:
        packet = radio.receive(timeout=None)
        if packet is not None:
            _dataprocessing.radio_q.put(packet)


def initialize_gpio_interrupt(rfm69_g0):
    logger.debug('initialize_gpio_interrupt called')
    rpigpio.setmode(rpigpio.BCM)
    rpigpio.setup(rfm69_g0, rpigpio.IN, pull_up_down=rpigpio.PUD_DOWN)
    rpigpio.remove_event_detect(rfm69_g0)
    rpigpio.add_event_detect(rfm69_g0, rpigpio.RISING)
    rpigpio.add_event_callback(rfm69_g0, rfm69_callback)


def initialize_logging(file_logging_level, console_logging_level):
    logging.basicConfig(level=console_logging_level,
                        format='%(name)-14s: %(levelname)-8s %(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        )
    file_handler = logging.handlers.RotatingFileHandler('/tmp/datarecorder.log', maxBytes=1000000, backupCount=5)
    file_handler_formatter = logging.Formatter('%(asctime)s: %(name)-14s: %(levelname)-8s: %(message)s')
    file_handler.setFormatter(file_handler_formatter)
    file_handler.setLevel(file_logging_level)
    logging.getLogger('').addHandler(file_handler)


def initialize_rfm69():
    logger.debug('initialize_rfm69 called')
    cs = digitalio.DigitalInOut(board.CE1)
    reset = digitalio.DigitalInOut(board.D25)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    try:
        rfm69 = adafruit_rfm69.RFM69(spi, cs, reset, 433)
        rfm69.encryption_key = RFM69_ENCRYPTION_KEY
        logger.info(f'RFM69 radio initialized successfully')
        _oleddisplay.write_message_to_queue(f'Radio initialized OK')
        return rfm69
    except RuntimeError as error:
        logger.critical(f'RFM69 radio failed to initialize with RuntimeError')
        raise error


def initialize_database(url_db):
    logger.debug('initialize_database called')
    database.initialize_database(url_db)


def initialize_processing_thread():
    logger.debug('initialize_processing_thread called')
    _dataprocessing.init_data_processing_thread()


def start_up(db_url=None, pi_irq_pin=None, logging_levels=(FILE_DEBUG_LEVEL, CONSOLE_DEBUG_LEVEL)):
    logger.debug('start_up called')
    initialize_logging(*logging_levels)
    initialize_database(db_url)
    initialize_processing_thread()
    rfm69 = initialize_rfm69()
    initialize_gpio_interrupt(pi_irq_pin)
    _oleddisplay.init_display_thread()
    rfm69.listen()
    logger.info('Listening for radio data…')
    return rfm69


def shut_down(pi_irq_pin=RFM69_INTERRUPT_PIN):
    logger.info('shut_down_called')
    rpigpio.remove_event_detect(pi_irq_pin)
    _dataprocessing.radio_q.join()
    _oleddisplay.shut_down()
    # tests.unittest_helper.kill_database()


if __name__ == '__main__':
    radio = start_up(db_url=DB_URL, pi_irq_pin=RFM69_INTERRUPT_PIN)
    finish_time = time.time() + 60
    try:
        # while time.time() < finish_time:
        while True:
            time.sleep(0.1)
    except Exception as e:
        raise e
    finally:
        shut_down()
