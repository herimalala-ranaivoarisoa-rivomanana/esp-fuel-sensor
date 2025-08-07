from machine import Pin, time_pulse_us
import time
import ucollections
from wifi import load_config
from supabase_client import send_to_supabase
from calibration_manager import update_calibration

# --- Configuration Capteur ---
trig = Pin(5, Pin.OUT)  # D1
echo = Pin(4, Pin.IN)   # D2

# Historique pour médiane
HISTORY_SIZE = 20
readings = ucollections.deque((), HISTORY_SIZE)

filtered_value = None
ALPHA = 0.2  # Filtre exponentiel

cfg = load_config()

# Charger le flag d'envoi hors plages depuis device_command.json
import ujson
try:
    with open("device_command.json") as f:
        device_cmd = ujson.load(f)
        SEND_OUT_OF_RANGE = device_cmd.get("send_out_of_range", False)
except:
    SEND_OUT_OF_RANGE = False

SEND_INTERVAL = 60  # Intervalle en secondes
DELTA_VOLUME = 1.0  # Seuil variation minimale volume (litres)

last_sent = 0
last_sent_volume = None

# Calibration initiale : toujours utiliser la copie locale
from calibration_manager import load_local_calibration, update_calibration
update_calibration()  # Met à jour la calibration locale si besoin, mais ne retourne plus la calibration à utiliser
calibration = load_local_calibration()  # Toujours charger la calibration locale

# --- Fonctions ---

def mesure_distance():
    """Mesure la distance en cm avec JSN-SR04T."""
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    try:
        duree = time_pulse_us(echo, 1, 30000)
    except OSError:
        return None

    return (duree / 2) * 0.0343

def get_median(values):
    """Calcule la médiane d'une deque."""
    if len(values) == 0:
        return None
    vals = []
    temp = []
    while len(values):
        item = values.popleft()
        vals.append(item)
        temp.append(item)
    for item in temp:
        values.append(item)
    sorted_vals = sorted(vals)
    n = len(sorted_vals)
    if n % 2 == 1:
        return sorted_vals[n // 2]
    else:
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

def level_to_volume(level_cm):
    """Convertit un niveau en volume par interpolation linéaire avec bornes."""
    if not calibration or "points" not in calibration:
        return None

    points = calibration["points"]
    min_level = points[0]["level"]
    max_level = points[-1]["level"]

    # ✅ Hors plage → pas de volume
    if level_cm < min_level or level_cm > max_level:
        print(f"⚠️ Mesure {round(level_cm,2)} cm hors plage calibration ({min_level}-{max_level} cm)")
        return None

    # Interpolation linéaire
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        if p1["level"] <= level_cm <= p2["level"]:
            ratio = (level_cm - p1["level"]) / (p2["level"] - p1["level"])
            return p1["volume"] + ratio * (p2["volume"] - p1["volume"])

    # Exactement au max
    if level_cm == max_level:
        return points[-1]["volume"]

    return None

def process_sensor_data():
    global filtered_value, last_sent, last_sent_volume
    dist = mesure_distance()

    if dist:
        readings.append(dist)
        median = get_median(readings)

        if median is not None:
            if filtered_value is None:
                filtered_value = median
            else:
                filtered_value = ALPHA * median + (1 - ALPHA) * filtered_value

            volume = level_to_volume(filtered_value)

            # Bornes calibration
            min_level = calibration["points"][0]["level"] if calibration else None
            max_level = calibration["points"][-1]["level"] if calibration else None

            print("Niveau:", round(filtered_value, 2), "cm | Volume:", volume if volume is not None else "N/A", "L")

            # Vérifications avant envoi
            if volume is None:
                print("⚠️ Mesure hors plage calibration")
                # Décision d'envoi selon le flag
                if SEND_OUT_OF_RANGE:
                    print("➡️ Envoi mesure hors plage à la base de données (flag activé)")
                    send_to_supabase(
                        cfg.get("device_id"),
                        round(filtered_value, 2),
                        None,
                        time.time()
                    )
                    last_sent = time.time()
                    last_sent_volume = None
                else:
                    print("🚫 Mesure hors plage NON envoyée (flag désactivé)")
                return
            elif time.time() - last_sent > SEND_INTERVAL:
                if last_sent_volume is None or abs(volume - last_sent_volume) >= DELTA_VOLUME:
                    send_to_supabase(
                        cfg.get("device_id"),
                        round(filtered_value, 2),
                        round(volume, 2),
                        time.time()
                    )
                    last_sent = time.time()
                    last_sent_volume = volume
                else:
                    print("ℹ️ Variation < seuil, pas d'envoi.")
    else:
        print("❌ Mesure échouée")

# --- Boucle principale ---
while True:
    process_sensor_data()
    time.sleep(3)
