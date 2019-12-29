#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 12:30:25 2019

@author: martinstephens
"""
import logging
import board
import time
import busio
import digitalio
import RPi.GPIO as rpigpio
import adafruit_rfm69
import database
import dataprocessing
from __config__ import DB_URL, RFM69_INTERRUPT_PIN, DEBUG_LEVEl
import tests.unittest_helper

logger = logging.getLogger(__name__)
logger.setLevel(DEBUG_LEVEl)


def rfm69_callback(rfm69_irq):
    logger.debug('rfm69_callback called')
    if radio.payload_ready:
        packet = radio.receive(timeout=None)
        if packet is not None:
            dataprocessing.radio_q.put(packet)


def initialize_gpio_interrupt(rfm69_g0):
    logger.debug('initialize_gpio_interrupt')
    rpigpio.setmode(rpigpio.BCM)
    rpigpio.setup(rfm69_g0, rpigpio.IN, pull_up_down=rpigpio.PUD_DOWN)
    rpigpio.remove_event_detect(rfm69_g0)
    rpigpio.add_event_detect(rfm69_g0, rpigpio.RISING)
    rpigpio.add_event_callback(rfm69_g0, rfm69_callback)


def initialize_logging():
    # create file handler which logs even debug messages
    # set up logging to file - see previous section for more details
    # logging.basicConfig(level=logging.DEBUG,
    #                     format='%(asctime)s: %(name)-12s: %(levelname)-8s: %(message)s',
    #                     datefmt='%y-%m-%d %H:%M',
    #                     filename='testing.log',  # '/temp/myapp.log',
    #                     filemode='w')
    # # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)


def initialize_rfm69():
    cs = digitalio.DigitalInOut(board.CE1)
    reset = digitalio.DigitalInOut(board.D25)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    try:
        rfm69 = adafruit_rfm69.RFM69(spi, cs, reset, 433.0)
        rfm69.encryption_key = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        logger.info(f'RFM69 radio initialized successfully')
        return rfm69
    except RuntimeError as error:
        logger.critical(f'RFM69 radio failed to initialize with RuntimeError')
        raise error


def initialize_database(url_db):
    database.initialize_database(DB_URL)


def initialize_processing_thread():
    dataprocessing.init_data_processing_thread()


def start_up(db_url=None, pi_irq_pin=None):
    initialize_logging()
    initialize_database(db_url)
    initialize_processing_thread()
    rfm69 = initialize_rfm69()
    initialize_gpio_interrupt(pi_irq_pin)
    rfm69.listen()
    logger.info('Listening for radio data…')
    return rfm69


def shut_down(pi_irq_pin=24):
    logger.info('shutdown_called')
    rpigpio.remove_event_detect(pi_irq_pin)
    dataprocessing.radio_q.join()
    print(f'Packets written to db: {tests.unittest_helper.count_all_records() // 9}')
    tests.unittest_helper.kill_database()


if __name__ == '__main__':
    radio = start_up(db_url=DB_URL, pi_irq_pin=RFM69_INTERRUPT_PIN)
    finish_time = time.time() + 3600
    try:
        while time.time() < finish_time:
            time.sleep(0.1)
    except Exception as e:
        raise e
    finally:
        shut_down()
