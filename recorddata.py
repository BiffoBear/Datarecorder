import time
from datarecorder import _main
from __config__ import RFM69_INTERRUPT_PIN, DB_URL

if __name__ == '__main__':
    _main.radio = _main.start_up(db_url=DB_URL, pi_irq_pin=RFM69_INTERRUPT_PIN)
    # finish_time = time.time() + 60
    try:
        # while time.time() < finish_time:
        while True:
            time.sleep(0.1)
    except Exception as e:
        raise e
    finally:
        _main.shut_down()
