import time
import math
import node_radio
import analogio
import board
import ulab

DEBUGGING = True

# def __init__(self, *, cs_pin=None, reset_pin=None, led_pin=None, node_id=None, send_freq=None):
radio = node_radio(cs_pin=board.D7, reset_pin=board.D5, led_pin=board.D13, node_id=0xfe, send_freq=15)

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

sensors = [{'name': 'voltage', 'adc_pin': voltage_pin, 'calibration_coeff': VOLTAGE_COEFF,
            'zero_threshold': VOLTAGE_0_THRESHOLD, 'accumulated_readings': []},
           {'name': 'house_current_pin', 'adc_pin': house_current_pin, 'calibration_coeff': CURRENT_COEFF, 'zero_threshold': CURRENT_0_THRESHOLD,
            'accumulated_readings': [], 'value': 0.0},
           {'name': 'kitchen_current_pin', 'adc_pin': kitchen_current_pin, 'calibration_coeff': CURRENT_COEFF, 'zero_threshold': CURRENT_0_THRESHOLD,
            'accumulated_readings': [], 'value': 0.0},
           {'name': 'pool_current_pin', 'adc_pin': pool_current_pin, 'calibration_coeff': CURRENT_COEFF, 'zero_threshold': CURRENT_0_THRESHOLD,
            'accumulated_readings': [], 'value': 0.0},
           {'name': 'garden_current_pin', 'adc_pin': garden_current_pin, 'calibration_coeff': CURRENT_COEFF, 'zero_threshold': CURRENT_0_THRESHOLD,
            'accumulated_readings': [], 'value': 0.0},
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
        elif (not gate) and (lower_gate_limit > reading) or (reading > upper_gate_limit):
            gate = True
    return crossing_list


print('Starting...')
radio.initial_sleep()
while True:
    radio.timer_reset()
    sensors = reset_data(sensors, 'accumulated_readings')
    while radio.timer_remaining > 0.5:
        for sensor in sensors:
            raw_data = []
            adc_to_read = sensor['adc_pin']
            for _ in range(1000):
                raw_data.append(adc_to_read.value)
            xings = find_crossings(raw_data)[:4]

            try:
                two_cycles = raw_data[xings[0]:xings[-1]]
                if len(two_cycles) < 600:
                    two_cycles = raw_data
            except IndexError:
                two_cycles = raw_data
            mid_point = int(ulab.numerical.mean(two_cycles))
            data_shifted_and_squared = [(x - mid_point) ** 2 for x in two_cycles]
            value = math.sqrt(ulab.numerical.sum(data_shifted_and_squared) / len(data_shifted_and_squared))
            value *= sensor['calibration_coeff']
            if value < sensor['zero_threshold']:
                value = 0
            sensor['accumulated_readings'].append(value)

            if DEBUGGING:
                print('**********')
                print(sensor['name'])
                print(len(two_cycles))
                print(f"max = {max(two_cycles)}")
                print(f"min = {min(two_cycles)}")
                print(f"Reading = {value}")

    for sensor in sensors:
        sensor['value'] = ulab.numerical.mean(sensor['accumulated_readings'])
    if DEBUGGING:
        print('==================')
        print(f'Points {len(sensors[0]["accumulated_readings"])}')
        for sensor in sensors:
            print(f"{sensor['name']} - {sensor['value']}")
        print('==================')
        time.sleep(5)
    else:
        while not radio.timer_expired:
            time.sleep(0.1)
        radio.send(sensors)
