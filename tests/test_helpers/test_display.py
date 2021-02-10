import queue
from collections import deque
from helpers import display

def test_display_has_a_queue():
    assert isinstance(display.message_queue, queue.Queue)
    
def test_write_to_queue():
    assert display.message_queue.empty()
    display.message_queue.put("Hello World")
    assert not display.message_queue.empty()
    assert display.message_queue.get() == "Hello World"


class TestDisplayClass:
    
    def test_display_class_exists_and_has_a_message_buffer(self):
        oled = display.Display()
        assert oled._screen_line_buffer.maxlen == 5
        
    def test_write_to_line_buffer_appends_on_the_right(self):
        oled = display.Display()
        [oled._write_to_buffer(line=text) for text in ["1", "2"]]
        assert oled._screen_line_buffer == deque(["1", "2"])
        