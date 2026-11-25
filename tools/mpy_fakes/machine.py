# Fake ESP32 hardware so device/main.py runs on the MicroPython unix port.
class Pin:
    OUT = 1
    def __init__(self, *a, **k): pass
    def on(self): pass
    def off(self): pass

class SoftI2C:
    def __init__(self, *a, **k): raise OSError("no I2C on laptop")
