from machine import Pin, time_pulse_us
import time
import ucollections
from wifi import load_config
from supabase_client import send_to_supabase

# Définition des broches
trig = Pin(5, Pin.OUT)  # D1
echo = Pin(4, Pin.IN)   # D2

# Historique des mesures (pour filtre médian)
HISTORY_SIZE = 5
readings = ucollections.deque((), HISTORY_SIZE)

# Valeur filtrée (initialisée à None)
filtered_value = None

# Coefficient du filtre exponentiel (0.1 = très lisse, 0.5 = plus réactif)
ALPHA = 0.2

# Chargement config (device_id, etc.)
cfg = load_config()

# Intervalle d’envoi vers Supabase (secondes)
SEND_INTERVAL = 60
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
    """Retourne la médiane d'une liste de valeurs."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 1:
        return sorted_vals[n // 2]
    else:
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

# Boucle principale
while True:
    dist = mesure_distance()
    if dist:
        readings.append(dist)
        median = get_median(readings)

        # Filtrage exponentiel
        if filtered_value is None:
            filtered_value = median
        else:
            filtered_value = ALPHA * median + (1 - ALPHA) * filtered_value

        print("Mesure brute:", dist, "cm | Médiane:", median, "cm | Filtrée:", round(filtered_value, 2), "cm")

        # Envoi vers Supabase à intervalle régulier
        if time.time() - last_sent > SEND_INTERVAL:
            send_to_supabase(cfg["device_id"], round(filtered_value, 2), time.time())
            last_sent = time.time()
    else:
        print("Mesure échouée")

    time.sleep(1)
