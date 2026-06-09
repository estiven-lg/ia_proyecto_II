from model.vision import Vision

vision = Vision()

while True:

    detections = vision.get_detections()

    if "traffic_light_red" in detections:
        print("DETENER")

    elif "traffic_light_green" in detections:
        print("AVANZAR")