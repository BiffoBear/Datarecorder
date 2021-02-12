import pytest
from unittest.mock import Mock
import queue
import PIL
import board
import digitalio
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

    @pytest.mark.parametrize("side_effect, result", [("i2c object", "i2c object"), (ValueError, None)])        
    def test_init_i2c_is_bus_object_or_none_if_init_error(self, mocker, side_effect, result):
        mock_i2c = mocker.patch.object(board, "I2C", autospec=True, side_effect=[side_effect])
        oled = display.Display()
        mock_i2c.assert_called_once()
        assert oled._i2c == result
        
    def test_reset_pin_is_the_correct_type(self):
        oled = display.Display()
        assert isinstance(oled._reset_pin, digitalio.DigitalInOut)
        
    def test_reset_pin_is_set_to_gpio_17(self, mocker):
        mock_digiio = mocker.patch.object(digitalio, "DigitalInOut")
        oled = display.Display()
        mock_digiio.assert_called_once_with(board.D17)

    @pytest.mark.parametrize("side_effect, result", [("ssd object", "ssd object"), (ValueError, None), (AttributeError, None)])
    def test_ssd_is_ssd1306_object_or_none_if_init_fails(self, mocker, side_effect, result):
        mock_i2c = mocker.patch.object(board, "I2C", autospec=True, side_effect=["I2C"])
        mock_ssd1306 = mocker.patch.object(display.adafruit_ssd1306, "SSD1306_I2C", side_effect=[side_effect])
        oled = display.Display()
        mock_ssd1306.assert_called_once_with(oled._OLED_WIDTH, oled._OLED_HEIGHT, oled._i2c, addr=0x3d, reset=oled._reset_pin)
        assert oled._ssd == result
        
    def test_update_screen_calls_ssd_image_image_and_ssd_image_show(self, mocker):
        mock_i2c = mocker.patch.object(board, "I2C", autospec=True, side_effect=["I2C"])
        mock_ssd1306 = mocker.patch.object(display.adafruit_ssd1306, "SSD1306_I2C", side_effect=["SSD1306"])
        oled = display.Display()
        oled._ssd = Mock()
        oled._update_screen()
        oled._ssd.image.assert_called_once_with(oled._image)
        oled._ssd.show.assert_called_once

    @pytest.mark.parametrize("text,block", [("Hello World", "Text block1"), ("Farewell", "Text Block2")])
    def test_message_calls_correct_functions(self, mocker, text, block):
        oled = display.Display()
        mock_write_line_to_buffer = mocker.patch.object(display.Display, "_write_to_buffer", autospec=True)
        mock_line_buffer_to_text = mocker.patch.object(display.Display, "_line_buffer_to_text", autospec=True, side_effect=[block])
        mock_draw_text_to_image = mocker.patch.object(display.Display, "_draw_text_to_image", autospec=True)
        mock_update_screen = mocker.patch.object(display.Display, "_update_screen")
        oled.message(text=text)
        mock_write_line_to_buffer.assert_called_once_with(oled, line=text)
        mock_line_buffer_to_text.assert_called_once()
        mock_draw_text_to_image.assert_called_once_with(oled, text=block)
        mock_update_screen.assert_called_once()
