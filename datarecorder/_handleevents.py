import logging
import threading
import queue
import urllib.request

event_queue = queue.Queue()
event_actions = {0x05: {0x00: {'url': 'http://google.com', 'delay': 0}}}


def read_event_queue_handle_event():
    """Take events from the queue and act on them."""
    logger.debug('read_event_queue_handle_event called')
    global event_queue
    try:
        event = event_queue.get()
        event_action = event_actions[event[node][code]]
        if event_action['delay']:
            time.sleep(event_action[delay])
        with urllib.request.urlopen(event_action['url']) as response:
            if response.status != 200:
                raise HTTPError('Bad response from server')    
        response = urllib.request(url)
    except queue.Empty:
        logger.error('Event thread called with empty queue')
    except KeyError:
        logger.error(f'Event {event[code]:02X} from node {event[node]:02X} does not exist')
    except HTTPError:
        logger.error('Bad response from server')
    finally:
        event_queue.task_done()


def write_event_to_queue(event=None):
    logger.debug('write_event_to_queue called')
    try:
        event_queue.put_nowait(message_text)
    except queue.Full:
        pass


def init_event_thread():
    logger.debug(f'init_event_thread called')
    event_thread = threading.Thread(target=loop_read_event_queue)
    event_thread.daemon = True
    event_thread.start()
    return event_thread


def loop_read_event_queue():
    logger.debug(f'loop_read_event_queue called')
    global global_display
    while True:
        global_display = read_message_queue_write_to_display(display=global_display)
