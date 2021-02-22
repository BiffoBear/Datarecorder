"""Writes messages to a small adafruit.com OLED display over an I2C bus."""
import threading
import queue
from collections import deque
import board
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

# Use a queue with an arbitrarily large maxsize to stop memory issues if queue not read.
message_queue = queue.Queue(maxsize=100)


class Display:
    """Instantiates an Adafruit 128 x 64 OLED display and writes short text messages to it."""

    def __init__(self):
        # deque with maxlen = 4 to automatically keep the last 4 lines of text
        self._screen_line_buffer = deque([], maxlen=4)
        self._line_maxlen = 20  # Maximum characters per line
        self._oled_width = 128
        self._oled_height = 64
        self._colour_depth = "1"
        self._image = Image.new(
            self._colour_depth, (self._oled_width, self._oled_height)
        )
        self._font = ImageFont.load_default()
        # If the !2C bus isn't available set it to None
        try:
            self._i2c = board.I2C()
        except ValueError:
            self._i2c = None
            # TODO: logging warning
        self._reset_pin = digitalio.DigitalInOut(board.D16)
        # If the OLED can't be initialized, set it to None. Messages will then be ignored
        try:
            self._ssd = adafruit_ssd1306.SSD1306_I2C(
                self._oled_width,
                self._oled_height,
                self._i2c,
                addr=0x3D,
                reset=self._reset_pin,
            )
        except (ValueError, AttributeError):
            self._ssd = None

    def _write_to_buffer(self, *, line):
        """Truncate a string if needed, then write it to the buffer."""
        if len(line) > self._line_maxlen:
            line = "".join([line[: self._line_maxlen - 3], "..."])
            # TODO: logging warning line too long.
        self._screen_line_buffer.append(line)

    def _line_buffer_to_text(self):
        """Convert the strings in the buffer to a block of text."""
        return "\n".join(list(self._screen_line_buffer))

    def _draw_text_to_image(self, *, text):
        """Clear the image then write a block of text."""
        draw = ImageDraw.Draw(self._image)
        draw.rectangle((0, 0, self._oled_width, self._oled_height), outline=0, fill=0)
        draw.text((1, 1), text, font=self._font, fill=255)

    def _update_screen(self):
        """Update the OLED display with the current image."""
        self._ssd.image(self._image)
        self._ssd.show()

    def message(self, text):
        """Process a message if the OLED display exists."""
        if self._ssd is None:
            return
        try:  # Keep thread running continuously as exceptions are not critical.
            self._write_to_buffer(line=text)
            self._draw_text_to_image(text=self._line_buffer_to_text())
            self._update_screen()
        except:  # pylint: disable=bare-except
            pass


def oled_message(text):
    """Write a message to the message queue. This function is called by other
    modules to output a single line message to the OLED display.

    :param str text: The message to be displayed. Should not be longer than
        _LINE_MAX_LEN in the Display class. Longer messages will be truncated.
    """
    try:
        message_queue.put_nowait(text)
    except queue.Full:
        # TODO: logging warning that queue is full
        pass


def thread_loop(screen, msg_queue):
    """Monitor the message queue for new messages. Run by the thread."""
    while True:
        text = msg_queue.get()
        screen.message(text)
        msg_queue.task_done()


def init():
    """Instatiate a display then pass the display and the message queue to a new
    thread object. Finally, start the thread.

    .. note:: This function should be called before any messages are written to
    the queue. However, the queue has a maxlen set and put_nowait is used so
    that memory usage is limited should init fail.
    """
    oled = Display()
    message_thread = threading.Thread(
        target=thread_loop, args=(oled, message_queue), daemon=True, name="message"
    )
    message_thread.start()


def shutdown():
    """Write a shutdown message and wait for all queued messages to be processed.

    .. note:: This function should be called before terminating the main thread.
    """
    # TDDO: logging warning that oled shutdown called
    for _ in range(3):
        oled_message(" ")
    oled_message("OLED shut down")
    message_queue.join()
    # TODO: logging warning oled shutdown complete
