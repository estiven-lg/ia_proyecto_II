from device_control.ADC import ADC


class LightSensor:
    def __init__(self):
        self.adc = ADC()

    def read_left(self):
        return self.adc.read_voltage(0)

    def read_right(self):
        return self.adc.read_voltage(1)

    def read_both(self):
        return {
            "left": self.read_left(),
            "right": self.read_right()
        }

    def difference(self):
        return abs(self.read_left() - self.read_right())