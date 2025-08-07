import machine
import socket
import ota
from wifi import save_config, setup_wifi
from boot import check_for_commands # Importer la fonction depuis boot

def web_page():
    return """<!DOCTYPE html>
<html>
<head><title>Config WiFi ESP</title></head>
<body>
    <nav style='margin-bottom:15px'>
        <a href='http://192.168.4.1:8080/mesure' style='font-weight:bold'>📈 Aller à la page de mesures</a>
    </nav>
    <h2>Configuration WiFi</h2>
    <form action="/save" method="get">
        SSID:<br><input type="text" name="ssid"><br>
        Password:<br><input type="password" name="pass"><br><br>
        <input type="submit" value="Enregistrer">
    </form>
</body>
</html>"""

def start_config_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 80))
    s.listen(5)
    print("🌐 Serveur de configuration démarré sur http://192.168.4.1")

    while True:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()

        if '/save?' in request:
            params = request.split('GET /save?')[1].split(' ')[0]
            pairs = params.split('&')
            ssid = pairs[0].split('=')[1].replace('%20', ' ')
            password = pairs[1].split('=')[1].replace('%20', ' ')
            save_config(ssid, password, sta=True)
            conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            conn.sendall("<h3>✅ Config enregistrée ! Redémarrage...</h3>")
            conn.close()
            machine.reset()
        else:
            conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            conn.sendall(web_page())
            conn.close()

# --- Logique principale ---
if setup_wifi():
    check_for_commands() # Vérifier les commandes après connexion
    ota.ota_update()     # Vérifier les mises à jour OTA
    print("📡 Lancement du capteur...")
    import sensor

    # --- Serveur HTTP pour /mesure et /mesure_data ---
    import socket
    import ujson

    def serve_mesure():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', 8080))
        s.listen(2)
        print("🌐 Page mesures dispo sur http://<ip>:8080/mesure")
        while True:
            conn, addr = s.accept()
            try:
                req = conn.recv(1024).decode()
                if req.startswith('GET /mesure_data'):
                    history = sensor.get_mesure_history()
                    labels = [time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(ts)) for ts, v in history]
                    values = [round(v,2) for ts, v in history]
                    resp = ujson.dumps({"labels": labels, "values": values})
                    conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
                    conn.sendall(resp)
                elif req.startswith('GET /mesure'):
                    with open('mesure.html') as f:
                        html = f.read()
                    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                    conn.sendall(html)
                elif req.startswith('GET /mesure_chart.js'):
                    with open('mesure_chart.js') as f:
                        js = f.read()
                    conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/javascript\r\n\r\n")
                    conn.sendall(js)
                else:
                    conn.send("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nNot found")
            except Exception as e:
                print("Erreur HTTP:", e)
            finally:
                conn.close()
    
    import _thread
    _thread.start_new_thread(serve_mesure, ())

    # Boucle capteur principale (déjà dans sensor.py)
    # (Ne rien faire ici, la boucle tourne déjà)
else:
    # Si le WiFi n'est pas configuré, lancer le serveur de configuration
    start_config_server()
