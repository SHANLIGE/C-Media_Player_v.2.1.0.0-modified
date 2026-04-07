from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from App.AppFrames.Controllers.Printers import TM_T88V
import os
import time

app = Flask(__name__)
CORS(app)

# Carpeta donde está index.html
BASE_DIR = "/home/ciel-linux/Escritorio/C-Media_Player_v.2.1.0.0-modified/cod/C-Media_Linux_player-master"

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.route('/print', methods=['POST'])
def print_ticket():
    try:
        printer = TM_T88V.Printer({
            "NombrePuerto": "/dev/ttyUSB0",
            "Baudios": 9600,
            "Paridad": "N",
            "BitsParada": 1,
            "BitsDatos": 8
        })
        print("Entrando a imprimir")

        # Inicializar impresora
        printer.printer.write(b"\x1b@")  # reset
        time.sleep(0.05)

        # Texto de prueba
        texto = "PruebaTurno\nLinea1\nLinea2\nLinea3\n"
        printer.printer.write(texto.encode("utf-8"))
        time.sleep(0.05)

        # Corte de papel
        printer.printer.write(b"\x1dV\x01")
        time.sleep(0.05)

        print("Ticket enviado a la impresora")
        print("DEBUG: enviando bytes al serial:", b"\x1dV\x01")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    print("📢 Flask arrancando en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
