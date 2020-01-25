#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import Mock, patch, call
from collections import deque
import queue
import PIL
import board
from datarecorder import oleddisplay
from __config__ import DISPLAY_WIDTH, DISPLAY_HEIGHT


class TestDisplayHardwareSetup(TestCase):

    @patch('busio.I2C')
    def test_initialize_i2c_called_with_correct_args(self, mock_busio_i2c):
        oleddisplay.initialize_i2c()
        mock_busio_i2c.assert_called_once_with(board.SCL, board.SDA)

    @patch('busio.I2C')
    def test_initialize_i2c_returns_i2c_object_if_successful(self, mock_busio_i2c):
        mock_busio_i2c.return_value = 'busio.i2c object'
        returned_result = oleddisplay.initialize_i2c()
        self.assertEqual('busio.i2c object', returned_result)

    @patch('busio.I2C')
    def test_initialize_i2c_logs_warning_and_returns_none_if_setup_fails(self, mock_busio_i2c):
        mock_busio_i2c.side_effect = ValueError
        returned_result = oleddisplay.initialize_i2c()
        self.assertEqual(returned_result, None)

    @patch('adafruit_ssd1306.SSD1306_I2C')
    def test_initialize_oled_called_with_correct_args(self, mock_oled):
        i2c = 'Fake I2C'
        reset_pin = 'Fake reset_pin'
        oleddisplay.initialize_oled(i2c, reset_pin)
        mock_oled.assert_called_once_with(DISPLAY_WIDTH, DISPLAY_HEIGHT, 'Fake I2C', addr=0x3d, reset=reset_pin)

    @patch('adafruit_ssd1306.SSD1306_I2C')
    def test_initialize_oled_returns_oled_object_if_successful(self, mock_oled):
        mock_oled.return_value = 'adafruit_ssd1306.SSD1306_I2C object'
        returned_result = oleddisplay.initialize_oled('dummy i2c', reset_pin='dummy reset')
        self.assertEqual('adafruit_ssd1306.SSD1306_I2C object', returned_result)

    @patch('adafruit_ssd1306.SSD1306_I2C')
    def test_initialize_oled_returns_none_if_setup_fails(self, mock_oled):
        mock_oled.side_effect = [ValueError, AttributeError]
        returned_result = oleddisplay.initialize_oled('dummy i2c', reset_pin='dummy reset')
        self.assertEqual(returned_result, None)
        returned_result = oleddisplay.initialize_oled('dummy i2c', reset_pin='dummy reset')
        self.assertEqual(returned_result, None)

    @patch('datarecorder.oleddisplay.initialize_i2c')
    @patch('datarecorder.oleddisplay.initialize_oled')
    def test_setup_hardware_returns_result_of_initialize_oled(self, mock_initialize_oled, _):
        mock_initialize_oled.return_value = 'dummy oled'
        returned_result = oleddisplay.setup_hardware_oled()
        self.assertEqual('dummy oled', returned_result)


@patch('datarecorder.oleddisplay.setup_hardware_oled')
class TestTextImageWriting(TestCase):

    # noinspection PyUnresolvedReferences
    def test_setup_display_dict_returns_dictionary_object(self, mock_setup_hardware_oled):
        mock_setup_hardware_oled.return_value = 'dummy oled'
        returned_result = oleddisplay.setup_display_dict()
        self.assertIsInstance(returned_result, dict)
        self.assertEqual(list(returned_result.keys()), ['oled', 'image', 'draw', 'font', 'lines'])
        self.assertEqual(returned_result['oled'], 'dummy oled')
        self.assertIsInstance(returned_result['image'], PIL.Image.Image)
        self.assertIsInstance(returned_result['draw'], PIL.ImageDraw.ImageDraw)
        self.assertIsInstance(returned_result['font'], PIL.ImageFont.ImageFont)
        self.assertIsInstance(returned_result['lines'], deque)

    def test_clear_display_returns_display_and_calls_pil_image_draw_with_correct_values(self, _1):
        mock_display = {'draw': Mock()}
        returned_result = oleddisplay.clear_display(mock_display)
        self.assertEqual(returned_result, mock_display)
        mock_display['draw'].rectangle.assert_called_once_with((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), fill=0, outline=0)

    def test_write_text_to_display_returns_display(self, mock_setup_hardware_oled):
        mock_setup_hardware_oled.return_value = 'dummy oled'
        display = oleddisplay.setup_display_dict()
        coord = (1, 1)
        data_returned = oleddisplay.write_text_to_display(display=display, coords=coord, text='Hello World')
        self.assertEqual(data_returned, display)


