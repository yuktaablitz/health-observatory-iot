# Replays a fixed series of DHT22 readings: normal, elevated, high, a failed read, then normal.
SERIES = [(28.4, 51.0), (30.6, 50.2), (32.1, 49.8), None, (29.0, 50.0)]
_i = [0]

class DHT22:
    def __init__(self, pin): pass
    def measure(self):
        v = SERIES[_i[0] % len(SERIES)]
        _i[0] += 1
        if v is None:
            raise OSError("sensor timeout")
        self._v = v
    def temperature(self): return self._v[0]
    def humidity(self): return self._v[1]
