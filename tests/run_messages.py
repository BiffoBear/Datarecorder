import oleddisplay
import time
oleddisplay.global_display = oleddisplay.setup_hardware_oled()
oleddisplay.init_display_thread()
greetees = ['Moon', 'Earth', 'Mars', 'Venus', 'Mercury', 'Saturn', 'Jupiter', 'Neptune', 'Uranus']
[oleddisplay.message_queue.put(f'Hello {x}') for x in greetees]
time.sleep(0.5)
oleddisplay.message_queue.join()