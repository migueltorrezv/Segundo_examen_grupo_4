# comunicacion.py - Model B
import serial
import json
import time

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE   = 115200

ser = None

def connect():
    global ser
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.05)
    time.sleep(2)

def send(data):
    ser.write((json.dumps(data) + "\n").encode())

def read():
    try:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            return json.loads(line)
    except:
        pass
    return None

def close():
    if ser:
        ser.close()
