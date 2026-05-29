# detector.py
import cv2
import numpy as np
from tensorflow.keras.models import load_model

CLASES    = ['coca_cola', 'fanta', 'pepsi', 'salvieti_200', 'vital_600', 'vital_salvieti']
UMBRAL    = 80.0
IMG_SIZE  = 224

model = None

def load(path='botellas_model_v2.h5'):
    global model
    model = load_model(path)

def predict(frame):
    img = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    img_array = img / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    pred = model.predict(img_array, verbose=0)
    clase = CLASES[np.argmax(pred)]
    confianza = float(np.max(pred)) * 100
    if confianza < UMBRAL:
        return None, confianza
    return clase, confianza
