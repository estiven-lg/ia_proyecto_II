from device_control.Led import LED
import time

led = LED()

print("Rojo")
led.set_all(255, 0, 0)
time.sleep(2)

print("Verde")
led.set_all(0, 255, 0)
time.sleep(2)

print("Azul")
led.set_all(0, 0, 255)
time.sleep(2)

led.off()