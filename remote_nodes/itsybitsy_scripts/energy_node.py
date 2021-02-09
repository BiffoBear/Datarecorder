# Version 1.0 2021-01-29
# Required for all nodes.
from node_helper import node
import board

# Specific to this node.
import time
import math
import ulab
import analogio

# Setup radio and status LED
RESET_PIN = board.D7
CS_PIN = board.D5
LED_PIN = board.D10
NODE_ID = 0x03
SEND_PERIOD = 60  # seconds

radio = node.Radio(
    cs_pin=CS_PIN,
    reset_pin=RESET_PIN,
    led_pin=LED_PIN,
    node_id=NODE_ID,
    send_period=SEND_PERIOD,
)

# Setup node specific sensors, etc.
# Setup reading pins
voltage_pin = analogio.AnalogIn(board.A0)
house_current_pin = analogio.AnalogIn(board.A1)
kitchen_current_pin = analogio.AnalogIn(board.A4)
pool_current_pin = analogio.AnalogIn(board.A3)
garden_current_pin = analogio.AnalogIn(board.A2)

# Sensor reading settings
VOLTAGE_COEFF = 223 * 3.3 / 2 ** 16
VOLTAGE_0_THRESHOLD = 30
CURRENT_COEFF = 30 * 3.3 / 2 ** 16
CURRENT_0_THRESHOLD = 0.09
sensors = [
    {
        "name": "voltage",
        "adc_pin": voltage_pin,
        "calibration_coeff": VOLTAGE_COEFF,
        "zero_threshold": VOLTAGE_0_THRESHOLD,
        "accumulated_readings": [],
        "id": 0x0F,
        "value": 0.0,
    },
    {
        "name": "house_current_pin",
        "adc_pin": house_current_pin,
        "calibration_coeff": CURRENT_COEFF,
        "zero_threshold": CURRENT_0_THRESHOLD,
        "accumulated_readings": [],
        "id": 0x10,
        "value": 0.0,
    },
    {
        "name": "kitchen_current_pin",
        "adc_pin": kitchen_current_pin,
        "calibration_coeff": CURRENT_COEFF,
        "zero_threshold": CURRENT_0_THRESHOLD,
        "accumulated_readings": [],
        "id": 0x13,
        "value": 0.0,
    },
    {
        "name": "pool_current_pin",
        "adc_pin": pool_current_pin,
        "calibration_coeff": CURRENT_COEFF,
        "zero_threshold": CURRENT_0_THRESHOLD,
        "accumulated_readings": [],
        "id": 0x12,
        "value": 0.0,
    },
    {
        "name": "garden_current_pin",
        "adc_pin": garden_current_pin,
        "calibration_coeff": CURRENT_COEFF,
        "zero_threshold": CURRENT_0_THRESHOLD,
        "accumulated_readings": [],
        "id": 0x11,
        "value": 0.0,
    },
]


def reset_data(sensors_to_reset, item_to_reset):
    for element in sensors_to_reset:
        element[item_to_reset] = []
    return sensors_to_reset


def find_crossings(readings):
    min_reading = ulab.numerical.min(readings)
    max_reading = ulab.numerical.max(readings)
    reading_range = max_reading - min_reading
    centre_point = reading_range // 2 + min_reading
    lower_crossing_limit = centre_point - reading_range // 64
    upper_crossing_limit = centre_point + reading_range // 64
    lower_gate_limit = centre_point - reading_range // 4
    upper_gate_limit = centre_point + reading_range // 4
    crossing_list = []
    gate = True
    for index, reading in enumerate(readings):
        if gate and (lower_crossing_limit < reading < upper_crossing_limit):
            crossing_list.append(index)
            gate = False
        elif (
            (not gate) and (lower_gate_limit > reading) or (reading > upper_gate_limit)
        ):
            gate = True
    return crossing_list


# Main loop
radio.initial_sleep()
while True:
    radio.timer_reset()
    sensors = reset_data(sensors, "accumulated_readings")
    while radio.timer_remaining > 0.5:
        for sensor in sensors:
            raw_data = []
            adc_to_read = sensor["adc_pin"]
            for _ in range(1000):
                raw_data.append(adc_to_read.value)
            xings = find_crossings(raw_data)[:4]

            try:
                two_cycles = raw_data[xings[0] : xings[-1]]
                if len(two_cycles) < 600:
                    two_cycles = raw_data
            except IndexError:
                two_cycles = raw_data
            mid_point = int(ulab.numerical.mean(two_cycles))
            data_shifted_and_squared = [(x - mid_point) ** 2 for x in two_cycles]
            value = math.sqrt(
                ulab.numerical.sum(data_shifted_and_squared)
                / len(data_shifted_and_squared)
            )
            value *= sensor["calibration_coeff"]
            if value < sensor["zero_threshold"]:
                value = 0
            sensor["accumulated_readings"].append(value)

    for sensor in sensors:
        sensor["value"] = ulab.numerical.mean(sensor["accumulated_readings"])
    while not radio.timer_expired:
        time.sleep(0.1)
    radio.send_data(sensors)
