"""Builds and validates the JSON message the ESP32 sends.

Kept free of MicroPython-only imports so it runs (and is unit-tested) on a laptop too.
"""

TEMP_MIN_C = -40.0   # DHT22 datasheet range
TEMP_MAX_C = 80.0
HUMIDITY_MIN = 0.0
HUMIDITY_MAX = 100.0


def valid_reading(temperature_c, humidity):
    """True when both values are numbers inside the DHT22's physical range."""
    try:
        t = float(temperature_c)
        h = float(humidity)
    except (TypeError, ValueError):
        return False
    return TEMP_MIN_C <= t <= TEMP_MAX_C and HUMIDITY_MIN <= h <= HUMIDITY_MAX


def build_message(patient_id, seq, temperature_c, humidity, pulse_ir=None, pulse_red=None):
    """Return the dict sent to the API Gateway `onMessage` route."""
    if not patient_id:
        raise ValueError("patient_id is required")
    if not valid_reading(temperature_c, humidity):
        raise ValueError("reading out of sensor range")
    msg = {
        "action": "onMessage",          # API Gateway route key
        "patient_id": patient_id,
        "seq": int(seq),                # lets the cloud spot dropped or repeated readings
        "temperature_c": round(float(temperature_c), 1),
        "humidity": round(float(humidity), 1),
    }
    if pulse_ir is not None and pulse_red is not None:
        msg["pulse_ir"] = int(pulse_ir)
        msg["pulse_red"] = int(pulse_red)
    return msg
