# Carro Autónomo con Raspberry Pi

Proyecto de un vehículo autónomo controlado por una **Raspberry Pi** que combina **visión por computadora (YOLOv8)** y **lectura de sensores** para detectar semáforos, señales de pare y obstáculos, y reaccionar en tiempo real controlando motores y una tira de LEDs.

---

## Tabla de contenidos

- [Características](#características)
- [Arquitectura del sistema](#arquitectura-del-sistema)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Hardware requerido](#hardware-requerido)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Modelo de visión](#modelo-de-visión)
- [Lógica de decisión](#lógica-de-decisión)
- [Pruebas](#pruebas)
- [Configuración](#configuración)
- [Solución de problemas](#solución-de-problemas)
- [Licencia y créditos](#licencia-y-créditos)

---

## Características

- **Detección de objetos en tiempo real** con YOLOv8 (exportado a NCNN para inferencia optimizada en ARM).
- Reconoce **4 clases**: `traffic_light_red`, `traffic_light_yellow`, `traffic_light_green` y `stop_sign`.
- **Sensor ultrasónico HC-SR04** para detectar obstáculos a menos de 20 cm.
- **Evasión de obstáculos** con giros incrementales a la derecha.
- **Tira de 8 LEDs WS2812** (vía SPI) como indicador visual de estado:
  - Verde: avanzar
  - Amarillo: precaución
  - Rojo: detenerse
  - Naranja: en evasión
- Cámara **CSI / PiCamera2** a 640×480 @ 15 FPS.
- **Doble hilo de ejecución** en paralelo: visión artificial y lectura ultrasónica (no se bloquean mutuamente).
- HUD en vivo con OpenCV mostrando distancia y número de intento de evasión.

---

## Arquitectura del sistema

```
┌──────────────────────┐         ┌──────────────────────┐
│ Hilo: vision_worker  │         │ Hilo: ultrasonic_w.  │
│   PiCamera2 + YOLOv8 │         │   HC-SR04 (GPIO)     │
└──────────┬───────────┘         └──────────┬───────────┘
           │ detecciones, frame             │ distancia (cm)
           └──────────────┬─────────────────┘
                          ▼
                ┌──────────────────┐
                │   Estado global  │
                │   (thread-safe)  │
                └────────┬─────────┘
                         ▼
                ┌──────────────────┐
                │ Bucle principal  │
                │ decide_action()  │
                └────────┬─────────┘
                         ▼
              ┌──────────┴──────────┐
              ▼                     ▼
   ┌──────────────────┐   ┌──────────────────┐
   │  Motor (PCA9685) │   │   Tira LED (SPI) │
   └──────────────────┘   └──────────────────┘
```

---

## Estructura del proyecto

```
ia_proyecto_II/
├── main.py                      # Punto de entrada — orquesta visión, ultrasónico, motores y LEDs
├── test.py                      # Test rápido del modelo con OpenCV (cámara o video)
│
├── device_control/              # Drivers de hardware
│   ├── Led.py                   # Tira WS2812 vía SPI (clase LED + SPI_LedPixel)
│   ├── Motor.py                 # 4 motores DC vía PCA9685 (avanzar / retroceder / girar)
│   ├── Servo.py                 # 8 servos (canales 8-15 del PCA9685)
│   ├── PCA9685.py               # Driver I2C del expansor PWM de 16 canales
│   ├── Ultrasonic.py            # Sensor HC-SR04 (TRIG=27, ECHO=22)
│   ├── ADC.py                   # ADC PCF8591 / ADS7830 (lectura de batería y sensores)
│   ├── LightSensor.py           # Sensores de luz izquierda/derecha (vía ADC)
│   └── Buzzer.py                # Buzzer pasivo (GPIO 17)
│
├── model/                       # Modelo YOLOv8 y dataset
│   ├── vision.py                # Clase Vision: captura + inferencia NCNN
│   ├── data.yaml                # Configuración del dataset (4 clases)
│   ├── README.roboflow.txt      # Origen del dataset (Roboflow)
│   ├── README.dataset.txt       # Notas del dataset
│   ├── train/  valid/  test/    # División del dataset
│   └── runs/detect/             # Pesos entrenados (no commiteados)
│
└── test/                        # Scripts de prueba
    ├── test_cam.py              # Test con cámara USB / video
    └── test_cam_rp.py           # Test con PiCamera2
```

---

## Hardware requerido

| Componente | Uso | Interfaz |
|---|---|---|
| Raspberry Pi 4 (recomendado) | Controlador principal | — |
| PiCamera v2 / v3 | Captura de video | CSI |
| Sensor ultrasónico HC-SR04 | Distancia al frente | GPIO 27 (TRIG), 22 (ECHO) |
| Driver PCA9685 | PWM para motores y servos | I2C (`0x40`) |
| 4 motores DC con encoder | Tracción | Canales 0-7 del PCA9685 |
| 8 servos | Dirección/actuadores auxiliares | Canales 8-15 del PCA9685 |
| Tira LED WS2812 (8 LEDs) | Indicador de estado | SPI0 MOSI (GPIO 10) |
| ADC PCF8591 / ADS7830 | Sensores analógicos | I2C (`0x48`) |
| Buzzer pasivo | Alerta sonora | GPIO 17 |
| Batería 7.4V LiPo | Alimentación motores | — |
| Chasis 4WD | Estructura mecánica | — |

---

## Requisitos previos

- Raspberry Pi OS (64 bits recomendado para YOLOv8/NCNN).
- Python 3.9+.
- SPI e I2C habilitados: `sudo raspi-config` → *Interface Options* → habilitar **SPI** e **I2C**.
- Cámara CSI conectada y activada (`sudo raspi-config` → *Interface Options* → *Camera*).
- Verificar `dtparam=spi=on` en `/boot/firmware/config.txt`.

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd ia_proyecto_II

# 2. Crear y activar un entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install ultralytics opencv-python picamera2 RPi.GPIO spidev smbus2 numpy
```

### Obtener los pesos del modelo

Los pesos entrenados no se incluyen en el repo (ver `.gitignore`). Tienes dos opciones:

1. **Usar el modelo ya entrenado**: copia los archivos `best_ncnn_model/` y `best_ncnn_model.param` a la ruta esperada:
   ```
   model/runs/detect/carro-autonomo-pi/weights/best_ncnn_model
   model/runs/detect/carro-autonomo-pi/weights/best_ncnn_model.param
   ```

2. **Entrenar desde cero** con el dataset incluido:
   ```bash
   yolo detect train data=model/data.yaml model=yolov8n.pt epochs=100 imgsz=640
   yolo export model=model/runs/detect/carro-autonomo-pi/weights/best.pt format=ncnn
   ```

---

## Uso

```bash
source .venv/bin/activate
python main.py
```

Al iniciar:
1. Se inicializan LED, motor y sensor ultrasónico.
2. Se lanzan los hilos `vision_worker` y `ultrasonic_worker`.
3. Se abre una ventana llamada **"Carro Autonomo"** con la imagen en vivo.
4. Presiona **`ESC`** para salir de forma segura.

### Comportamiento esperado

| Evento detectado | Acción en motores | LED |
|---|---|---|
| `traffic_light_red` | Detener | Rojo |
| `stop_sign` | Detener | Rojo |
| `traffic_light_yellow` | Detener (precaución) | Amarillo |
| `traffic_light_green` | Avanzar (duty 700) | Verde |
| Obstáculo < 20 cm | Girar derecha (intento N) | Naranja |
| Sin detecciones | — | Apagado |

---

## Modelo de visión

- **Arquitectura**: YOLOv8 (Ultralytics) — backbone liviano adecuado para Raspberry Pi.
- **Formato de exportación**: NCNN (optimizado para ARM, sin dependencia de PyTorch en inferencia).
- **Inferencia**: `half=True` (FP16) para reducir memoria y acelerar en ARM.
- **Resolución de entrada**: 640×480 @ 15 FPS.
- **Confianza mínima**: 0.10 (ajustable en `model/vision.py` → `CONF_THRESH`).
- **IoU**: 0.5 (NMS).
- **Clases** (4): `stop_sign`, `traffic_light_green`, `traffic_light_red`, `traffic_light_yellow`.
- **Dataset**: 200 imágenes etiquetadas en formato YOLOv8, exportadas desde Roboflow.

---

## Lógica de decisión

Definida en `main.py`:

1. **Hilo de visión** actualiza continuamente `latest_frame` y `latest_detections`.
2. **Hilo ultrasónico** actualiza `latest_distance` (mediana de 5 lecturas).
3. El bucle principal, con un `lock` para acceso seguro:
   - Si `distance < OBSTACLE_DISTANCE_CM` (20 cm) → incrementa `obstacle_attempts` y ejecuta `evade_obstacle()` (giro a la derecha durante `TURN_DURATION` segundos).
   - Si no hay obstáculo → resetea el contador y aplica la regla de prioridad:
     ```
     traffic_light_red    (100)   → DETENER
     stop_sign             (90)   → DETENER
     traffic_light_yellow  (50)   → PRECAUCIÓN
     traffic_light_green   (10)   → AVANZAR
     ```
   - Solo cambia la acción cuando aparece un objeto **distinto** al último procesado (evita parpadeo).

Constantes ajustables al inicio de `main.py`:

```python
OBSTACLE_DISTANCE_CM = 20    # Distancia de detección de obstáculo
TURN_DURATION        = 0.5   # Segundos girando por cada intento
```

---

## Pruebas

```bash
# Test del modelo con cámara USB o un video
python test.py 0                          # cámara 0
python test.py ruta/al/video.mp4

# Test del modelo con PiCamera2 (Raspberry Pi)
python test/test_cam_rp.py

# Test del modelo con cámara USB desde test/
python test/test_cam.py

# Test rápido de la tira LED
python test.py
```

---

## Configuración

| Archivo | Qué modificar |
|---|---|
| `main.py` | Umbrales de prioridad, distancia de obstáculo, duración de giro, velocidades de motor. |
| `model/vision.py` | `MODEL_PATH`, `CONF_THRESH`, resolución de cámara, FPS. |
| `device_control/Motor.py` | Mapeo de canales PWM a ruedas, velocidades por defecto. |
| `device_control/Ultrasonic.py` | Pines TRIG/ECHO, distancia máxima. |
| `device_control/Led.py` | Cantidad de LEDs, bus SPI, secuencia de color (GRB por defecto). |
| `model/data.yaml` | Rutas del dataset y nombres de clases. |

---

## Solución de problemas

**`Please check the configuration in /boot/firmware/config.txt`** — El SPI no está habilitado.
```bash
sudo raspi-config
# Interface Options → SPI → Enable
sudo reboot
```

**`ModuleNotFoundError: picamera2`** — Instala la librería específica para Bookworm (64 bits):
```bash
sudo apt install -y python3-picamera2
pip install picamera2
```

**El modelo NCNN no se carga** — Verifica que existan los archivos:
```
model/runs/detect/carro-autonomo-pi/weights/best_ncnn_model
model/runs/detect/carro-autonomo-pi/weights/best_ncnn_model.param
```

**FPS muy bajos en la Pi** — Reduce resolución en `model/vision.py` (`size=(320, 240)`) o aumenta `CONF_THRESH` para descartar detecciones tempranamente.

**El carro no frena en amarillo** — Revisa que `decide_action()` reconozca `traffic_light_yellow` y que la prioridad (`PRIORITY`) esté bien configurada.

---

## Licencia y créditos

- **Dataset**: [find-traffic_light en Roboflow](https://universe.roboflow.com/estiven-joel-laferre-guevara/find-traffic_light-heubh) — Public Domain.
- **Modelo**: [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) — AGPL-3.0.
- **Driver PCA9685**: basado en la librería Adafruit_PCA9685.
- **Tira LED WS2812**: protocolo SPI-bitbang según referencia de Raspberry Pi.

Proyecto académico de **Inteligencia Artificial II**.
