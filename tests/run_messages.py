#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datarecorder import oleddisplay
import time

oleddisplay.init_display_thread()
greetees = ['Moon', 'Earth', 'Mars', 'Venus', 'Mercury', 'Saturn', 'Jupiter', 'Neptune', 'Uranus']
[oleddisplay.message_queue.put(f'Hello {x}') for x in greetees]
time.sleep(0.5)
oleddisplay.message_queue.join()
