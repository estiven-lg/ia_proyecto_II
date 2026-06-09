import RPi.GPIO as GPIO


class Buzzer:
    def __init__(self, pin=17):
        self.pin = pin

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    def on(self):
        GPIO.output(self.pin, True)

    def off(self):
        GPIO.output(self.pin, False)

    def beep(self, duration=0.2):
        import time

        self.on()
        time.sleep(duration)
        self.off()

    def cleanup(self):
        GPIO.cleanup(self.pin)