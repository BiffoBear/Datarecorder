import analogio
# noinspection PyPackageRequirements
import board
import time
import math

voltage_pin = analogio.AnalogIn(board.A1)
emon = {'house': {'v_pin': voltage_pin,
                  'i_pin': analogio.AnalogIn(board.A2),
                  'v': [],
                  'i': [],
                  },
        'garden': {'v_pin': voltage_pin,
                   'i_pin': analogio.AnalogIn(board.A3),
                   'v': [],
                   'i': [],
                   },
        'pool': {'v_pin': voltage_pin,
                 'i_pin': analogio.AnalogIn(board.A4),
                 'v': [],
                 'i': [],
                 },
        'kitchen': {'v_pin': voltage_pin,
                    'i_pin': analogio.AnalogIn(board.A5),
                    'v': [],
                    'i': [],
                    },
        }

PHASE_CAL = 1.2
SAMPLE_TIME = 0.15
dummy_data = {'v': [int((math.sin(x / 10) + 1) * 32768) for x in range(1000)],
              'i': [int((math.sin(x / 10) + 1) * 32000) for x in range(1000)],
              }


def filter_phaseshift_and_calibrate_list(readings_dict, phaseshift):
    volts = readings_dict['v']
    maxima = [x for x in range(1, len(volts)-1) if volts[x-1] < volts[x] > volts[x+1]]
    for key in readings_dict:
        readings = readings_dict[key]
        one_cycle = readings[maxima[0]:maxima[1]]
        offset = sum(one_cycle) / len(one_cycle)
        readings = readings[maxima[0]:maxima[-1]]
        readings_dict[key] = [x - offset for x in readings]
    y = readings_dict['v']
    readings_dict['v'] = [y[x-1] + phaseshift * (y[x] - y[x-1]) for x in range(1, len(y))]
    return readings_dict


def sample_electricity_a(current_set, duration):
    v_readings = []
    i_readings = []
    v_pin = current_set['v_pin']
    i_pin = current_set['i_pin']
    start_time = time.monotonic()
    while time.monotonic() < start_time + duration:
        v_readings.append(v_pin.value)
        i_readings.append(i_pin.value)
    print(len(v_readings))
    current_set['v'] = v_readings
    current_set['i'] = i_readings
    return current_set


# print(filter_list(dummy_data)['v'][:100])
st = time.monotonic()
sample_electricity_a(emon['house'], SAMPLE_TIME)
filter_phaseshift_and_calibrate_list(dummy_data, PHASE_CAL)
print(time.monotonic() - st)
