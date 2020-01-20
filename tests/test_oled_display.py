from unittest import TestCase, skip
from unittest.mock import Mock, patch, call
from collections import deque
import queue
import PIL
import board
import oleddisplay
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
        with self.assertLogs() as cm:
            returned_result = oleddisplay.initialize_i2c()
        self.assertIn('I2C bus failed to initialize. Check that I2C is enabled', cm.output[0])
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
    def test_initialize_oled_logs_oled_initialization(self, _):
        with self.assertLogs(level='INFO') as cm:
            oleddisplay.initialize_oled('dummy i2c', reset_pin='dummy reset')
        self.assertIn('OLED display initialized successfully', cm.output[0])

    @patch('adafruit_ssd1306.SSD1306_I2C')
    def test_initialize_oled_logs_warning_and_returns_none_if_setup_fails(self, mock_oled):
        mock_oled.side_effect = ValueError
        with self.assertLogs() as cm:
            returned_result = oleddisplay.initialize_oled('dummy i2c', reset_pin='dummy reset')
        self.assertIn('OLED display failed to initialize. Check that wiring is correct',
                      cm.output[0])
        self.assertEqual(returned_result, None)

    @patch('oleddisplay.initialize_i2c')
    @patch('oleddisplay.initialize_oled')
    def test_setup_hardware_returns_result_of_inititalize_oled(self, mock_initialize_oled, _):
        mock_initialize_oled.return_value = 'dummy oled'
        returned_result = oleddisplay.setup_hardware_oled()
        self.assertEqual('dummy oled', returned_result)


@patch('oleddisplay.setup_hardware_oled')
class TestTextImageWriting(TestCase):

    def test_setup_display_dict_returns_dictionary_object(self, mock_setup_hardware_oled):
        mock_setup_hardware_oled.return_value = 'dummy oled'
        returned_result = oleddisplay.setup_display_dict()
        self.assertIsInstance(returned_result, dict)
        self.assertEqual(returned_result['oled'], 'dummy oled')
        self.assertIsInstance(returned_result['image'], PIL.Image.Image)
        self.assertIsInstance(returned_result['draw'], PIL.ImageDraw.ImageDraw)
        self.assertIsInstance(returned_result['font'], PIL.ImageFont.ImageFont)

    def test_clear_display_returns_display(self, mock_setup_hardware_oled):
        mock_setup_hardware_oled.return_value = 'dummy oled'
        display = oleddisplay.setup_display_dict()
        returned_result = oleddisplay.clear_display(display)
        self.assertEqual(returned_result, display)

    def test_write_text_to_display_returns_display(self, mock_setup_hardware_oled):
        mock_setup_hardware_oled.return_value = 'dummy oled'
        display = oleddisplay.setup_display_dict()
        coord = (1, 1)
        data_returned = oleddisplay.write_text_to_display(display=display, coords=coord, text='Hello World')
        self.assertEqual(data_returned, display)


@patch('oleddisplay.clear_display')
@patch('oleddisplay.show_display')
@patch('oleddisplay.write_text_to_display')
class TestTextDeliveryAndLayout(TestCase):

    def test_screen_queue_fifo(self, _1, _2, _3):
        queue = deque([])
        x = oleddisplay.add_screen_line(lines=queue, text='0 Line')
        self.assertEqual(x, deque(['0 Line']))
        y = oleddisplay.add_screen_line(lines=x, text='1 Line')
        self.assertEqual(y, deque(['0 Line', '1 Line']))
        queue = deque([])
        for z in range(6):
            queue = oleddisplay.add_screen_line(lines=queue, text=f'{z} Line')
        self.assertEqual(deque(['1 Line', '2 Line', '3 Line', '4 Line', '5 Line']), queue)

    def test_lines_are_drawn_at_correct_coordinates(self, mock_write_to_display, _1, mock_clear_display):
        display = None
        mock_clear_display.return_value = display
        lines = deque(['0 Line', '1 Line', '2 Line', '3 Line', '4 Line'])
        oleddisplay.draw_lines(display=display, lines=lines)
        calls = [call(display=None, coords=(1, 1), text='0 Line'),
                 call(display=None, coords=(1, 13), text='1 Line'),
                 call(display=None, coords=(1, 25), text='2 Line'),
                 call(display=None, coords=(1, 37), text='3 Line'),
                 call(display=None, coords=(1, 49), text='4 Line'),
                 ]
        mock_write_to_display.assert_has_calls(calls)

    def test_draw_lines_returns_display(self, _1, mock_show_display, _2):
        mock_show_display.side_effect = ['Display']
        lines = deque(['Test Line'])
        returned_data = oleddisplay.draw_lines(display=None, lines=lines)
        self.assertEqual('Display', returned_data)

    def test_draw_lines_calls_clear_display(self, _1, _2, mock_clear_display):
        test_display = oleddisplay.setup_hardware_oled()
        test_lines = deque(['Test text'])
        oleddisplay.draw_lines(lines=test_lines, display=test_display)
        mock_clear_display.assert_called_once()

    def test_draw_lines_calls_show_display(self, _1, mock_show_display, _2):
        test_display = oleddisplay.setup_hardware_oled()
        test_lines = deque(['Test text'])
        oleddisplay.draw_lines(lines=test_lines, display=test_display)
        mock_show_display.assert_called_once()


