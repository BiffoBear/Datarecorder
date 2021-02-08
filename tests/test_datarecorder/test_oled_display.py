#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import Mock, call
import threading
from collections import deque
import queue
import PIL
import board
import busio
import adafruit_ssd1306
import datarecorder
from datarecorder import _oleddisplay
from __config__ import DISPLAY_WIDTH, DISPLAY_HEIGHT


class TestDisplayHardwareSetup:
    def test_initialize_i2c_called_with_correct_args(self, mocker):
        mock_busio_i2c = mocker.patch.object(busio, "I2C", autospec=True)
        _oleddisplay.initialize_i2c()
        mock_busio_i2c.assert_called_once_with(board.SCL, board.SDA)

    def test_initialize_i2c_returns_i2c_object_if_successful(self, mocker):
        mock_busio_i2c = mocker.patch.object(busio, "I2C", autospec=True)
        mock_busio_i2c.return_value = "busio.i2c object"
        assert "busio.i2c object" == _oleddisplay.initialize_i2c()

    def test_initialize_i2c_logs_warning_and_returns_none_if_setup_fails(self, mocker):
        mock_busio_i2c = mocker.patch.object(busio, "I2C", autospec=True)
        mock_busio_i2c.side_effect = ValueError
        assert _oleddisplay.initialize_i2c() is None

    def test_initialize_oled_called_with_correct_args(self, mocker):
        mock_oled = mocker.patch.object(adafruit_ssd1306, "SSD1306_I2C", autospec=True)
        i2c = "Fake I2C"
        reset_pin = "Fake reset_pin"
        _oleddisplay.initialize_oled(i2c, reset_pin)
        mock_oled.assert_called_once_with(
            DISPLAY_WIDTH, DISPLAY_HEIGHT, "Fake I2C", addr=0x3D, reset=reset_pin
        )

    def test_initialize_oled_returns_oled_object_if_successful(self, mocker):
        mock_oled = mocker.patch.object(adafruit_ssd1306, "SSD1306_I2C", autospec=True)
        mock_oled.return_value = "adafruit_ssd1306.SSD1306_I2C object"
        returned_result = _oleddisplay.initialize_oled(
            "dummy i2c", reset_pin="dummy reset"
        )
        assert "adafruit_ssd1306.SSD1306_I2C object" == returned_result

    def test_initialize_oled_returns_none_if_setup_fails(self, mocker):
        mock_oled = mocker.patch.object(adafruit_ssd1306, "SSD1306_I2C", autospec=True)
        mock_oled.side_effect = [ValueError, AttributeError]
        returned_result = _oleddisplay.initialize_oled(
            "dummy i2c", reset_pin="dummy reset"
        )
        assert returned_result is None
        assert (
            _oleddisplay.initialize_oled("dummy i2c", reset_pin="dummy reset") is None
        )

    def test_setup_hardware_returns_result_of_initialize_oled(self, mocker):
        _ = mocker.patch.object(
            datarecorder._oleddisplay, "initialize_i2c", autospec=True
        )
        mock_initialize_oled = mocker.patch.object(
            datarecorder._oleddisplay, "initialize_oled", autospec=True
        )
        mock_initialize_oled.return_value = "dummy oled"
        assert "dummy oled" == _oleddisplay.setup_hardware_oled()


class TestTextImageWriting:
    def test_setup_display_dict_returns_dictionary_object(self, mocker):
        mock_setup_hardware_oled = mocker.patch.object(
            datarecorder._oleddisplay, "setup_hardware_oled", autospec=True
        )
        mock_setup_hardware_oled.return_value = "dummy oled"
        returned_result = _oleddisplay.setup_display_dict()
        assert isinstance(returned_result, dict)
        assert list(returned_result.keys()) == [
            "oled",
            "image",
            "draw",
            "font",
            "lines",
        ]
        assert returned_result["oled"] == "dummy oled"
        assert isinstance(returned_result["image"], PIL.Image.Image)
        assert isinstance(returned_result["draw"], PIL.ImageDraw.ImageDraw)
        assert isinstance(returned_result["font"], PIL.ImageFont.ImageFont)
        assert isinstance(returned_result["lines"], deque)

    def test_clear_display_returns_display_and_calls_pil_image_draw_with_correct_values(
        self, mocker
    ):
        mock_display = {"draw": Mock()}
        assert _oleddisplay.clear_display(mock_display) == mock_display
        mock_display["draw"].rectangle.assert_called_once_with(
            (0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), fill=0, outline=0
        )

    def test_write_text_to_display_returns_display_and_is_called_with_correct_args(
        self,
    ):
        mock_display = {"draw": Mock(), "font": Mock()}
        coord = (1, 1)
        assert (
            _oleddisplay.write_text_to_display(
                display=mock_display, coords=coord, text="Hello World"
            )
            == mock_display
        )
        mock_display["draw"].text.assert_called_once_with(
            (1, 1), "Hello World", fill=255, font=mock_display["font"]
        )

    def test_show_display_calls_image_and_show_then_returns_none(self):
        mock_display = {"oled": Mock(), "image": Mock()}
        assert _oleddisplay.show_display(mock_display) is None
        mock_display["oled"].image.assert_called_once_with(mock_display["image"])
        mock_display["oled"].show.assert_called_once_with()


