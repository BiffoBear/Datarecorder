from unittest import TestCase, skip
from unittest.mock import Mock, patch, call
from collections import deque
import PIL
import board
import adafruit_ssd1306
import oleddisplay


class TestDisplaySetupAndFunction(TestCase):

    @patch('busio.I2C')
    def test_raspi_i2c_bus_initialized(self, mock_busio_i2c):
        oleddisplay.initialize_i2c()
        mock_busio_i2c.assert_called_once_with(board.SCL, board.SDA)

    @patch('adafruit_ssd1306.SSD1306_I2C')
    def test_oled_display_initialized_with_correct_args(self, mock_oled):
        i2c = 'Fake I2C'
        reset_pin = 'Fake reset_pin'
        oleddisplay.initialize_oled(i2c, reset_pin)
        mock_oled.assert_called_once_with(128, 64, 'Fake I2C', addr=0x3d, reset=reset_pin)

    def test_setup_returns_dictionary_object(self):
        # Assumes display is correctly connected and working
        x = oleddisplay.setup()
        self.assertIsInstance(x, dict)
        self.assertIsInstance(x['oled'], adafruit_ssd1306.SSD1306_I2C)
        self.assertIsInstance(x['image'], PIL.Image.Image)
        self.assertIsInstance(x['draw'], PIL.ImageDraw.ImageDraw)
        self.assertIsInstance(x['font'], PIL.ImageFont.ImageFont)

    @patch('adafruit_ssd1306.SSD1306_I2C')
    def test_setup_logs_warning_and_returns_none_if_setup_fails(self, mock_oled):
        mock_oled.side_effect = ValueError
        with self.assertLogs() as cm:
           x = oleddisplay.setup()
        self.assertIn('OLED display failed to initialize. Check that I2C bus enabled and wiring is correct',
                      cm.output[0])
        self.assertEqual(x, None)

    def test_setup_logs_oled_initialization(self):
        with self.assertLogs() as cm:
            oleddisplay.setup()
        self.assertIn('OLED display initialized successfully', cm.output[0])

    def test_clear_display(self):
        test_display = oleddisplay.setup()
        x = oleddisplay.clear_display(test_display)
        self.assertEqual(x, test_display)

    def test_write_to_display_returns_dict(self):
        test_display = oleddisplay.setup()
        coords = (1, 1)
        data_returned = oleddisplay.write_text_to_display(display=test_display, coords=coords, text='Hello World')
        self.assertEqual(data_returned, test_display)

    def test_show_display_returns_dict(self):
        test_display = oleddisplay.setup()
        test_display['draw'].text((10, 10), 'Hi Mars!', font=test_display['font'], fill=255)
        test_display['draw'].text((10, 22), 'Yo Pluto!', font=test_display['font'], fill=255)
        test_display['oled'].image(test_display['image'])
        x = oleddisplay.show_display(display=test_display)
        self.assertEqual(x, test_display)

    @patch('oleddisplay.clear_display')
    def test_show_display_calls_clear_display(self, mock_clear_display):
        test_display = oleddisplay.setup()
        oleddisplay.show_display(display=test_display)
        mock_clear_display.assert_called_once()


class TestTextDeliveryAndLayout(TestCase):

    def test_screen_queue_fifo(self):
        queue = deque([])
        x = oleddisplay.add_screen_line(lines=queue, text='0 Line')
        self.assertEqual(x, deque(['0 Line']))
        y = oleddisplay.add_screen_line(lines=x, text='1 Line')
        self.assertEqual(y, deque(['0 Line', '1 Line']))
        queue = deque([])
        for z in range(6):
            queue = oleddisplay.add_screen_line(lines=queue, text=f'{z} Line')
        self.assertEqual(deque(['1 Line', '2 Line', '3 Line', '4 Line', '5 Line']), queue)

    @patch('oleddisplay.show_display')
    @patch('oleddisplay.write_text_to_display')
    def test_lines_are_drawn_at_correct_coordinates(self, mock_write_to_display, _):
        display = None
        lines = deque(['0 Line', '1 Line', '2 Line', '3 Line', '4 Line'])
        oleddisplay.draw_lines(display=display, lines=lines)
        calls = [call(display=None, coords=(1, 13), text='0 Line'),
                 call(display=None, coords=(1, 25), text='1 Line'),
                 call(display=None, coords=(1, 37), text='2 Line'),
                 call(display=None, coords=(1, 49), text='3 Line'),
                 call(display=None, coords=(1, 61), text='4 Line'),
                 ]
        mock_write_to_display.assert_has_calls(calls)

    @patch('oleddisplay.show_display')
    @patch('oleddisplay.write_text_to_display')
    def test_draw_lines_returns_display(self, _1, mock_show_display):
        mock_show_display.side_effect = ['Display']
        lines = deque(['Test Line'])
        returned_data = oleddisplay.draw_lines(display=None, lines=lines)
        self.assertEqual('Display', returned_data)

    @patch('oleddisplay.show_display')
    def test_draw_lines_calls_show_display(self, mock_show_display):
        test_display = oleddisplay.setup()
        test_lines = deque(['Test text'])
        oleddisplay.draw_lines(lines=test_lines, display=test_display)
        mock_show_display.assert_called_once()


class TestDataFlow(TestCase):

    @patch('oleddisplay.message_queue')
    @patch('oleddisplay.draw_lines')
    def test_read_one_line_from_queue_write_to_screen(self, mock_draw_lines, mock_message_queue):
        mock_message_queue.get.return_value = 'dummy text'
        display_queue = deque([])
        oleddisplay.read_message_queue_write_to_display(lines=display_queue, display=None)
        mock_draw_lines.assert_called_once_with(display=None, lines=deque(['dummy text']))
        mock_message_queue.get.assert_called()
        mock_message_queue.task_done.assert_called()

    @patch('oleddisplay.show_display')
    @patch('oleddisplay.write_text_to_display')
    def test_read_message_queue_write_to_display_returns_lines_and_display(self, _1, mock_show_display):
        oleddisplay.message_queue.put_nowait('dummy data')
        lines = deque(['test_lines'])
        test_display = 'test display'
        mock_show_display.return_value = test_display
        returned_data = oleddisplay.read_message_queue_write_to_display(lines=lines, display=None)
        self.assertEqual((lines, test_display), returned_data)

    @patch('oleddisplay.show_display')
    def test_display_is_passed_up_and_down_correctly(self, mock_show_display):
        mock_show_display.return_value = 'Show Display'
        oleddisplay.message_queue.put_nowait('Test passing display dict')
        test_display = oleddisplay.setup()
        test_lines = deque([])
        data_returned = oleddisplay.read_message_queue_write_to_display(lines=test_lines, display=test_display)
        mock_show_display.assert_called_once()
        self.assertEqual('Show Display', data_returned[1])


class TestInitAndThreadingCalls(TestCase):

    @patch('oleddisplay.setup')
    @patch('oleddisplay.loop_read_message_queue')
    @patch('threading.Thread')
    def test_setup_called_and_thread_called_and_started_as_daemon(self, mock_threading,
                                                                  mock_loop_read_message_queue,
                                                                  mock_setup
                                                                  ):
        mock_setup.return_value = 'mock display dict'
        mock_message_thread = Mock()
        mock_threading.return_value = mock_message_thread
        returned_message_thread = oleddisplay.init_display_thread()
        mock_setup.assert_called_once()
        mock_threading.assert_called_once_with(target=mock_loop_read_message_queue)
        self.assertTrue(returned_message_thread.daemon)
        returned_message_thread.start.assert_called()
