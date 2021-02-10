"""Writes messages to a small adafruit.com OLED display over an I2C bus."""
import threading
import queue
from collections import deque

message_queue = queue.Queue()


class Display:
    """Updates screen line buffer and writes to the display."""
    pass
    def __init__(self):
        self._screen_line_buffer = deque([], maxlen=5)
        
    def _write_to_buffer(self, *, line=""):
        self._screen_line_buffer.append(line)
        