class TestTextDeliveryAndLayout:
    def test_add_screen_line_maintains_max_5_item_fifo_queue(self, mocker):
        _1 = mocker.patch.object(
            datarecorder._oleddisplay, "setup_hardware_oled", autospec=True
        )
        _2 = mocker.patch.object(
            datarecorder._oleddisplay, "clear_display", autospec=True
        )
        _3 = mocker.patch.object(
            datarecorder._oleddisplay, "show_display", autospec=True
        )
        _4 = mocker.patch.object(
            datarecorder._oleddisplay, "write_text_to_display", autospec=True
        )
        dummy_display = {"lines": deque([])}
        expected_result = deque([])
        for x in ["line 0", "line 1", "line 2", "line 3", "line 4"]:
            expected_result.append(x)
            returned_result = _oleddisplay.add_screen_line(
                display=dummy_display, text=x
            )
            assert expected_result == returned_result["lines"]
        expected_result = deque(["line 1", "line 2", "line 3", "line 4", "line 5"])
        returned_result = _oleddisplay.add_screen_line(
            display=dummy_display, text="line 5"
        )
        assert expected_result == returned_result["lines"]
        assert len(returned_result["lines"]) == 5

    def test_lines_are_drawn_at_correct_coordinates(self, mocker):
        _1 = mocker.patch.object(
            datarecorder._oleddisplay, "setup_hardware_oled", autospec=True
        )
        mock_clear_display = mocker.patch.object(
            datarecorder._oleddisplay, "clear_display", autospec=True
        )
        _3 = mocker.patch.object(
            datarecorder._oleddisplay, "show_display", autospec=True
        )
        mock_write_text_to_display = mocker.patch.object(
            datarecorder._oleddisplay, "write_text_to_display", autospec=True
        )
        dummy_display = {
            "lines": deque(["0 Line", "1 Line", "2 Line", "3 Line", "4 Line"])
        }
        mock_clear_display.return_value = dummy_display
        mock_write_text_to_display.return_value = dummy_display
        _oleddisplay.draw_lines(display=dummy_display)
        calls = [
            call(display=dummy_display, coords=(1, 1), text="0 Line"),
            call(display=dummy_display, coords=(1, 13), text="1 Line"),
            call(display=dummy_display, coords=(1, 25), text="2 Line"),
            call(display=dummy_display, coords=(1, 37), text="3 Line"),
            call(display=dummy_display, coords=(1, 49), text="4 Line"),
        ]
        mock_write_text_to_display.assert_has_calls(calls)

    def test_draw_lines_calls_clear_display(self, mocker):
        _1 = mocker.patch.object(
            datarecorder._oleddisplay, "setup_hardware_oled", autospec=True
        )
        mock_clear_display = mocker.patch.object(
            datarecorder._oleddisplay, "clear_display", autospec=True
        )
        mock_show_display = mocker.patch.object(
            datarecorder._oleddisplay, "show_display", autospec=True
        )
        _4 = mocker.patch.object(
            datarecorder._oleddisplay, "write_text_to_display", autospec=True
        )
        test_display = _oleddisplay.setup_display_dict()
        test_display["lines"] = deque(["Test text"])
        _oleddisplay.draw_lines(display=test_display)
        mock_clear_display.assert_called_once()
        mock_show_display.assert_called_once()

    # def test_draw_lines_calls_show_display(self, _1, , _3, _4):
    #     test_display = _oleddisplay.setup_display_dict()
    #     test_lines = deque(['Test text'])
    #     _oleddisplay.draw_lines(lines=test_lines, display=test_display)
    #     mock_show_display.assert_called_once()


