# main_rpi.py - Raspberry Pi 4 - Model B
import cv2
import time
import camera
import detector
import comunicacion
import contador

SALVIETTI = ['salvieti_200', 'vital_salvieti']

def main():
    comunicacion.connect()
    detector.load()
    contador.iniciar()

    try:
        while not contador.terminado():
            # Verificar pausa desde Pico
            msg = comunicacion.read()
            if msg and msg.get("cmd") == "emergency":
                pausado = contador.toggle_pausa()
                estado = "PAUSADO" if pausado else "REANUDADO"
                print(f"Sistema {estado}")

            if contador.pausado:
                time.sleep(0.1)
                continue

            frame = camera.capture()
            if frame is None:
                continue

            clase, confianza = detector.predict(frame)
            frame = detector.draw_box(frame, clase, confianza)
            contador.registrar(clase)

            # Mostrar tiempo restante
            t = int(contador.tiempo_restante())
            cv2.putText(frame, f"Tiempo: {t}s", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame, f"Estado: {'PAUSADO' if contador.pausado else 'ACTIVO'}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

            cv2.imshow("Model B - Botellas", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        comunicacion.send({"cmd": "stop"})
        comunicacion.close()
        cv2.destroyAllWindows()
        contador.guardar_txt()
        contador.mostrar_grafica()
        print("Resultados guardados en resultados.txt y resultados.png")

if __name__ == "__main__":
    main()
