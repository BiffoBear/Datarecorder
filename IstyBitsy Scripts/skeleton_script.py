# Version 1.0 2021-01-29
# Required for all nodes.
from node_helper import node
import board
# Specific to this node.

# Setup radio and status LED
RESET_PIN = board.D7
CS_PIN = board.D9
LED_PIN = board.D13
NODE_ID = 0xfe
SEND_PERIOD = 60  # seconds

radio = node.Radio(cs_pin=CS_PIN, reset_pin=RESET_PIN, led_pin=LED_PIN,
                   node_id=NODE_ID, send_period=SEND_PERIOD)

# Setup node specific sensors, etc.

# Main loop
radio.initial_sleep()
while True:
    radio.timer_reset()
    radio.wait_for_timer()
    radio.send_data([{'id': 0xfe, 'value': 999.99}])
