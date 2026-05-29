# ══════════════════════════════════════════════
# main.py — Sistema completo todos los sensores
# Grupo 2 — Instrumentacion Industrial
#
# Sensores:
#   HC-SR04    → Nivel      (GPIO5/18)
#   HX711      → Carga      (GPIO21/22)
#   YF-S201    → Caudal     (GPIO23)
#   DS18B20    → Temp       (GPIO4)
#   Rele       → Valvula    (GPIO13)
# ══════════════════════════════════════════════
from time import sleep_ms, ticks_ms, ticks_diff
from hx711      import HX711
from hcsr04     import HCSR04
from flujometro import Flujometro
from termocupla import Termocupla
from valvula    import Valvula
from wifi       import conectar, esta_conectado
from mqtt_client import conectar as mqtt_conectar, publicar, ping, suscribir, check_msg
from mqtt_config import (
    PIN_TRIG, PIN_ECHO, PIN_DT, PIN_SCK,
    PIN_FLUJO, PIN_TEMP, PIN_VALVULA,
    ALTURA_TANQUE, FACTOR_CARGA, ZONA_MUERTA,
    TOPIC_NIVEL, TOPIC_CARGA, TOPIC_CAUDAL,
    TOPIC_TEMPERATURA, TOPIC_STATUS, TOPIC_VALVULA
)
import sys

INTERVALO_MS  = 500
RETARA_MS     = 8000
TEMP_MS       = 2000   # temperatura cada 2s (DS18B20 es lento)
PING_MS       = 30000

print("=" * 45)
print("  Grupo 2 — Sistema Completo MQTT")
print("  HC-SR04 + HX711 + YF-S201 + DS18B20 + Rele")
print("=" * 45)

wifi_ok = conectar()
mqtt_ok = False

hx     = HX711(PIN_DT, PIN_SCK)
sonar  = HCSR04(PIN_TRIG, PIN_ECHO, ALTURA_TANQUE)
flujo  = Flujometro(PIN_FLUJO)
temp   = Termocupla(PIN_TEMP)
valv   = Valvula(PIN_VALVULA)

# Callback para mensajes recibidos (valvula)
def on_message(topic, msg):
    t = topic.decode() if isinstance(topic, bytes) else topic
    m = msg.decode().strip() if isinstance(msg, bytes) else msg.strip()
    print("MQTT recibido:", t, "->", m)
    if t == TOPIC_VALVULA:
        if m == "toggle":
            valv.toggle()
        elif m == "abrir":
            valv.abrir()
        elif m == "cerrar":
            valv.cerrar()

if wifi_ok:
    mqtt_ok = mqtt_conectar(callback=on_message)
    if mqtt_ok:
        suscribir(TOPIC_VALVULA)

# Calibrar HX711
for _ in range(10):
    hx.read(); sleep_ms(10)

TARA            = hx.tara(30)
ultimo_con_peso = ticks_ms()
ultimo_envio    = ticks_ms()
ultimo_temp     = ticks_ms()
ultimo_ping     = ticks_ms()
peso_anterior   = 0.0
temp_actual     = None

print("Sistema listo — publicando en MQTT...")

while True:
    try:
        # Verificar mensajes MQTT entrantes (valvula)
        if mqtt_ok:
            check_msg()

        # Ping MQTT cada 30s
        if ticks_diff(ticks_ms(), ultimo_ping) > PING_MS:
            if mqtt_ok and not ping():
                print("MQTT caido, reconectando...")
                mqtt_ok = mqtt_conectar(callback=on_message)
                if mqtt_ok:
                    suscribir(TOPIC_VALVULA)
            ultimo_ping = ticks_ms()

        # Temperatura (cada 2s — DS18B20 necesita 750ms de conversion)
        if ticks_diff(ticks_ms(), ultimo_temp) > TEMP_MS:
            t = temp.leer()
            if t is not None:
                temp_actual = t
                print("Temp: {}°C".format(t))
            ultimo_temp = ticks_ms()

        # Celda de carga
        raw = hx.promedio()
        if raw is None:
            sleep_ms(50); continue

        g = (TARA - raw) / FACTOR_CARGA
        if abs(g) < ZONA_MUERTA: g = 0.0

        if g == 0.0:
            if ticks_diff(ticks_ms(), ultimo_con_peso) > RETARA_MS:
                nueva = hx.tara(15)
                if nueva: TARA = nueva; ultimo_con_peso = ticks_ms()
        else:
            ultimo_con_peso = ticks_ms()

        # Nivel
        dist, pct = sonar.nivel()
        if dist is None: dist = 0.0; pct = 0.0

        # Caudal
        caudal, volumen = flujo.leer()

        # Publicar en MQTT
        if ticks_diff(ticks_ms(), ultimo_envio) >= INTERVALO_MS:
            if not esta_conectado():
                print("WiFi perdido, reconectando...")
                wifi_ok = conectar()
                mqtt_ok = mqtt_conectar(callback=on_message) if wifi_ok else False
                if mqtt_ok: suscribir(TOPIC_VALVULA)
            elif mqtt_ok:
                publicar(TOPIC_NIVEL, {
                    "distancia": dist,
                    "nivel_pct": pct
                })
                publicar(TOPIC_CARGA, {
                    "gramos": round(g, 2),
                    "kg": round(g / 1000, 6)
                })
                publicar(TOPIC_CAUDAL, {
                    "lmin": caudal,
                    "volumen": volumen
                })
                if temp_actual is not None:
                    publicar(TOPIC_TEMPERATURA, {
                        "celsius": temp_actual,
                        "fahrenheit": round(temp_actual * 9/5 + 32, 2)
                    })
                publicar(TOPIC_STATUS, {
                    "valvula": valv.estado_str,
                    "uptime": ticks_ms() // 1000
                })
                print("D:{} N:{}% T:{}C C:{:.3f}g V:{}".format(
                    dist, pct,
                    temp_actual if temp_actual else "--",
                    g, valv.estado_str))
            else:
                mqtt_ok = mqtt_conectar(callback=on_message)
                if mqtt_ok: suscribir(TOPIC_VALVULA)
            ultimo_envio = ticks_ms()

        sleep_ms(80)

    except KeyboardInterrupt:
        valv.cerrar()
        print("Detenido.")
        sys.exit()
    except Exception as e:
        print("Error:", e)
        sleep_ms(100)
