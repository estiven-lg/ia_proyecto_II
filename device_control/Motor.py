import math
import time

from device_control.PCA9685 import PCA9685
from device_control.ADC import ADC


class Motor:
    MAX_DUTY = 4095

    def __init__(self, address=0x40):
        self.pwm = PCA9685(address, debug=False)
        self.pwm.setPWMFreq(50)

        self.time_proportion = 2.5
        self.adc = ADC()

        # Mapeo de ruedas:
        # (canal_forward, canal_backward)
        self.wheels = {
            "left_upper": (1, 0),
            "left_lower": (2, 3),
            "right_upper": (6, 7),
            "right_lower": (5, 4),
        }

    def _clamp_duty(self, duty):
        return max(-self.MAX_DUTY, min(self.MAX_DUTY, int(duty)))

    def _set_wheel(self, wheel_name, duty):
        duty = self._clamp_duty(duty)

        forward_channel, backward_channel = self.wheels[wheel_name]

        if duty > 0:
            self.pwm.setMotorPwm(backward_channel, 0)
            self.pwm.setMotorPwm(forward_channel, duty)

        elif duty < 0:
            self.pwm.setMotorPwm(forward_channel, 0)
            self.pwm.setMotorPwm(backward_channel, abs(duty))

        else:
            self.pwm.setMotorPwm(forward_channel, self.MAX_DUTY)
            self.pwm.setMotorPwm(backward_channel, self.MAX_DUTY)

    def set_motor_model(self, left_upper, left_lower, right_upper, right_lower):
        self._set_wheel("left_upper", left_upper)
        self._set_wheel("left_lower", left_lower)
        self._set_wheel("right_upper", right_upper)
        self._set_wheel("right_lower", right_lower)

    # =========================
    # MOVIMIENTOS BÁSICOS
    # =========================

    def forward(self, speed=2000):
        self.set_motor_model(speed, speed, speed, speed)

    def backward(self, speed=2000):
        self.set_motor_model(-speed, -speed, -speed, -speed)

    def left(self, speed=2000):
        self.set_motor_model(-speed, -speed, speed, speed)

    def right(self, speed=2000):
        self.set_motor_model(speed, speed, -speed, -speed)

    def stop(self):
        self.set_motor_model(0, 0, 0, 0)

    # =========================
    # ROTACIÓN AVANZADA
    # =========================

    def rotate(self, angle):
        bat_compensate = 7.5 / (self.adc.recvADC(2) * 3)

        W = 2000

        VY = int(2000 * math.cos(math.radians(angle)))
        VX = -int(2000 * math.sin(math.radians(angle)))

        FR = VY - VX + W
        FL = VY + VX - W
        BL = VY - VX - W
        BR = VY + VX + W

        self.set_motor_model(FL, BL, FR, BR)

        time.sleep(
            5 * self.time_proportion * bat_compensate / 1000
        )

        self.stop()
