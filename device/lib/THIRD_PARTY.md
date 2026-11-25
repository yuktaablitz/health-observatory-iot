Vendored libraries (modified where noted):

- `uwebsockets/` - MicroPython WebSocket client, from danni/uwebsockets (MIT). Modified: TLS with SNI.
- `max30100.py` - MAX30100 driver, from mfitzp/max30100 (MIT). Modified: ESP32 I2C, register fixes.
- `logging.py` - from micropython-lib (MIT).
- `smbus.py` - small py-smbus style wrapper over SoftI2C, written for this project.
