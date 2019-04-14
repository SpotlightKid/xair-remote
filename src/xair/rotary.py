# -*- coding: utf-8 -*-
#
# rotary.py
#
"""A class to handle rotary encoders on a Rasberry Pi or NextThing C.H.I.P."""

import CHIP_IO.GPIO as GPIO


ENC_STATES = (
    0,   # 00 00
    -1,  # 00 01
    1,   # 00 10
    0,   # 00 11
    1,   # 01 00
    0,   # 01 01
    0,   # 01 10
    -1,  # 01 11
    -1,  # 10 00
    0,   # 10 01
    0,   # 10 10
    1,   # 10 11
    0,   # 11 00
    1,   # 11 01
    -1,  # 11 10
    0    # 11 11
)
ACCEL_THRESHOLD = 5


class RotaryEncoder:
    def __init__(self, pin_dt, pin_clk, pullup=GPIO.PUD_OFF, clicks=1,
                 min_val=0, max_val=100, accel=0, reverse=False):
        self.pin_dt = pin_dt
        self.pin_clk = pin_clk
        self.min_val = min_val * clicks
        self.max_val = max_val * clicks
        self.accel = int((max_val - min_val) / 100 * accel)
        self.max_accel = int((max_val - min_val) / 2)
        self.clicks = clicks
        self.reverse = 1 if reverse else -1
        self._value = 0
        self._readings = 0
        self._state = 0
        self.cur_accel = 0

        GPIO.setup(pin_dt, GPIO.IN, pullup)
        GPIO.setup(pin_clk, GPIO.IN, pullup)
        self.set_callbacks(self._cb)

    def set_callbacks(self, callback=None):
        GPIO.add_event_detect(self.pin_dt, GPIO.BOTH, callback=callback)
        GPIO.add_event_detect(self.pin_clk, GPIO.BOTH, callback=callback)

    def _cb(self, ch):
        self._readings = (self._readings << 2 | GPIO.input(self.pin_clk) << 1 |
                          GPIO.input(self.pin_dt)) & 0x0f
        self._state = ENC_STATES[self._readings] * self.reverse

        if self._state:
            self.cur_accel = min(self.max_accel, self.cur_accel + self.accel)

            self._value = min(self.max_val, max(self.min_val, self._value +
                              (1 + (self.cur_accel >> ACCEL_THRESHOLD)) *
                              self._state))

    def close(self):
        GPIO.remove_event_detect(self.pin_clk)
        GPIO.remove_event_detect(self.pin_dt)

    @property
    def value(self):
        return self._value // self.clicks

    def reset(self):
        self._value = 0


def _test():
    import time
    e = RotaryEncoder('XIO-P2', 'XIO-P4')
    oldval = 0

    try:
        while True:
            if e.value != oldval:
                oldval = e.value
                print(oldval)
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        e.close()


if __name__ == '__main__':
    _test()
