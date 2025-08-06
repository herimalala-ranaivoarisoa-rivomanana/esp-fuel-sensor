import network
import ujson
import time

CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return ujson.load(f)
    except:
        return {
            "device_id": "ESP001",
            "wifi_ssid": "",
            "wifi_password": "",
            "sta": False,
            "current_version": "1.0.0"
        }

def save_config(ssid, password, sta=True, version="1.0.0"):
    cfg = load_config()
    config = {
        "device_id": cfg.get("device_id", "ESP001"),
        "wifi_ssid": ssid,
        "wifi_password": password,
        "sta": sta,
        "current_version": version
    }
    with open(CONFIG_FILE, "w") as f:
        ujson.dump(config, f)

def connect_sta(ssid, password, timeout=10):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            return False
        time.sleep(1)
    print("✅ Connecté au WiFi:", wlan.ifconfig())
    return True

def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="TLS", password="Tls100Sor")

def setup_wifi():
    config = load_config()
    if config["sta"] and config["wifi_ssid"]:
        if connect_sta(config["wifi_ssid"], config["wifi_password"]):
            print("🚀 Mode STA actif")
            return True
        else:
            print("⚠️ Échec WiFi → Mode AP")
            start_ap()
            return False
    else:
        print("📶 Mode configuration (AP)")
        start_ap()
        return False
