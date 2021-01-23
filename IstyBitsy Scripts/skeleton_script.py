from node_radio import node_radio
import board

NODE_ID = 0xfe
SEND_PERIOD = 15

radio = node_radio.Radio(cs_pin=board.D7, reset_pin=board.D5, led_pin=board.D13,
                         node_id=NODE_ID, send_period=SEND_PERIOD)

radio.initial_sleep()
while True:
    radio.timer_reset()
    radio.wait_for_timer()
    radio.send_data([{'id': 0xfe, 'value': 999.99}])
