import urequests
import ujson
import time
from wifi import load_config

SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = "YOUR_ANON_KEY"
TABLE_NAME = "calibration_table"

def fetch_calibration_from_supabase():
    """Télécharge les données de calibration depuis Supabase."""
    cfg = load_config()
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?device_id=eq.{cfg.get('device_id')}&order=level_cm"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json"
    }
    try:
        response = urequests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            response.close()
            if not data:
                print("⚠️ Aucune calibration trouvée")
                return None

            # On prend la version la plus récente
            version = max(row["version"] for row in data)
            points = [{"level": row["level_cm"], "volume": row["volume_liters"]} for row in data]

            return {"version": version, "points": points}
        else:
            print("❌ Erreur calibration HTTP:", response.status_code)
            response.close()
            return None
    except Exception as e:
        print("❌ Exception calibration:", e)
        return None

def load_local_calibration():
    """Charge calibration depuis fichier local."""
    try:
        with open("calibration.json") as f:
            return ujson.load(f)
    except:
        return None

def save_local_calibration(data):
    """Sauvegarde calibration dans fichier local."""
    with open("calibration.json", "w") as f:
        ujson.dump(data, f)

def update_calibration():
    """Vérifie si calibration locale est à jour et met à jour si besoin."""
    remote = fetch_calibration_from_supabase()
    if not remote:
        return load_local_calibration()  # utiliser locale si dispo

    local = load_local_calibration()
    if not local or remote["version"] > local["version"]:
        print("⬇️ Mise à jour calibration.json")
        save_local_calibration(remote)
        return remote
    return local
