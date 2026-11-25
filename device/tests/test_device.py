"""Runs the ESP32 code on a laptop with fake MicroPython modules."""
import json
import os
import sys
import types

import pytest

HERE = os.path.dirname(__file__)
sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "lib")]


class FakeDHT:
    readings = []

    def __init__(self, pin):
        pass

    def measure(self):
        value = FakeDHT.readings.pop(0)
        if isinstance(value, Exception):
            raise value
        self.t, self.h = value

    def temperature(self):
        return self.t

    def humidity(self):
        return self.h


def install_fakes():
    machine = types.ModuleType("machine")
    machine.Pin = type("Pin", (), {"OUT": 1, "__init__": lambda s, *a, **k: None,
                                   "on": lambda s: None, "off": lambda s: None})
    machine.SoftI2C = object
    sys.modules["machine"] = machine
    sys.modules["network"] = types.ModuleType("network")
    dht = types.ModuleType("dht")
    dht.DHT22 = FakeDHT
    sys.modules["dht"] = dht
    sys.modules["ujson"] = json
    ws_pkg = types.ModuleType("uwebsockets")
    ws_pkg.client = types.ModuleType("uwebsockets.client")
    sys.modules["uwebsockets"] = ws_pkg
    sys.modules["uwebsockets.client"] = ws_pkg.client
    cfg = types.ModuleType("config")
    cfg.__dict__.update(PATIENT_ID="bed-01", SEND_INTERVAL_S=0, DHT22_PIN=14, STATUS_LED_PIN=2,
                        I2C_SCL_PIN=22, I2C_SDA_PIN=21, WIFI_SSID="x", WIFI_PASSWORD="y", WS_URL="wss://h/dev")
    sys.modules["config"] = cfg


install_fakes()
import main  # noqa: E402
from payload import build_message, valid_reading  # noqa: E402


class FakeSocket:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def send(self, text):
        if self.fail:
            raise OSError("ECONNRESET")
        self.sent.append(json.loads(text))


def test_build_message_shape():
    m = build_message("bed-01", 4, 30.44, 51.06, pulse_ir=812, pulse_red=640)
    assert m == {"action": "onMessage", "patient_id": "bed-01", "seq": 4, "temperature_c": 30.4,
                 "humidity": 51.1, "pulse_ir": 812, "pulse_red": 640}


@pytest.mark.parametrize("t,h,ok", [(25, 50, True), (-41, 50, False), (25, 101, False), (None, 50, False)])
def test_valid_reading(t, h, ok):
    assert valid_reading(t, h) is ok


def test_sends_reading_and_advances_seq():
    FakeDHT.readings = [(30.2, 48.0)]
    ws = FakeSocket()
    assert main.send_one(ws, None, 0) == 1
    assert ws.sent == [{"action": "onMessage", "patient_id": "bed-01", "seq": 0, "temperature_c": 30.2, "humidity": 48.0}]


def test_failed_sensor_read_is_skipped_not_sent():
    FakeDHT.readings = [OSError("sensor timeout"), (99.0, 50.0)]
    ws = FakeSocket()
    assert main.send_one(ws, None, 5) == 5      # DHT22 raised
    assert main.send_one(ws, None, 5) == 5      # 99 C is out of the DHT22 range
    assert ws.sent == []


def test_socket_error_is_raised_for_reconnect():
    FakeDHT.readings = [(25.0, 40.0)]
    with pytest.raises(OSError):
        main.send_one(FakeSocket(fail=True), None, 0)
