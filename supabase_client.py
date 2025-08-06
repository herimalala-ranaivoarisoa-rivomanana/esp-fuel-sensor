import urequests
import ujson

# 🔑 À remplir avec ton projet
SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = "YOUR_ANON_OR_SERVICE_KEY"
TABLE_NAME = "fuel_levels"

def send_to_supabase(device_id, distance, timestamp):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "device_id": device_id,
        "distance_cm": distance,
        "timestamp": timestamp
    }
    try:
        response = urequests.post(url, headers=headers, data=ujson.dumps(data))
        print("✅ Donnée envoyée:", response.status_code)
        response.close()
    except Exception as e:
        print("❌ Erreur envoi Supabase:", e)
