# main_pico.py - MicroPython 1.27 - Model B
import sys
import json
import utime
import uselect
from machine import Pin, PWM

# --- Motores L298N ---
in1 = Pin(2, Pin.OUT)
in2 = Pin(3, Pin.OUT)
in3 = Pin(4, Pin.OUT)
in4 = Pin(5, Pin.OUT)
ena = PWM(Pin(6)); ena.freq(1000)
enb = PWM(Pin(7)); enb.freq(1000)

# --- LEDs ---
led_r = Pin(16, Pin.OUT)
led_g = Pin(17, Pin.OUT)

# --- Boton emergencia ---
btn = Pin(19, Pin.IN, Pin.PULL_UP)

# --- Estado ---
led_color    = "none"
led_interval = 1000
led_state    = False
last_toggle  = utime.ticks_ms()
btn_prev     = True

def set_motor(duty):
    speed = int(abs(duty) * 65535)
    if duty > 0:
        in1.high(); in2.low()
        in3.high(); in4.low()
    else:
        in1.low(); in2.low()
        in3.low(); in4.low()
    ena.duty_u16(speed)
    enb.duty_u16(speed)

def leds_off():
    led_r.low()
    led_g.low()

def update_leds():
    global led_state, last_toggle
    now = utime.ticks_ms()
    if utime.ticks_diff(now, last_toggle) >= led_interval:
        led_state = not led_state
        last_toggle = now
        if led_color == "red":
            led_r.value(led_state)
            led_g.low()
        elif led_color == "green":
            led_g.value(led_state)
            led_r.low()
        else:
            leds_off()

# --- Init ---
leds_off()
set_motor(0)

buffer = ""
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

# --- Loop principal ---
while True:
    # Boton emergencia
    btn_now = btn.value()
    if btn_prev and not btn_now:
        sys.stdout.write(json.dumps({"cmd": "emergency"}) + "\n")
    btn_prev = btn_now

    # Leer comandos desde RPi
    events = poll.poll(10)
    if events:
        char = sys.stdin.read(1)
        if char == '\n':
            try:
                cmd = json.loads(buffer)
                c = cmd.get("cmd", "")

                if c == "led":
                    led_color    = cmd.get("color", "none")
                    led_interval = int(cmd.get("interval", 1)) * 1000
                    set_motor(0)

                elif c == "motor":
                    set_motor(float(cmd.get("duty", 0.5)))
                    leds_off()
                    led_color = "none"

                elif c == "stop":
                    set_motor(0)
                    leds_off()
                    led_color = "none"

            except:
                pass
            buffer = ""
        else:
            buffer += char

    update_leds()