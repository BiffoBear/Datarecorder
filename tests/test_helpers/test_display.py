import pytest
from unittest.mock import call
import queue
import PIL
import board
import adafruit_ssd1306
from collections import deque
from helpers import display

def test_display_module_has_a_queue_maxsize_100():
    assert isinstance(display.message_queue, queue.Queue)
    try:
        for item in range(100):
            display.message_queue.put_nowait(item)
        with pytest.raises(queue.Full):
            display.message_queue.put_nowait(101)
    finally:
        while not display.message_queue.empty():
            display.message_queue.get()
    
def test_write_to_queue_and_queue_is_fifo():
    assert display.message_queue.empty()
    display.message_queue.put("Hello World")
    display.message_queue.put("Byeee!")
    assert not display.message_queue.empty()
    assert display.message_queue.get() == "Hello World"
    assert display.message_queue.get() == "Byeee!"


class TestDisplayClass:
    
    def test_display_class_exists_and_has_a_message_buffer(self):
        oled = display.Display()
        assert oled._screen_line_buffer.maxlen == 5
  
    def test_write_to_line_buffer_appends_on_the_right(self):
        oled = display.Display()
        [oled._write_to_buffer(line=text) for text in ["1", "2"]]
        assert oled._screen_line_buffer == deque(["1", "2"])

    def test_write_to_line_buffer_truncates_long_lines_using_maxlen(self):
        oled = display.Display()
        assert oled._LINE_MAXLEN == 20
        test_lines = ["", "A" * 5, "B" * oled._LINE_MAXLEN, "C" * (oled._LINE_MAXLEN + 1)]
        [oled._write_to_buffer(line=line) for line in test_lines]
        expected_result = deque(test_lines[:-1])
        expected_result.append("".join(["C" * (oled._LINE_MAXLEN - 1), "*"]))
        assert oled._screen_line_buffer == expected_result
        oled._LINE_MAXLEN = 18
        oled._write_to_buffer(line="D" * 20)
        assert oled._screen_line_buffer.pop() == "".join(["D" * 17, "*"])

    def test_line_buffer_to_text(self):
        oled = display.Display()
        test_lines = ["Test 1", "Test 2", "Test 3", "Test 4", "Test 5"]
        [oled._screen_line_buffer.append(line) for line in test_lines]
        expected_result = (
            "Test 1\n"
            "Test 2\n"
            "Test 3\n"
            "Test 4\n"
            "Test 5"
        )
        assert oled._line_buffer_to_text() == expected_result

    def test_display_has_settings_for_pil(self):
        oled = display.Display()
        assert oled._OLED_WIDTH == 128
        assert oled._OLED_HEIGHT == 64
        assert oled._COLOUR_DEPTH == "1"
        assert isinstance(oled._font, PIL.ImageFont.ImageFont)

    def test_pil_image_is_called_with_correct_args(self, mocker):
        oled = display.Display()
        assert isinstance(oled._image, PIL.Image.Image)
        assert oled._image.mode == oled._COLOUR_DEPTH
        assert oled._image.size == (oled._OLED_WIDTH, oled._OLED_HEIGHT)

    def test_draw_text_on_pil_image(self):
        oled = display.Display()
        test_image = PIL.Image.new("1", (128, 64))
        font = PIL.ImageFont.load_default()
        draw = PIL.ImageDraw.Draw(test_image)
        draw.text((1, 1), "Hello World!", font=font, fill=255)
        oled._draw_text_to_image(text="Hello World!")
        assert oled._image.getdata == test_image.getdata
        
        