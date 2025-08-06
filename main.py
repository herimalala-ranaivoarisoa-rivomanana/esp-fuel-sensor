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
    import sensor        # Lancer l'application principale
else:
    # Si le WiFi n'est pas configuré, lancer le serveur de configuration
    start_config_server()
