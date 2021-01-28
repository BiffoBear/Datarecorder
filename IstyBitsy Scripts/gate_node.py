import time
import board
from digitalio import DigitalInOut, Direction, Pull
from node_radio import node_radio

# LED setup.
led = node_radio.StatusLed(board.D13)

# For Gemma M0, Trinket M0, Metro M0 Express, ItsyBitsy M0 Express, Itsy M4 Express, QT Py M0
switch = DigitalInOut(board.D2)
# switch = DigitalInOut(board.D5)  # For Feather M0 Express, Feather M4 Express
# switch = DigitalInOut(board.D7)  # For Circuit Playground Express
switch.direction = Direction.INPUT
switch.pull = Pull.UP

switch_status = switch.value
led.value = switch_status
while True:
    if switch.value is not switch_status:
        switch_status = switch.value
        led.value = switch.value
        print(f'Send status gate open is {switch_status}')
    time.sleep(1)
