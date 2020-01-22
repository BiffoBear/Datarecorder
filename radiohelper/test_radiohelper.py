from unittest import TestCase
import radiohelper


class TestRadioHelper(TestCase):

    def test_increment_serial_number_with_wrap_increments(self):
        self.assertEqual(0x02, radiohelper.increment_number_with_wrap(0x01))

    def test_increment_serial_number_with_wrap_wraps(self):
        self.assertEqual(0x00, radiohelper.increment_number_with_wrap(0xffff))

    def test_increment_serial_number_with_wrap_raises_typeerror_if_number_not_number(self):
        for incorrect_arg in ('x', []):
            with self.assertRaises(TypeError) as dm:
                radiohelper.increment_number_with_wrap(incorrect_arg)
            self.assertIn('number and wrap_at must be numbers', dm.exception.args)

    def test_increment_serial_number_with_wrap_raises_typeerror_if_wrap_at_not_number(self):
        for incorrect_arg in ('x', []):
            with self.assertRaises(TypeError) as dm:
                radiohelper.increment_number_with_wrap(1, wrap_at=incorrect_arg)
            self.assertIn('number and wrap_at must be numbers', dm.exception.args)
