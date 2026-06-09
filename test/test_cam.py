# test.py
from ultralytics import YOLO
import cv2
import sys

MODEL_PATH = "runs/detect/carro-autonomo-pi/weights/best.pt"
CONF_THRESH = 0.05

ACTIONS = {
    "stop sign":            "🛑 DETENER",
    "traffic_light_red":    "🔴 SEMÁFORO ROJO",
    "traffic_light_green":  "🟢 SEMÁFORO VERDE",
    "traffic_light_yellow": "🟡 PRECAUCIÓN",
}

model = YOLO(MODEL_PATH)
print("Clases:", model.names)

source = sys.argv[1] if len(sys.argv) > 1 else 0

cap = cv2.VideoCapture(source)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=CONF_THRESH)
    annotated = results[0].plot()

    for r in results:
        for box in r.boxes:
            name = model.names[int(box.cls[0])]
            conf = float(box.conf[0])
            print(f"Detectado: {name}  conf={conf:.3f}")
            if name in ACTIONS:
                print(f">>> {ACTIONS[name]}")

    cv2.imshow("Test Carro Autonomo", annotated)
    if cv2.waitKey(1) == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()