class TestDataFlow(TestCase):

    @patch('oleddisplay.message_queue')
    @patch('oleddisplay.draw_lines')
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

    @patch('oleddisplay.message_queue')
    @patch('oleddisplay.draw_lines')
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

    @patch('oleddisplay.clear_display')
    @patch('oleddisplay.show_display')
    @patch('oleddisplay.write_text_to_display')
    def test_read_message_queue_write_to_display_returns_lines_and_display(self, _1, mock_show_display, _2):
        oleddisplay.message_queue.put_nowait('dummy data')
        lines = deque(['test_lines'])
        display = {'oled': 'dummy display'}
        mock_show_display.return_value = display
        returned_data = oleddisplay.read_message_queue_write_to_display(lines=lines, display=display)
        self.assertEqual((lines, display), returned_data)

    @patch('oleddisplay.add_screen_line')
    @patch('oleddisplay.message_queue')
    def test_read_message_queue_write_to_display_raises_exception_and_calls_task_done(self, mock_message_queue,
                                                                                      mock_add_screen_line,
                                                                                      ):
        mock_message_queue.get.side_effect = [queue.Empty]
        display = {'oled': 'dummy display'}
        lines = deque(['test_lines'])
        oleddisplay.read_message_queue_write_to_display(lines=lines, display=display)
        mock_add_screen_line.not_called
        mock_message_queue.task_done.assert_called_once()

    @patch('oleddisplay.setup_hardware_oled')
    @patch('oleddisplay.show_display')
    def test_display_is_passed_up_and_down_correctly(self, mock_show_display, mock_setup_hardware_oled):
        mock_setup_hardware_oled.return_value = 'dummy display'
        mock_show_display.return_value = 'Show Display'
        oleddisplay.message_queue.put_nowait('Test passing display dict')
        test_display = oleddisplay.setup_display_dict()
        test_lines = deque([])
        data_returned = oleddisplay.read_message_queue_write_to_display(lines=test_lines, display=test_display)
        mock_show_display.assert_called_once()
        self.assertEqual('Show Display', data_returned[1])


class TestInitAndThreadingCalls(TestCase):

    @patch('oleddisplay.setup_hardware_oled')
    @patch('oleddisplay.setup_display_dict')
    @patch('oleddisplay.loop_read_message_queue')
    @patch('threading.Thread')
    def test_setup_called_and_thread_called_and_started_as_daemon(self, mock_threading,
                                                                  mock_loop_read_message_queue,
                                                                  mock_setup_display_dict,
                                                                  mock_setup_hardware_oled,
                                                                  ):
        mock_setup_hardware_oled.return_value = 'dummy display'
        mock_setup_display_dict.return_value = 'x'  # oleddisplay.setup_display_dict()
        mock_message_thread = Mock()
        mock_threading.return_value = mock_message_thread
        returned_message_thread = oleddisplay.init_display_thread()
        mock_setup_display_dict.assert_called_once()
        mock_threading.assert_called_once_with(target=mock_loop_read_message_queue)
        self.assertTrue(returned_message_thread.daemon)
        returned_message_thread.start.assert_called()
