import oleddisplay
oleddisplay.global_display = oleddisplay.setup()
oleddisplay.message_queue.put(f'Hello Mars')
oleddisplay.read_message_queue_write_to_display(lines=oleddisplay.global_lines, display=oleddisplay.global_display)
