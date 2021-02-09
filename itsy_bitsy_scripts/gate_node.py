# Version 1.0 2021-01-29
# Required for all nodes.
from node_helper import node
import board

# Specific to this node.
import time
import digitalio

# Setup radio and status LED
RESET_PIN = board.D3
CS_PIN = board.D2
LED_PIN = board.D13
NODE_ID = 0x05
SEND_PERIOD = 30  # seconds

radio = node.Radio(
    cs_pin=CS_PIN,
    reset_pin=RESET_PIN,
    led_pin=LED_PIN,
    node_id=NODE_ID,
    send_period=SEND_PERIOD,
)

# Setup node specific sensors, etc.
gate_open = digitalio.DigitalInOut(board.D4)
gate_open.direction = digitalio.Direction.INPUT
gate_open.pull = digitalio.Pull.UP

gate_open_led = node.StatusLed(board.D12)

gate_was_open = gate_open.value
gate_open_led.value = not gate_was_open
radio.update_register(bit=0, status=gate_was_open)
radio.update_register(bit=1, status=not gate_was_open)
radio.send_data([])
timer_was_expired = True

# Main loop
while True:
    gate_is_open, timer_is_expired = gate_open.value, radio.timer_expired
    gate_open_led.value = gate_is_open
    if gate_is_open and not gate_was_open and timer_is_expired:
        radio.update_register(bit=0, status=gate_is_open)
        radio.update_register(bit=1, status=not gate_is_open)
        radio.send_data([])
    elif not gate_is_open and gate_was_open:
        radio.timer_reset()
    elif (
        not gate_is_open
        and not gate_was_open
        and timer_is_expired
        and not timer_was_expired
    ):
        radio.update_register(bit=0, status=gate_is_open)
        radio.update_register(bit=1, status=not gate_is_open)
        radio.send_data([])
    gate_was_open, timer_was_expired = gate_is_open, timer_is_expired
    time.sleep(0.5)
