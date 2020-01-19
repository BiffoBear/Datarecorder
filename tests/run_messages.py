import oleddisplay
oleddisplay.global_display = oleddisplay.setup()
oleddisplay.init_display_thread()
oleddisplay.message_queue.put(f'Hello Mars')
oleddisplay.message_queue.put(f'Hello Earth')
oleddisplay.message_queue.put(f'Hello Venus')
oleddisplay.message_queue.put(f'Hello Pluto')

oleddisplay.message_queue.join()