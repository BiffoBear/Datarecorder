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
SEND_PERIOD = 60  # seconds

radio = node.Radio(cs_pin=CS_PIN, reset_pin=RESET_PIN, led_pin=LED_PIN,
                         node_id=NODE_ID, send_period=SEND_PERIOD)

# Setup node specific sensors, etc.
gate_closed = digitalio.DigitalInOut(board.D4)
gate_closed.direction = digitalio.Direction.INPUT
gate_closed.pull = digitalio.Pull.UP

gate_closed_led = node.StatusLed(board.D12)


def update_and_send_data(*, gate_closed=None):
    gate_open = not gate_closed
    radio.update_register(bit=1, state=gate_open)
    radio.send_data([])


# Main loop
gate_closed_led.value = gate_closed.value
if not gate_closed.value:
    update_and_send_data(gate_closed=False)
while True:
    while gate_closed.value == gate_closed_led.value:
        time.sleep(0.5)
    gate_closed_state = gate_closed.value
    update_and_send_data(gate_closed=gate_closed_state)
    gate_closed_led.value = gate_closed_state