@patch('datarecorder.oleddisplay.setup_hardware_oled')
@patch('datarecorder.oleddisplay.clear_display')
@patch('datarecorder.oleddisplay.show_display')
@patch('datarecorder.oleddisplay.write_text_to_display')
class TestTextDeliveryAndLayout(TestCase):

    def test_screen_queue_fifo(self, _1, _2, _3, _4):
        lines = deque([])
        returned_result_1 = oleddisplay.add_screen_line(lines=lines, text='0 Line')
        self.assertEqual(returned_result_1, deque(['0 Line']))
        returned_result_2 = oleddisplay.add_screen_line(lines=returned_result_1, text='1 Line')
        self.assertEqual(returned_result_2, deque(['0 Line', '1 Line']))
        lines = deque([])
    #
    # def test_
    #     for z in range(6):
    #         returned_result = oleddisplay.add_screen_line(lines=lines, text=f'{z} Line')
    #     self.assertEqual(deque(['1 Line', '2 Line', '3 Line', '4 Line', '5 Line']), returned_result)

    def test_lines_are_drawn_at_correct_coordinates(self, mock_write_text_to_display, _2, mock_clear_display, _4):
        display = None
        mock_clear_display.return_value = display
        mock_write_text_to_display.return_value = display
        lines = deque(['0 Line', '1 Line', '2 Line', '3 Line', '4 Line'])
        oleddisplay.draw_lines(display=display, lines=lines)
        calls = [call(display=None, coords=(1, 1), text='0 Line'),
                 call(display=None, coords=(1, 13), text='1 Line'),
                 call(display=None, coords=(1, 25), text='2 Line'),
                 call(display=None, coords=(1, 37), text='3 Line'),
                 call(display=None, coords=(1, 49), text='4 Line'),
                 ]
        mock_write_text_to_display.assert_has_calls(calls)

    def test_draw_lines_calls_clear_display(self, _1, _2, mock_clear_display, _4):
        test_display = oleddisplay.setup_display_dict()
        test_lines = deque(['Test text'])
        oleddisplay.draw_lines(lines=test_lines, display=test_display)
        mock_clear_display.assert_called_once()

    def test_draw_lines_calls_show_display(self, _1, mock_show_display, _3, _4):
        test_display = oleddisplay.setup_display_dict()
        test_lines = deque(['Test text'])
        oleddisplay.draw_lines(lines=test_lines, display=test_display)
        mock_show_display.assert_called_once()


