import logging
from collections import deque
import board
import busio
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def initialize_i2c():
    logger.debug('initialize_i2c called')
    return busio.I2C(board.SCL, board.SDA)


def initialize_oled(i2c_bus, reset_pin=None):
    logger.debug('initialize_oled called')
    return adafruit_ssd1306.SSD1306_I2C(128, 64, i2c_bus, addr=0x3d, reset=reset_pin)


def setup():
    logger.debug('setup called')
    try:
        i2c = initialize_i2c()
        reset = digitalio.DigitalInOut(board.D17)
        oled = initialize_oled(i2c, reset)
        image = Image.new('1', (oled.width, oled.height))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        logger.info('OLED display initialized successfully')
        return {'oled': oled, 'image': image, 'draw': draw, 'font': font, }
    except ValueError:
        logger.error('OLED display failed to initialize. Check that I2C bus enabled and wiring is correct')
        return None


def clear_display(display):
    logger.debug('clear_display called')
    display['oled'].fill(0)
    display['oled'].show()
    return display


def write_text_to_display(display=None, coords=(0, 0), text=''):
    logger.debug('write_text_to_display called')
    display['draw'].text(coords, text, font=display['font'], fill=255)
    return display


def show_display(display=None):
    logger.debug('show_display called')
    display['oled'].image(display['image'])
    display['oled'].show()
    return display


def add_screen_line(queue=None, text=''):
    queue.append(text)
    if len(queue) == 6:
        queue.popleft()
    return queue
