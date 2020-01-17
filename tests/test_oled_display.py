from unittest import TestCase, skip
from unittest.mock import Mock, patch
from collections import deque
import PIL
import board
import adafruit_ssd1306
import oleddisplay


@skip
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
        oled = oleddisplay.setup()
        x = oleddisplay.clear_display(oled)
        self.assertEqual(x, oled)

    def test_write_to_display_returns_dict(self):
        oled = oleddisplay.setup()
        coords = (1, 1)
        x = oleddisplay.write_text_to_display(display=oled, coords=coords, text='Hello World')
        self.assertEqual(x, oled)

    def test_show_display_returns_dict(self):
        oled = oleddisplay.setup()
        oled['draw'].text((10, 10), 'Hi Mars!', font=oled['font'], fill=255)
        oled['draw'].text((10, 22), 'Yo Pluto!', font=oled['font'], fill=255)
        oled['oled'].image(oled['image'])
        x = oleddisplay.show_display(display=oled)
        self.assertEqual(x, oled)


class TestTextDeliveryAndLayout(TestCase):

    def test_screen_queue_fifo(self):
        queue = deque([])
        x = oleddisplay.add_screen_line(queue=queue, text='0 Line')
        self.assertEqual(x, deque(['0 Line']))
        y = oleddisplay.add_screen_line(queue=x, text='1 Line')
        self.assertEqual(y, deque(['0 Line', '1 Line']))
        queue = deque([])
        for z in range(6):
            queue = oleddisplay.add_screen_line(queue=queue, text=f'{z} Line')
        self.assertEqual(deque(['1 Line', '2 Line', '3 Line', '4 Line', '5 Line']), queue)

