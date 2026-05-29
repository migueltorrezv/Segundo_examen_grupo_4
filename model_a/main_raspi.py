import cv2
import time
import camera
import detector
import comunicacion

SALVIETTI         = ['salvieti_200', 'vital_salvieti']
NO_DETECT_TIMEOUT = 3.0

def main():
    comunicacion.connect()
    detector.load()

    last_detected = time.time()
    motor_on      = False

    try:
        while True:
            frame = camera.capture()
            if frame is None:
                continue

            clase, confianza = detector.predict(frame)

            if clase is None:
                label = f"Desconocido ({confianza:.1f}%)"
                color = (0, 0, 255)
                comunicacion.send({"cmd": "led", "color": "none", "interval": 3})

                if time.time() - last_detected > NO_DETECT_TIMEOUT:
                    if not motor_on:
                        comunicacion.send({"cmd": "motor", "duty": 0.5})
                        motor_on = True
            else:
                label = f"{clase} ({confianza:.1f}%)"
                last_detected = time.time()
                motor_on      = False

                if clase == "coca_cola":
                    color = (0, 0, 255)
                    comunicacion.send({"cmd": "led", "color": "red", "interval": 1})
                elif clase in SALVIETTI:
                    color = (0, 255, 0)
                    comunicacion.send({"cmd": "led", "color": "green", "interval": 1})
                else:
                    color = (0, 255, 255)
                    comunicacion.send({"cmd": "led", "color": "none", "interval": 3})

            cv2.putText(frame, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
            cv2.imshow("Model A - Botellas", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        comunicacion.send({"cmd": "stop"})
        comunicacion.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

