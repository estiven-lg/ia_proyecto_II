import time
import RPi.GPIO as GPIO


class Ultrasonic:
    def __init__(self, trigger_pin=27, echo_pin=22, max_distance=300):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.max_distance = max_distance
        self.timeout = max_distance * 60

        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

    def pulse_in(self, pin, level, timeout):
        start = time.time()

        while GPIO.input(pin) != level:
            if (time.time() - start) > timeout * 0.000001:
                return 0

        start = time.time()

        while GPIO.input(pin) == level:
            if (time.time() - start) > timeout * 0.000001:
                return 0

        return (time.time() - start) * 1000000

    def get_distance(self):
        readings = []

        for _ in range(5):
            GPIO.output(self.trigger_pin, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(self.trigger_pin, GPIO.LOW)

            ping_time = self.pulse_in(
                self.echo_pin,
                GPIO.HIGH,
                self.timeout
            )

            distance = ping_time * 340.0 / 2.0 / 10000.0
            readings.append(distance)

        readings.sort()
        distance = readings[2]

        if distance == 0:
            return 255

        return int(distance)

    def cleanup(self):
        GPIO.cleanup()