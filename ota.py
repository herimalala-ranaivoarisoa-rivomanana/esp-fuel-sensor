import urequests
import machine
from wifi import load_config, save_config

VERSION_URL = "https://raw.githubusercontent.com/herimalala-ranaivoarisoa-rivomanana/esp-fuel-sensor/main/version.json"
BASE_URL = "https://raw.githubusercontent.com/herimalala-ranaivoarisoa-rivomanana/esp-fuel-sensor/main/"

def ota_update():
    try:
        cfg = load_config()
        current_version = cfg.get("current_version", "1.0.0")

        print("🔍 Vérification version OTA...")
        r = urequests.get(VERSION_URL)
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception as json_err:
                print("❌ Erreur parsing JSON version:", r.text)
                raise json_err
        else:
            print("❌ Erreur HTTP version:", r.status_code)
            r.close()
            return
        r.close()

        if data["version"] != current_version:
            print("🔄 Nouvelle version:", data["version"])
            for filename in data["files"]:
                print("Téléchargement:", filename)
                r = urequests.get(BASE_URL + filename)
                if r.status_code == 200:
                    with open(filename, "w") as f:
                        f.write(r.text)
                    print("✅", filename, "mis à jour.")
                else:
                    print(f"❌ Erreur HTTP lors du téléchargement de {filename}: {r.status_code}")
                    print(f"Contenu reçu: {r.text}")
                r.close()

            save_config(cfg["wifi_ssid"], cfg["wifi_password"], sta=True, version=data["version"])
            print("♻️ Reboot après OTA...")
            machine.reset()
        else:
            print("✅ Firmware à jour")
    except Exception as e:
        print("❌ Erreur OTA:", e)
