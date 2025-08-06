from machine import Pin, time_pulse_us
import time
import ucollections
from wifi import load_config
from supabase_client import send_to_supabase

# --- Configuration des broches ---
trig = Pin(5, Pin.OUT)  # D1
echo = Pin(4, Pin.IN)   # D2

# --- Filtrage ---
HISTORY_SIZE = 20
readings = ucollections.deque((), HISTORY_SIZE)
filtered_value = None
ALPHA = 0.2  # 0.1 = très lisse, 0.5 = plus réactif

# --- Config ---
cfg = load_config()
SEND_INTERVAL = 60  # secondes
last_sent = 0

def mesure_distance():
    """Mesure la distance en cm avec le capteur JSN-SR04T."""
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

def get_median(values):
    """Retourne la médiane d'une deque sans utiliser l'indexation."""
    if len(values) == 0:
        return None

    vals = []
    temp_storage = []

    # Extraire les éléments de la deque
    while len(values):
        item = values.popleft()
        vals.append(item)
        temp_storage.append(item)

    # Remettre les éléments
    for item in temp_storage:
        values.append(item)

    sorted_vals = sorted(vals)
    n = len(sorted_vals)

    if n % 2 == 1:
        return sorted_vals[n // 2]
    else:
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

def process_sensor_data():
    """Effectue une mesure, applique le filtrage et envoie à Supabase."""
    global filtered_value, last_sent

    dist = mesure_distance()
    if dist:
        readings.append(dist)
        median = get_median(readings)

        if median is not None:
            if filtered_value is None:
                filtered_value = median
            else:
                filtered_value = ALPHA * median + (1 - ALPHA) * filtered_value

            print("Mesure brute:", round(dist, 2), "cm | Médiane:", round(median, 2), "cm | Filtrée:", round(filtered_value, 2), "cm")

            if time.time() - last_sent > SEND_INTERVAL:
                send_to_supabase(cfg.get("device_id"), round(filtered_value, 2), time.time())
                last_sent = time.time()
    else:
        print("❌ Mesure échouée")

# --- Boucle principale ---
while True:
    process_sensor_data()
    time.sleep(1)
