from machine import Pin, time_pulse_us
import time
import ucollections
from wifi import load_config
from supabase_client import send_to_supabase
from calibration_manager import update_calibration

trig = Pin(5, Pin.OUT)  # D1
echo = Pin(4, Pin.IN)   # D2

HISTORY_SIZE = 20
readings = ucollections.deque((), HISTORY_SIZE)
filtered_value = None
ALPHA = 0.2

cfg = load_config()
SEND_INTERVAL = 60
last_sent = 0

# Charger calibration
calibration = update_calibration()

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
    return (duree / 2) * 0.0343

def get_median(values):
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
    return sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

def level_to_volume(level_cm):
    if not calibration or "points" not in calibration:
        return None
    points = calibration["points"]
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i+1]
        if p1["level"] <= level_cm <= p2["level"]:
            ratio = (level_cm - p1["level"]) / (p2["level"] - p1["level"])
            return p1["volume"] + ratio * (p2["volume"] - p1["volume"])
    return points[-1]["volume"]

def process_sensor_data():
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
            volume = level_to_volume(filtered_value)
            print("Niveau:", round(filtered_value, 2), "cm | Volume:", volume, "L")
            if time.time() - last_sent > SEND_INTERVAL:
                send_to_supabase(cfg.get("device_id"), round(filtered_value, 2), volume, time.time())
                last_sent = time.time()
    else:
        print("❌ Mesure échouée")

while True:
    process_sensor_data()
    time.sleep(1)
