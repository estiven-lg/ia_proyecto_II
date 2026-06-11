from model.vision import Vision
from device_control.Led import LED
from device_control.Motor import Motor
from device_control.Ultrasonic import Ultrasonic
import cv2
import threading
import time

led = LED()
motor = Motor()
ultrasonic = Ultrasonic()

PRIORITY = {
    "traffic_light_red": 100,
    "stop sign": 90,
    "traffic_light_yellow": 50,
    "traffic_light_green": 10,
}

OBSTACLE_DISTANCE_CM = 20
TURN_BASE_SPEED   = 300   # velocidad base del giro
TURN_INCREMENT    = 150   # cuánto aumenta cada vez que sigue el obstáculo
TURN_MAX_SPEED    = 1000  # tope de velocidad de giro
TURN_DURATION     = 0.5   # segundos girando por cada intento


def decide_action(detections):
    best_object = None
    best_priority = -1
    for detection in detections:
        name = detection["name"]
        priority = PRIORITY.get(name, 0)
        if priority > best_priority:
            best_priority = priority
            best_object = name
    return best_object


# --- Estado compartido ---
latest_frame      = None
latest_detections = []
latest_distance   = 255
lock    = threading.Lock()
running = True


def vision_worker():
    global latest_frame, latest_detections, running
    vision = Vision()
    while running:
        detections, frame = vision.get_detections()
        with lock:
            latest_frame      = frame
            latest_detections = detections


def ultrasonic_worker():
    global latest_distance, running
    while running:
        distance = ultrasonic.get_distance()
        with lock:
            latest_distance = distance


threading.Thread(target=vision_worker,    daemon=True).start()
threading.Thread(target=ultrasonic_worker, daemon=True).start()

last_obj          = None
obstacle_attempts = 0   # cuántas veces consecutivas se detectó obstáculo


def evade_obstacle(attempts):
    """
    Gira a la derecha con velocidad creciente según los intentos.
    attempts=1 → giro suave, attempts=2 → más cerrado, etc.
    """
    speed = 1500
    print(f"↪️  EVASIÓN intento {attempts} — velocidad {speed}")
    led.set_all(255, 165, 0)  # naranja durante evasión

    # Girar a la derecha: motores izquierda adelante, derecha atrás
    motor.set_motor_model(speed, speed, -speed, -speed)
    time.sleep(TURN_DURATION)
    motor.set_motor_model(0, 0, 0, 0)   # pausa breve para re-medir
    time.sleep(0.1)


while True:
    with lock:
        frame      = latest_frame
        detections = list(latest_detections)
        distance   = latest_distance

    if frame is None:
        continue

    obstacle_near = distance < OBSTACLE_DISTANCE_CM

    if obstacle_near:
        obstacle_attempts += 1
        evade_obstacle(obstacle_attempts)

    else:
        # Sin obstáculo: resetear contador y seguir lógica de semáforos
        obstacle_attempts = 0

        obj = decide_action(detections)

        if obj != last_obj:
            last_obj = obj

            if obj == "traffic_light_red":
                print("🔴 DETENER")
                led.set_all(255, 0, 0)
                motor.set_motor_model(0, 0, 0, 0)

            elif obj == "stop_sign":
                print("🛑 DETENER")
                led.set_all(255, 0, 0)
                motor.set_motor_model(0, 0, 0, 0)

            elif obj == "traffic_light_yellow":
                print("🟡 REDUCIR VELOCIDAD")
                led.set_all(255, 255, 0)
                motor.set_motor_model(0, 0, 0, 0)

            elif obj == "traffic_light_green":
                print("🟢 AVANZAR")
                led.set_all(0, 255, 0)
                motor.set_motor_model(700, 700, 700, 700)

            elif obj is None:
                led.set_all(0, 0, 0)

    # HUD
    color = (0, 0, 255) if obstacle_near else (0, 255, 0)
    cv2.putText(frame, f"Dist: {distance}cm", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    if obstacle_attempts > 0:
        cv2.putText(frame, f"Evasion #{obstacle_attempts}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

    cv2.imshow("Carro Autonomo", frame)

    if cv2.waitKey(1) == 27:
        running = False
        break

cv2.destroyAllWindows()
ultrasonic.cleanup()