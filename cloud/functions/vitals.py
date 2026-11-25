"""Pure logic shared by the Lambda handlers (no AWS calls, easy to unit test)."""
import os

NORMAL, ELEVATED, HIGH = 0, 1, 2
STATUS = {NORMAL: "normal", ELEVATED: "elevated", HIGH: "high - check-up needed"}


def thresholds():
    """Upper bound of NORMAL and of ELEVATED, in deg C.

    Defaults match the original classroom demo, where the DHT22 read room air
    (~29-31 C). For a body-temperature probe set NORMAL_MAX_C=37.5, ELEVATED_MAX_C=38.5.
    """
    normal_max = float(os.environ.get("NORMAL_MAX_C", "30.0"))
    elevated_max = float(os.environ.get("ELEVATED_MAX_C", "31.0"))
    if normal_max >= elevated_max:
        raise ValueError("NORMAL_MAX_C must be below ELEVATED_MAX_C")
    return normal_max, elevated_max


def classify(temperature_c):
    """Map a temperature to NORMAL / ELEVATED / HIGH with no gaps between bands.

    Fixes the original if/elif chain, which returned nothing for 29 < t < 30.
    """
    normal_max, elevated_max = thresholds()
    t = float(temperature_c)
    if t < normal_max:
        return NORMAL
    if t <= elevated_max:
        return ELEVATED
    return HIGH


def parse_reading(body):
    """Validate a device message. Returns a clean dict or raises ValueError."""
    if not isinstance(body, dict):
        raise ValueError("body must be a JSON object")
    patient_id = body.get("patient_id")
    if not isinstance(patient_id, str) or not patient_id.strip():
        raise ValueError("patient_id is required")
    try:
        temperature_c = float(body["temperature_c"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("temperature_c must be a number")
    if not -40.0 <= temperature_c <= 80.0:
        raise ValueError("temperature_c outside DHT22 range")
    reading = {"patient_id": patient_id.strip(), "temperature_c": temperature_c}
    for key in ("humidity", "seq", "pulse_ir", "pulse_red"):
        if body.get(key) is not None:
            reading[key] = body[key]
    return reading