class TestDataFlow:
    def test_display_message_from_queue_calls_draw_lines_if_oled_not_None(self, mocker):
        mock_draw_lines = mocker.patch.object(
            datarecorder._oleddisplay, "draw_lines", autospec=True
        )
        mock_message_queue = mocker.patch.object(
            datarecorder._oleddisplay, "message_queue", autospec=True
        )
        mock_message_queue.get.return_value = "dummy text"
        dummy_display = {"oled": "dummy display", "lines": deque([])}
        _oleddisplay.display_message_from_queue(display=dummy_display)
        mock_draw_lines.assert_called_once_with(display=dummy_display)
        mock_message_queue.get.assert_called()
        mock_message_queue.task_done.assert_called()

    def test_display_message_from_queue_does_not_call_draw_lines_if_oled_None(
        self, mocker
    ):
        mock_draw_lines = mocker.patch.object(
            datarecorder._oleddisplay, "draw_lines", autospec=True
        )
        mock_message_queue = mocker.patch.object(
            datarecorder._oleddisplay, "message_queue", autospec=True
        )
        mock_message_queue.get.return_value = "dummy text"
        display = {"oled": None, "lines": deque([])}
        _oleddisplay.display_message_from_queue(display=display)
        mock_draw_lines.assert_not_called()
        mock_message_queue.get.assert_called()
        mock_message_queue.task_done.assert_called()

    def test_display_message_from_queue_returns_lines_and_display(
        self,
        mocker,
    ):
        mock_draw_lines = mocker.patch.object(
            datarecorder._oleddisplay, "draw_lines", autospec=True
        )
        _oleddisplay.message_queue.put_nowait("dummy data")
        display = {"oled": "dummy display", "lines": deque(["test_lines"])}
        mock_draw_lines.return_value = display
        returned_data = _oleddisplay.display_message_from_queue(display=display)
        assert display == returned_data

    def test_display_message_from_queue_raises_exception_and_calls_task_done(
        self, mocker
    ):
        mock_add_screen_line = mocker.patch.object(
            datarecorder._oleddisplay, "add_screen_line", autospec=True
        )
        mock_message_queue = mocker.patch.object(
            datarecorder._oleddisplay, "message_queue", autospec=True
        )
        mock_message_queue.get.side_effect = [queue.Empty]
        display = {"oled": "dummy display", "lines": deque(["test_lines"])}
        _oleddisplay.display_message_from_queue(display=display)
        mock_add_screen_line.assert_not_called()
        mock_message_queue.task_done.assert_called_once()

    @pytest.mark.skip(reason="Weird TypeError raised in assert.")
    def test_display_is_passed_up_and_down_correctly(self, mocker):
        mock_show_display = mocker.patch.object(
            datarecorder._oleddisplay, "show_display", autospec=True
        )
        mock_setup_hardware_oled = mocker.patch.object(
            datarecorder._oleddisplay, "setup_hardware_oled", autospec=True
        )
        mock_write_text_to_display = mocker.patch.object(
            datarecorder._oleddisplay, "show_display", autospec=True
        )
        mock_setup_hardware_oled.return_value = "dummy display"
        mock_write_text_to_display.return_value = "write_text_to_display"
        _oleddisplay.message_queue.put_nowait("Test passing display dict")
        mock_display = {"lines": deque([]), "oled": Mock(), "draw": Mock()}
        data_returned = _oleddisplay.display_message_from_queue(display=mock_display)
        mock_show_display.assert_called_once()
        assert "write_text_to_display" == data_returned


class TestInitAndThreadingCalls:
    def test_setup_called_and_thread_called_and_started_as_daemon(self, mocker):
        mock_threading = mocker.patch.object(threading, "Thread", autospec=True)
        mock_loop_read_message_queue = mocker.patch.object(
            datarecorder._oleddisplay, "loop_read_message_queue", autospec=True
        )
        mock_setup_display_dict = mocker.patch.object(
            datarecorder._oleddisplay, "setup_display_dict", autospec=True
        )
        mock_setup_hardware_oled = mocker.patch.object(
            datarecorder._oleddisplay, "setup_hardware_oled", autospec=True
        )
        mock_setup_hardware_oled.return_value = "dummy display"
        mock_setup_display_dict.return_value = "x"
        mock_message_thread = Mock()
        mock_threading.return_value = mock_message_thread
        returned_message_thread = _oleddisplay.init_display_thread()
        mock_setup_display_dict.assert_called_once()
        mock_threading.assert_called_once_with(target=mock_loop_read_message_queue)
        assert returned_message_thread.daemon is True
        returned_message_thread.start.assert_called()

    def test_write_message_to_queue_calls_message_queue_put(self):
        _oleddisplay.message_queue = Mock()
        _oleddisplay.write_message_to_queue("Message text")
        _oleddisplay.message_queue.put_nowait.assert_called_once_with("Message text")

    def test_write_message_to_queue_handles_queue_full_error(self):
        _oleddisplay.message_queue = Mock()
        _oleddisplay.message_queue.put_nowait.side_effect = queue.Full
        _oleddisplay.write_message_to_queue("Message text")

    def test_shut_down_calls_message_queue_join_and_clear_display(self, mocker):
        mock_show_display = mocker.patch.object(
            datarecorder._oleddisplay, "show_display", autospec=True
        )
        mock_clear_display = mocker.patch.object(
            datarecorder._oleddisplay, "clear_display", autospec=True
        )
        mock_message_queue = mocker.patch.object(
            datarecorder._oleddisplay, "message_queue"
        )
        _oleddisplay.shut_down()
        mock_message_queue.join.assert_called_once()
        mock_clear_display.assert_called_once_with(_oleddisplay.global_display)
        mock_show_display.assert_called_once_with(_oleddisplay.global_display)
