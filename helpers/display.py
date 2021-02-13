"""Writes messages to a small adafruit.com OLED display over an I2C bus."""
import threading
import queue
import board
import digitalio
import adafruit_ssd1306
from collections import deque
from PIL import Image, ImageDraw, ImageFont

message_queue = queue.Queue(maxsize=100)


class Display:
    """Updates screen line buffer and writes to the display."""

    def __init__(self):
        self._screen_line_buffer = deque([], maxlen=4)
        self._LINE_MAXLEN = 20
        self._OLED_WIDTH = 128
        self._OLED_HEIGHT = 64
        self._COLOUR_DEPTH = "1"
        self._image = Image.new(self._COLOUR_DEPTH, (self._OLED_WIDTH, self._OLED_HEIGHT))
        self._font = ImageFont.load_default()
        try:
            self._i2c = board.I2C()
        except ValueError:
            self._i2c = None
            # TODO: logging warning
        self._reset_pin = digitalio.DigitalInOut(board.D17)
        try:
            self._ssd = adafruit_ssd1306.SSD1306_I2C(self._OLED_WIDTH, self._OLED_HEIGHT, self._i2c, addr=0x3d, reset=self._reset_pin)
        except (ValueError, AttributeError):
            self._ssd = None

    def _write_to_buffer(self, *, line):
        if len(line) > self._LINE_MAXLEN:
            line = "".join([line[:self._LINE_MAXLEN - 1], "*"])
            # TODO: logging warning line too long.
        self._screen_line_buffer.append(line)

    def _line_buffer_to_text(self):
        return "\n".join(list(self._screen_line_buffer))

    def _draw_text_to_image(self, *, text):
        draw = ImageDraw.Draw(self._image)
        draw.text((1, 1), text, font=self._font, fill=255)

    def _update_screen(self):
        self._ssd.image(self._image)
        self._ssd.show()

    def message(self, text):
        if self._ssd is None:
            return
        try:
            self._write_to_buffer(line=text)
            self._draw_text_to_image(text=self._line_buffer_to_text())
            self._update_screen()
        except:  # Keep the thread running if the OLED fails as it's not critical.
            pass


def oled_message(text):
    try:
        message_queue.put_nowait(text)
    except queue.Full:
        # TODO: logging warning that queue is full
        pass


def thread_loop(screen, msg_queue):
    while True:
        text = msg_queue.get()
        screen.message(text)
        msg_queue.task_done()


def init():
    oled = Display()
    message_thread = threading.Thread(target=thread_loop, args=(oled, message_queue), daemon=True, name="message")
    message_thread.start()
    
    
def shutdown():
    # TDDO: logging warning that oled shutdown called
    message_queue.join()
    # TODO: logging warning oled shutdown complete
