from device_control.PCA9685 import PCA9685
import time


class Servo:
    def __init__(self, address=0x40):
        self.pwm = PCA9685(address, debug=False)
        self.pwm.setPWMFreq(50)

        self.channel_map = {
            0: 8,
            1: 9,
            2: 10,
            3: 11,
            4: 12,
            5: 13,
            6: 14,
            7: 15,
        }

        self.center_all()

    def set_angle(self, servo_id, angle, error=10):
        angle = max(0, min(180, int(angle)))

        if servo_id not in self.channel_map:
            raise ValueError(f"Servo {servo_id} no válido")

        pulse = 500 + int((angle + error) / 0.09)

        self.pwm.setServoPulse(
            self.channel_map[servo_id],
            pulse
        )

    def center(self, servo_id):
        self.set_angle(servo_id, 90)

    def center_all(self):
        for servo_id in self.channel_map:
            self.center(servo_id)

        time.sleep(0.5)