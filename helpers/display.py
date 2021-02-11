"""Writes messages to a small adafruit.com OLED display over an I2C bus."""
import threading
import queue
from collections import deque
from PIL import Image, ImageDraw, ImageFont

message_queue = queue.Queue(maxsize=100)


class Display:
    """Updates screen line buffer and writes to the display."""

    def __init__(self):
        self._screen_line_buffer = deque([], maxlen=5)
        self._LINE_MAXLEN = 20
        self._OLED_WIDTH = 128
        self._OLED_HEIGHT = 64
        self._COLOUR_DEPTH = "1"
        self._image = Image.new(self._COLOUR_DEPTH, (self._OLED_WIDTH, self._OLED_HEIGHT))
        
    def _write_to_buffer(self, *, line=""):
        if len(line) > self._LINE_MAXLEN:
            line = "".join([line[:self._LINE_MAXLEN - 1], "*"])
            # TODO: logging warning line too long.
        self._screen_line_buffer.append(line)

    def _line_buffer_to_text(self):
        return "\n".join(list(self._screen_line_buffer))
