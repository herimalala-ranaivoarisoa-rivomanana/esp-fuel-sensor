import socket
import machine
from wifi import save_config, setup_wifi
import ota

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

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 80))
    s.listen(5)
    print("🌐 Serveur HTTP démarré")

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

if setup_wifi():
    ota.ota_update()
    print("📡 Lancement capteur...")
    import sensor
else:
    start_server()
