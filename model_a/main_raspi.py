# main_rpi.py - Raspberry Pi 4
import pygame
import serial
import json
import time
import cv2
import numpy as np
import threading
from picamera2 import Picamera2
import tflite_runtime.interpreter as tflite

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE   = 115200
MODEL_PATH  = "botellas_model_v2.tflite"
IMG_SIZE    = 224
CLASSES     = ["coca_cola", "fanta", "pepsi", "salvietti"]
NO_DETECT_TIMEOUT = 3.0

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Model A - Botellas")
font = pygame.font.SysFont("monospace", 24, bold=True)

BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
GREEN  = (0, 255, 0)
RED    = (255, 50, 50)
YELLOW = (255, 220, 0)

def send(data):
    ser.write((json.dumps(data) + "\n").encode())

def predict(frame):
    img = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)
    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])[0]
    idx = int(np.argmax(output))
    return CLASSES[idx], float(output[idx])

def draw(label, accuracy, color):
    for event in pygame.event.get():
        pass
    screen.fill(BLACK)
    t1 = font.render(f"Deteccion: {label}", True, color)
    t2 = font.render(f"Accuracy:  {accuracy:.1%}", True, WHITE)
    screen.blit(t1, (20, 20))
    screen.blit(t2, (20, 60))
    pygame.display.flip()

def main():
    cam = Picamera2()
    cam.start()
    time.sleep(1)

    last_detected = time.time()
    motor_on = False

    try:
        while True:
            frame = cam.capture_array()
            label, acc = predict(frame)

            if acc < 0.6:
                label = "ninguna"

            if label == "coca_cola":
                send({"cmd": "led", "color": "red", "interval": 1})
                last_detected = time.time()
                motor_on = False
                draw(label, acc, RED)
            elif label == "salvietti":
                send({"cmd": "led", "color": "green", "interval": 1})
                last_detected = time.time()
                motor_on = False
                draw(label, acc, GREEN)
            elif label in ["fanta", "pepsi"]:
                send({"cmd": "led", "color": "none", "interval": 3})
                last_detected = time.time()
                motor_on = False
                draw(label, acc, YELLOW)
            else:
                draw("ninguna", 0.0, WHITE)
                if time.time() - last_detected > NO_DETECT_TIMEOUT:
                    if not motor_on:
                        send({"cmd": "motor", "duty": 0.5})
                        motor_on = True

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        send({"cmd": "stop"})
        cam.stop()
        ser.close()
        pygame.quit()

if __name__ == "__main__":
    main()