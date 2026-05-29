# comunicacion.py
import serial
import json
import time

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE   = 115200

ser = None

def connect():
    global ser
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

def send(data):
    ser.write((json.dumps(data) + "\n").encode())

def close():
    if ser:
        ser.close()
