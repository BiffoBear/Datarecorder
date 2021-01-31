import time
import board
import digitalio

pulses = digitalio.DigitalInOut(board.D13)
pulses.direction = digitalio.Direction.INPUT

while True:
    sample_duration = 0.5
    stop_time = time.monotonic() + sample_duration
    pulse_counter = 0
    old_state = pulses.value
    while time.monotonic() < stop_time:
        if old_state != pulses.value:
            pulse_counter = pulse_counter + 1
            old_state = not old_state
    print(pulse_counter)
    print(pulse_counter / (2 * sample_duration))
    time.sleep(0.5)
