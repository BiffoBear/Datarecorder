"""Writes messages to a small adafruit.com OLED display over an I2C bus."""
import threading
import queue
from collections import deque

message_queue = queue.Queue(maxsize=100)


class Display:
    """Updates screen line buffer and writes to the display."""
    
    def __init__(self):
        self._screen_line_buffer = deque([], maxlen=5)
        self.LINE_MAXLEN = 20
        
    def _write_to_buffer(self, *, line=""):
        if len(line) > self.LINE_MAXLEN:
            line = "".join([line[:self.LINE_MAXLEN - 1], "*"])
            # TODO: logging warning line too long.
        self._screen_line_buffer.append(line)
        
    def _line_buffer_to_text(self):
        return "\n".join(list(self._screen_line_buffer))
