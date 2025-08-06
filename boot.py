import urequests
from wifi import load_config, save_config, setup_wifi

COMMAND_URL = "https://raw.githubusercontent.com/herimalala-ranaivoarisoa-rivomanana/esp-fuel-sensor/main/device_command.json"

def check_for_commands():
    """Vérifie les commandes distantes après la connexion WiFi."""
    try:
        cfg = load_config()
        device_id = cfg.get("device_id", "UNKNOWN")

        print("🔍 Vérification des commandes distantes...")
        r = urequests.get(COMMAND_URL)
        cmd = r.json()
        r.close()

        if cmd.get("target_device") == device_id and cmd.get("force_ap"):
            print("⚠️ Commande reçue → Forcer mode AP")
            # Sauvegarder la config pour désactiver le mode STA et redémarrer
            save_config(cfg.get("wifi_ssid"), cfg.get("wifi_password"), sta=False, version=cfg.get("current_version"))
            print("♻️ Redémarrage en mode AP...")
            machine.reset()

    except Exception as e:
        print("❌ Erreur lecture commande:", e)

print("🚀 Booting ESP...")
# Tenter de se connecter au WiFi. Si réussi, vérifier les commandes.
if setup_wifi():
    check_for_commands()
