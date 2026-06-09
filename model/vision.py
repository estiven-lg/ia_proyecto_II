from ultralytics import YOLO
from picamera2 import Picamera2
from libcamera import Transform
import cv2

MODEL_PATH = "./model/runs/detect/carro-autonomo-pi/weights/best.pt"
CONF_THRESH = 0.05

ACTIONS = {
    "stop sign":            "🛑 DETENER",
    "traffic_light_red":    "🔴 SEMÁFORO ROJO",
    "traffic_light_green":  "🟢 SEMÁFORO VERDE",
    "traffic_light_yellow": "🟡 PRECAUCIÓN",
}

model = YOLO(MODEL_PATH)

print("Clases:", model.names)

# Cámara CSI
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={
        "format": "RGB888",
        "size": (640, 480)
    },
    transform=Transform(hflip=1, vflip=1)
)

picam2.configure(config)
picam2.start()

while True:
    frame = picam2.capture_array()

    results = model(frame, conf=CONF_THRESH)

    annotated = results[0].plot()

    for r in results:
        for box in r.boxes:
            name = model.names[int(box.cls[0])]
            conf = float(box.conf[0])

            print(f"Detectado: {name} conf={conf:.3f}")

            if name in ACTIONS:
                print(f">>> {ACTIONS[name]}")

    cv2.imshow("Carro Autonomo", annotated)

    if cv2.waitKey(1) == 27:  # ESC
        break

cv2.destroyAllWindows()