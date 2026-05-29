# contador.py
import matplotlib.pyplot as plt
import time

DURACION = 60

conteo = {}
pausado = False
inicio = None

def iniciar():
    global inicio
    inicio = time.time()

def tiempo_restante():
    return max(0, DURACION - (time.time() - inicio))

def terminado():
    return time.time() - inicio >= DURACION

def registrar(clase):
    if pausado or clase is None:
        return
    conteo[clase] = conteo.get(clase, 0) + 1

def toggle_pausa():
    global pausado
    pausado = not pausado
    return pausado

def guardar_txt():
    with open("resultados.txt", "w") as f:
        f.write("Resultados de deteccion\n")
        f.write("=======================\n")
        for clase, total in sorted(conteo.items(), key=lambda x: -x[1]):
            f.write(f"{clase}: {total}\n")

def mostrar_grafica():
    if not conteo:
        return
    ordenado = sorted(conteo.items(), key=lambda x: -x[1])[:3]
    clases = [x[0] for x in ordenado]
    valores = [x[1] for x in ordenado]

    plt.figure(figsize=(8, 5))
    plt.bar(clases, valores, color=['red', 'orange', 'green'][:len(clases)])
    plt.title("Top 3 botellas detectadas")
    plt.xlabel("Botella")
    plt.ylabel("Cantidad")
    plt.tight_layout()
    plt.savefig("resultados.png")
    plt.show()
