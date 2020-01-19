import logging
import threading
from collections import deque
import queue
import board
import busio
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

message_queue = queue.Queue()
global_lines = deque([])
global_display = None


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
        display = initialize_oled(i2c, reset)
        image = Image.new('1', (display.width, display.height))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        logger.info('OLED display initialized successfully')
        return {'oled': display, 'image': image, 'draw': draw, 'font': font, }
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


def add_screen_line(lines=None, text=''):
    logger.debug('add_screen_line called')
    lines.append(text)
    if len(lines) == 6:
        lines.popleft()
    return lines


def draw_lines(lines=None, display=None):
    logger.debug('draw_lines called')
    line_coords = ((1, 13), (1, 25), (1, 37), (1, 49), (1, 61))
    for line in range(len(lines)):
        write_text_to_display(display=display, coords=line_coords[line], text=lines[line])
    display = show_display(display)
    return display


def read_message_queue_write_to_display(lines=None, display=None):
    logger.debug('read_message_queue_write_to_display called')
    global message_queue
    lines = add_screen_line(lines=lines, text=message_queue.get_nowait())
    display = draw_lines(lines=lines, display=display)
    message_queue.task_done()
    return lines, display


def loop_read_message_queue():
    logger.debug(f'loop_read_message_queue called')
    global global_lines, global_display
    while True:
        global_lines, global_display = read_message_queue_write_to_display(lines=global_lines, display=global_display)


def init_display_thread():
    logger.debug(f'init_display_thread called')
    global global_display
    global_display = setup()
    message_thread = threading.Thread(target=loop_read_message_queue)
    message_thread.daemon = True
    message_thread.start()
    return message_thread
