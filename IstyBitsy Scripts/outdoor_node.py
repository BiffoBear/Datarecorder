# Version 1.0 2021-01-29
# Required for all nodes.
from node_helper import node
import board
# Specific to this node.
import time
import digitalio
import analogio
import adafruit_bme680
import adafruit_mcp9808

# Setup radio and status LED
RESET_PIN = board.D11
CS_PIN = board.D10
LED_PIN = board.D9
NODE_ID = 0x02
SEND_PERIOD = 60  # seconds

radio = node.Radio(cs_pin=CS_PIN, reset_pin=RESET_PIN, led_pin=LED_PIN,
                   node_id=NODE_ID, send_period=SEND_PERIOD)

# Setup node specific sensors, etc.


class MaxSonicSensor:

    def __init__(self, power_pin, value_pin, tank_height, m3_per_m):
        self.sensor_power = digitalio.DigitalInOut(power_pin)
        self.sensor_power.switch_to_output()
        self.sensor_power.value = False
        self.sensor_reading = analogio.AnalogIn(value_pin)
        self.m_per_point = 1 / 6715
        self.tank_height_m = tank_height
        self.tank_volume_m3_per_m = m3_per_m

    def read_sensor(self):
        self.sensor_power.value = True
        time.sleep(.1)
        raw_value = self.sensor_reading.value
        self.sensor_power.value = False
        return raw_value

    @property
    def volume(self):
        water_level = self.tank_height_m - self.read_sensor() * self.m_per_point
        return water_level * self.tank_volume_m3_per_m


class MiltoneEtape:

    def __init__(self, value_pin, depth_offset, length=30, reading_0=52800, reading_30_cm=3666):
        self.sensor_reading = analogio.AnalogIn(value_pin)
        self.reading_min = reading_0
        self.reading_max = reading_30_cm
        self.min_value = length / 100
        self.max_value = 0.0
        self.reading_range = self.reading_max - self.reading_min
        self.value_range = self.max_value - self.min_value
        self.depth_offset = depth_offset

    @property
    def water_depth(self):
        reading = self.sensor_reading.value
        return (reading - self.reading_min) / self.reading_range * self.value_range + self.min_value + self.depth_offset

    @property
    def water_level_below_max(self):
        return self.min_value + self.depth_offset - self.water_depth


class PressureSensorMPX5700AP:

    def __init__(self, value_pin, reading_0=2621, reading_700=61603):
        self.sensor_reading = analogio.AnalogIn(value_pin)
        self.reading_min = reading_0
        self.reading_max = reading_700
        self.min_value = 0
        self.max_value = 700
        self.reading_range = self.reading_max - self.reading_min
        self.value_range = self.max_value - self.min_value

    @property
    def pressure(self):
        reading = self.sensor_reading.value
        return (reading - self.reading_min) / self.reading_range * self.value_range + self.min_value


i2c = board.I2C()
# BME680 Temperature, Pressure, Humidity, Air Quality (outdoors)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
# MCP9808 Temperature (roof space)
mcp = adafruit_mcp9808.MCP9808(i2c)
# MaxSonicSensor (house water tanks)
house_tank = MaxSonicSensor(board.D12, board.A3, 1.65, 1.951)
# MaxSonicSensor (irrigation water tank)
irrigation_tank = MaxSonicSensor(board.D13, board.A2, 1.52, 0.638)
# Miltone Etape 30 cm (pond depth)
fishpond = MiltoneEtape(board.A4, 0.08)
# MPX5700AP pressure sensor (irrigation system pressure)
irrigation_pressure = PressureSensorMPX5700AP(board.A5)

# Main loop
radio.initial_sleep()
while True:
    radio.timer_reset()
    radio.wait_for_timer()
    readings = [{'name': 'temperature', 'id': 0x05, 'value': bme680.temperature + 273.15},
                {'name': 'gas', 'id': 0x06 'value': bme680.gas},
                {'name': 'humidity', 'id': 0x07, 'value': bme680.humidity},
                {'name': 'pressure', 'id': 0x08 'value': bme680.pressure / 100},
                {'name': 'house_tank', 'id': 0x09, 'value': house_tank.volume},
                {'name': 'irrigation_tank', 'id': 0x0a, 'value': irrigation_tank.volume},
                {'name': 'irrigation_pressure', 'id': 0x0b, 'value': irrigation_pressure.pressure},
                {'name': 'fishpond_depth', 'id': 0x0c, 'value': fishpond.water_depth},
                {'name': 'fishpond_level', 'id': 0x0d, 'value': fishpond.water_level_below_max},
                {'name': 'Roof Temperature', 'id': 0x0e, 'value': mcp.temperature + 273.15},
                ]
    radio.send_data(readings)
