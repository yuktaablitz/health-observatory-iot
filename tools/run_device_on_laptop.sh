#!/bin/sh
# Runs the real device/main.py on the MicroPython unix port with fake sensors.
# Needs a MicroPython binary: MICROPYTHON=/path/to/micropython (default: micropython on PATH).
cd "$(dirname "$0")/.."
MP=${MICROPYTHON:-micropython}
MICROPYPATH="tools/mpy_fakes:device:device/lib" exec "$MP" device/main.py
