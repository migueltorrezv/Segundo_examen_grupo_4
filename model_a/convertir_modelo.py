import tensorflow as tf

model = tf.keras.models.load_model("botellas_model_v2.h5")

converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open("botellas_model_v2.tflite", "wb") as f:
    f.write(tflite_model)

print("listo: botellas_model_v2.tflite")