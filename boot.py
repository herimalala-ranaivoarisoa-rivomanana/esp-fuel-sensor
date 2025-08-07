import esp
esp.osdebug(None)
import gc
import urequests
import machine
from wifi import load_config, save_config

COMMAND_URL = "https://raw.githubusercontent.com/herimalala-ranaivoarisoa-rivomanana/esp-fuel-sensor/main/device_command.json"

def check_for_commands():
    """Vérifie les commandes distantes après la connexion WiFi."""
    try:
        cfg = load_config()
        device_id = cfg.get("device_id", "UNKNOWN")

        print("🔍 Vérification des commandes distantes...")
        r = urequests.get(COMMAND_URL)
        if r.status_code == 200:
            try:
                cmd = r.json()
            except Exception as json_err:
                print("❌ Erreur parsing JSON commande:", r.text)
                raise json_err
        else:
            print("❌ Erreur HTTP commande:", r.status_code)
            r.close()
            return
        r.close()

        if cmd.get("target_device") == device_id and cmd.get("force_ap"):
            print("⚠️ Commande reçue → Forcer mode AP")
            save_config(cfg.get("wifi_ssid"), cfg.get("wifi_password"), sta=False, version=cfg.get("current_version"))
            print("♻️ Redémarrage en mode AP...")
            machine.reset()

    except Exception as e:
        print("❌ Erreur lecture commande:", e)

print("🚀 Booting ESP...")
gc.collect()
