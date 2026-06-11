from ultralytics import YOLO
from picamera2 import Picamera2
from libcamera import Transform
import cv2

MODEL_PATH = "./model/runs/detect/carro-autonomo-pi/weights/best_ncnn_model"
CONF_THRESH = 0.1  # Subir umbral: menos falsos positivos, menos trabajo
IOU_THRESH = 0.5


class Vision:

    def __init__(self):
        self.model = YOLO(MODEL_PATH)

        # Exportar a NCNN para inferencia optimizada en Pi (solo primera vez)
        # self.model.export(format="ncnn")
        # self.model = YOLO("./model/.../best_ncnn_model")

        self.picam2 = Picamera2()

        config = self.picam2.create_preview_configuration(
            main={
                "format": "RGB888",
                "size": (640, 480)  # Reducir resolución: 4x menos píxeles
            },
            transform=Transform(hflip=1, vflip=1),
            controls={"FrameRate": 15}  # Limitar FPS de captura
        )

        self.picam2.configure(config)
        self.picam2.start()

        # Calentar el modelo (primer inference es siempre lenta)
        import numpy as np
        self.model(np.zeros((480, 640, 3), dtype="uint8"), verbose=False)

    def get_detections(self):

        frame = self.picam2.capture_array()

        results = self.model(
            frame,
            conf=CONF_THRESH,
            iou=IOU_THRESH,
            verbose=False,   # Silenciar logs por frame (ahorra I/O)
            half=True,       # FP16: reduce memoria y acelera en ARM
        )

        detections = []

        for r in results:
            for box in r.boxes:
                detections.append({
                    "name": self.model.names[int(box.cls[0])],
                    "confidence": float(box.conf[0])
                })

        # plot() solo si hay detecciones (evita trabajo innecesario)
        annotated = results[0].plot() if detections else frame

        return detections, annotated