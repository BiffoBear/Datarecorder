# Required for all nodes.
from node_radio import node_radio
import board
# Specific to this node.
import adafruit_bme680

# Setup radio and status LED
RESET_PIN = board.D3
CS_PIN = board.D2
LED_PIN = board.D13
NODE_ID = 0x03
SEND_PERIOD = 60  # seconds

radio = node_radio.Radio(cs_pin=CS_PIN, reset_pin=RESET_PIN, led_pin=LED_PIN,
                         node_id=NODE_ID, send_period=SEND_PERIOD)

# Setup node speciic sensors, etc.
i2c = board.I2C()
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)

# Main loop
radio.initial_sleep()
while True:
    radio.timer_reset()
    radio.wait_for_timer()
    readings = [{'name': 'temperature', 'id': 0x05, 'value': bme680.temperature + 273.15},
            {'name': 'gas', 'id': 0x06, 'value': bme680.gas},
            {'name': 'humidity', 'id': 0x07, 'value': bme680.humidity},
            {'name': 'pressure', 'id': 0x08, 'value': bme680.pressure / 100},
            ]
    print(readings)
    radio.send_data(readings)
