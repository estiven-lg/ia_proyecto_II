import smbus
import time


class ADC:
    ADDRESS = 0x48
    PCF8591_CMD = 0x40
    ADS7830_CMD = 0x84

    def __init__(self, bus_id=1):
        self.bus = smbus.SMBus(bus_id)
        self.chip_type = self._detect_chip()

    def _detect_chip(self):
        value = self.bus.read_byte_data(self.ADDRESS, 0xF4)
        return "PCF8591" if value < 150 else "ADS7830"

    def _read_pcf8591(self, channel):
        readings = [
            self.bus.read_byte_data(
                self.ADDRESS,
                self.PCF8591_CMD + channel
            )
            for _ in range(9)
        ]

        readings.sort()
        return readings[4]

    def _read_ads7830(self, channel):
        command = self.ADS7830_CMD | (
            (((channel << 2) | (channel >> 1)) & 0x07) << 4
        )

        self.bus.write_byte(self.ADDRESS, command)

        while True:
            value1 = self.bus.read_byte(self.ADDRESS)
            value2 = self.bus.read_byte(self.ADDRESS)

            if value1 == value2:
                return value1

    def read_voltage(self, channel):
        if self.chip_type == "PCF8591":
            raw = self._read_pcf8591(channel)
            return round(raw / 256.0 * 3.3, 2)

        raw = self._read_ads7830(channel)
        return round(raw / 255.0 * 3.3, 2)

    def read_battery(self):
        return self.read_voltage(2) * 5

    def close(self):
        self.bus.close()