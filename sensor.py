from machine import Pin, time_pulse_us
import time

trig = Pin(5, Pin.OUT)  # D1
echo = Pin(4, Pin.IN)   # D2

def mesure_distance():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    try:
        duree = time_pulse_us(echo, 1, 30000)
    except OSError:
        return None

    distance_cm = (duree / 2) * 0.0343
    return distance_cm

while True:
    dist = mesure_distance()
    if dist:
        print("Distance:", dist, "cm")
    else:
        print("Mesure échouée")
    time.sleep(1)
