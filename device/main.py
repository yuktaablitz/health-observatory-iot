"""Health Observatory - ESP32 firmware (MicroPython).

Reads a DHT22 (temperature, humidity) and, if wired, a MAX30100 pulse oximeter,
then sends one JSON reading every SEND_INTERVAL_S seconds over a secure WebSocket
to AWS API Gateway. Reconnects Wi-Fi and the WebSocket on failure.
"""
import time
import ujson
import network
import dht
from machine import Pin

import config
from payload import build_message
import uwebsockets.client

led = Pin(config.STATUS_LED_PIN, Pin.OUT)
dht_sensor = dht.DHT22(Pin(config.DHT22_PIN))


def connect_wifi(timeout_s=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout_s:
                raise OSError("Wi-Fi connect timed out")
            time.sleep(0.5)
    print("Wi-Fi:", wlan.ifconfig()[0])
    return wlan


def connect_websocket():
    ws = uwebsockets.client.connect(config.WS_URL)
    print("WebSocket connected")
    return ws


def init_pulse_sensor():
    """Return a MAX30100 object, or None if it is not wired."""
    try:
        import max30100
        from smbus import SMBus
        bus = SMBus(scl=Pin(config.I2C_SCL_PIN), sda=Pin(config.I2C_SDA_PIN))
        sensor = max30100.MAX30100(i2c=bus)
        sensor.enable_spo2()
        print("MAX30100 found")
        return sensor
    except Exception as e:  # sensor missing or not responding
        print("MAX30100 not used:", e)
        return None


def read_vitals(pulse):
    dht_sensor.measure()
    temp_c = dht_sensor.temperature()
    humidity = dht_sensor.humidity()
    ir = red = None
    if pulse:
        pulse.read_sensor()
        ir, red = pulse.ir, pulse.red
    return temp_c, humidity, ir, red


def send_one(ws, pulse, seq):
    """Read sensors and send one message. Returns the next sequence number.

    A failed or out-of-range sensor read is skipped (not sent); a socket error
    is raised so run() can reconnect.
    """
    try:
        temp_c, humidity, ir, red = read_vitals(pulse)
        msg = build_message(config.PATIENT_ID, seq, temp_c, humidity, ir, red)
    except (ValueError, OSError) as e:
        print("skipped reading:", e)
        return seq
    ws.send(ujson.dumps(msg))
    print("sent", msg)
    return seq + 1


def run():
    pulse = init_pulse_sensor()
    seq = 0
    backoff_s = 1
    while True:
        ws = None
        try:
            connect_wifi()
            ws = connect_websocket()
            led.on()
            backoff_s = 1
            while True:
                seq = send_one(ws, pulse, seq)
                time.sleep(config.SEND_INTERVAL_S)
        except Exception as e:
            led.off()
            print("connection lost:", e, "- retrying in", backoff_s, "s")
            try:
                if ws:
                    ws.close()
            except Exception:
                pass
            time.sleep(backoff_s)
            backoff_s = min(backoff_s * 2, 60)


if __name__ == "__main__":
    run()
