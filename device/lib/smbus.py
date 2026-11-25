"""Minimal py-smbus style wrapper over MicroPython's SoftI2C.

The MAX30100 driver was written for Raspberry Pi's `smbus`; this gives it the
same read/write calls on an ESP32. Uses composition instead of subclassing
machine.I2C, which newer MicroPython builds do not allow to be subclassed.
"""
from machine import Pin, SoftI2C


class SMBus:
    def __init__(self, scl, sda, freq=100000):
        self._i2c = SoftI2C(scl=scl, sda=sda, freq=freq)

    def read_byte_data(self, addr, register):
        return self._i2c.readfrom_mem(addr, register, 1)[0]

    def read_i2c_block_data(self, addr, register, length):
        return self._i2c.readfrom_mem(addr, register, length)

    def write_byte_data(self, addr, register, data):
        self._i2c.writeto_mem(addr, register, bytes([data & 0xFF]))