class TestDataFlow(TestCase):

    @patch('datarecorder.oleddisplay.message_queue')
    @patch('datarecorder.oleddisplay.draw_lines')
    def test_read_message_queue_write_to_display_calls_draw_lines_if_oled_not_None(self, mock_draw_lines,
                                                                                   mock_message_queue,
                                                                                   ):
        mock_message_queue.get.return_value = 'dummy text'
        display = {'oled': 'dummy display'}
        lines = deque([])
        oleddisplay.read_message_queue_write_to_display(lines=lines, display=display)
        mock_draw_lines.assert_called_once_with(display=display, lines=deque(['dummy text']))
        mock_message_queue.get.assert_called()
        mock_message_queue.task_done.assert_called()

    @patch('datarecorder.oleddisplay.message_queue')
    @patch('datarecorder.oleddisplay.draw_lines')
    def test_read_message_queue_write_to_display_does_not_call_draw_lines_if_oled_None(self, mock_draw_lines,
                                                                                       mock_message_queue,
                                                                                       ):
        mock_message_queue.get.return_value = 'dummy text'
        display = {'oled': None}
        lines = deque([])
        oleddisplay.read_message_queue_write_to_display(lines=lines, display=display)
        mock_draw_lines.assert_not_called()
        mock_message_queue.get.assert_called()
        mock_message_queue.task_done.assert_called()

    @patch('datarecorder.oleddisplay.draw_lines')
    def test_read_message_queue_write_to_display_returns_lines_and_display(self, mock_draw_lines,):
        oleddisplay.message_queue.put_nowait('dummy data')
        lines = deque(['test_lines'])
        display = {'oled': 'dummy display'}
        mock_draw_lines.return_value = display
        returned_data = oleddisplay.read_message_queue_write_to_display(lines=lines, display=display)
        self.assertEqual((lines, display), returned_data)

    @patch('datarecorder.oleddisplay.add_screen_line')
    @patch('datarecorder.oleddisplay.message_queue')
    def test_read_message_queue_write_to_display_raises_exception_and_calls_task_done(self, mock_message_queue,
                                                                                      mock_add_screen_line,
                                                                                      ):
        mock_message_queue.get.side_effect = [queue.Empty]
        display = {'oled': 'dummy display'}
        lines = deque(['test_lines'])
        oleddisplay.read_message_queue_write_to_display(lines=lines, display=display)
        mock_add_screen_line.assert_not_called()
        mock_message_queue.task_done.assert_called_once()

    @patch('datarecorder.oleddisplay.write_text_to_display')
    @patch('datarecorder.oleddisplay.setup_hardware_oled')
    @patch('datarecorder.oleddisplay.show_display')
    def test_display_is_passed_up_and_down_correctly(self, mock_show_display,
                                                     mock_setup_hardware_oled,
                                                     mock_write_text_to_display
                                                     ):
        mock_setup_hardware_oled.return_value = 'dummy display'
        mock_write_text_to_display.return_value = 'write_text_to_display'
        oleddisplay.message_queue.put_nowait('Test passing display dict')
        test_display = oleddisplay.setup_display_dict()
        test_lines = deque([])
        data_returned = oleddisplay.read_message_queue_write_to_display(lines=test_lines, display=test_display)
        mock_show_display.assert_called_once()
        self.assertEqual('write_text_to_display', data_returned[1])


class TestInitAndThreadingCalls(TestCase):

    @patch('datarecorder.oleddisplay.setup_hardware_oled')
    @patch('datarecorder.oleddisplay.setup_display_dict')
    @patch('datarecorder.oleddisplay.loop_read_message_queue')
    @patch('threading.Thread')
    def test_setup_called_and_thread_called_and_started_as_daemon(self, mock_threading,
                                                                  mock_loop_read_message_queue,
                                                                  mock_setup_display_dict,
                                                                  mock_setup_hardware_oled,
                                                                  ):
        mock_setup_hardware_oled.return_value = 'dummy display'
        mock_setup_display_dict.return_value = 'x'
        mock_message_thread = Mock()
        mock_threading.return_value = mock_message_thread
        returned_message_thread = oleddisplay.init_display_thread()
        mock_setup_display_dict.assert_called_once()
        mock_threading.assert_called_once_with(target=mock_loop_read_message_queue)
        self.assertTrue(returned_message_thread.daemon)
        returned_message_thread.start.assert_called()

    def test_write_message_to_queue_calls_message_queue_put(self):
        oleddisplay.message_queue = Mock()
        oleddisplay.write_message_to_queue('Message text')
        oleddisplay.message_queue.put_nowait.assert_called_once_with('Message text')

    def test_write_message_to_queue_handles_queue_full_error(self):
        oleddisplay.message_queue = Mock()
        oleddisplay.message_queue.put_nowait.side_effect = queue.Full
        oleddisplay.write_message_to_queue('Message text')
        self.assertTrue(True)

    @patch('datarecorder.oleddisplay.show_display')
    @patch('datarecorder.oleddisplay.clear_display')
    @patch('datarecorder.oleddisplay.message_queue')
    def test_shut_down_calls_message_queue_join_and_clear_display(self, mock_message_queue,
                                                                  mock_clear_display,
                                                                  mock_show_display,
                                                                  ):
        oleddisplay.shut_down()
        mock_message_queue.join.assert_called_once()
        mock_clear_display.assert_called_once_with(oleddisplay.global_display)
        mock_show_display.assert_called_once_with(oleddisplay.global_display)
