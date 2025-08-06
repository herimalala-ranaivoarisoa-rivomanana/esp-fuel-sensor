import urequests
import ujson
from wifi import load_config

SUPABASE_URL = "https://zhzzcirgbhfjmeoohzbo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpoenpjaXJnYmhmam1lb29oemJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ0NTc2NjMsImV4cCI6MjA3MDAzMzY2M30.yPXXjMsdlWyithiY7OroiH4dONeIHHRke3TFCM7G1dc"
TABLE_NAME = "calibration_table"

def fetch_calibration_from_supabase():
    """Télécharge les données de calibration depuis Supabase pour ce device."""
    cfg = load_config()
    device_id = cfg.get("device_id")
    
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?device_id=eq.{device_id}&order=level_cm"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json"
    }
    
    try:
        resp = urequests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            resp.close()

            if not data:
                print("⚠️ Aucune calibration trouvée pour ce device")
                return None

            version = max(row.get("version", 1) for row in data)
            points = [
                {"level": float(row["level_cm"]), "volume": float(row["volume_liters"])}
                for row in data
            ]

            print(f"📥 Calibration récupérée (version {version}, {len(points)} points)")
            return {"version": version, "points": points}
        else:
            print(f"❌ Erreur HTTP calibration: {resp.status_code}")
            resp.close()
            return None
    except Exception as e:
        print("❌ Exception téléchargement calibration:", e)
        return None

def load_local_calibration():
    """Charge la calibration locale depuis fichier."""
    try:
        with open("calibration.json") as f:
            data = ujson.load(f)
            print(f"📂 Calibration locale chargée (version {data.get('version')})")
            return data
    except:
        print("⚠️ Pas de calibration locale disponible")
        return None

def save_local_calibration(data):
    """Sauvegarde la calibration en local."""
    try:
        with open("calibration.json", "w") as f:
            ujson.dump(data, f)
        print("💾 Calibration locale mise à jour")
    except Exception as e:
        print("❌ Erreur sauvegarde calibration locale:", e)

def update_calibration():
    """
    Vérifie la version de la calibration locale et la met à jour si une version
    plus récente est disponible dans Supabase.
    """
    remote = fetch_calibration_from_supabase()
    local = load_local_calibration()

    if not remote:
        # Si pas de remote, on garde local si dispo
        return local

    if not local or remote["version"] > local.get("version", 0):
        print("⬇️ Nouvelle version de calibration détectée, mise à jour...")
        save_local_calibration(remote)
        return remote
    
    print("✅ Calibration locale déjà à jour")
    return local
