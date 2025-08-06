import urequests
from wifi import load_config, save_config, setup_wifi

COMMAND_URL = "https://raw.githubusercontent.com/herimalala-ranaivoarisoa-rivomanana/esp-fuel-sensor/main/device_command.json"

def check_force_ap():
    try:
        cfg = load_config()
        device_id = cfg.get("device_id", "UNKNOWN")
        r = urequests.get(COMMAND_URL)
        cmd = r.json()
        r.close()

        if cmd.get("target_device") == device_id and cmd.get("force_ap"):
            print("⚠️ Commande reçue → Forcer mode AP")
            save_config(cfg["wifi_ssid"], cfg["wifi_password"], sta=False, version=cfg["current_version"])
            return True
    except Exception as e:
        print("Erreur lecture commande:", e)
    return False

print("🚀 Booting ESP...")
if not check_force_ap():
    setup_wifi()
