import json
from ..Connection.SerialConnection import SerialConnection
import threading
import logging
from ...Event import Event
import re




class BarCodeReader():

    def __init__(self, device=None):
        self.device = device if device else "/dev/ttyACM0"

        self.reader = None
        self.thread = None
        self.killThread = False

        self.event = Event("Omnidireccional.Honeywell")
        self.detalle = "Lectura Serial Honeywell"
        
    def get_event(self):
        return self.event
    # --------------------------------------------------
    # CONEXIÓN
    # --------------------------------------------------
    def connect(self):
        if self.thread is not None:
            logging.warning("Honeywell: connect() duplicado ignorado")
            return

        try:
            self.reader = SerialConnection(
                self.device,
                parity=0,
                stopbits=1,
                baudrate=9600,
                timeout=1
            )
        except Exception as e:
            logging.error(f"Honeywell error abriendo puerto: {e}")
            return

        if self.reader.device:
            self.killThread = False
            self.thread = threading.Thread(target=self.receiveData, daemon=True)
            self.thread.start()
            logging.info(f"Honeywell conectado en {self.device}")
        else:
            logging.error("Honeywell: no se pudo abrir el puerto")

    # --------------------------------------------------
    # LECTURA CONTINUA
    # --------------------------------------------------
    def receiveData(self):
        

        while not self.killThread:
            try:
                raw = self.reader.device.readline()
            except Exception as e:
                logging.error(f"Error leyendo serial: {e}")
                break

            if not raw:
                continue

            print("RAW:", raw)  # DEBUG REAL

            try:
                texto = raw.decode("latin-1", errors="ignore")

                # 🔥 MISMA LÓGICA QUE TU SCRIPT
                match = re.search(r'(\d{10,})([A-Z]{2,})', texto)

                if match:
                    digits = match.group(1)
                    cedula = digits[-10:].lstrip("0")

                    if cedula:
                        print("CÉDULA DETECTADA:", cedula)

                        self._auto_turno(cedula)

                else:
                    print("NO CÉDULA:", texto[:50])

            except Exception as e:
                logging.error(f"Parse error: {e}")

    # --------------------------------------------------
    # PROCESAMIENTO
    # --------------------------------------------------
    def procesar_datos(self, prefix, byte):
        
        # 🟢 DOCUMENTO REAL (cédula)
        if prefix == 80:
            cedula = self._parsear_cedula(byte)

            if cedula and "Numero" in cedula:
                numero = cedula["Numero"]
                logging.info(f"CÉDULA OK: {numero}")

                # 🔥 ENVÍO A JS (AUTOTURNO)
                self._auto_turno(numero)

        # 🟡 CODIGO SIMPLE
        else:
            try:
                res = ""
                for elem in byte:
                    if elem <= 32 or elem >= 126:
                        return
                    res += chr(elem)

                if res:
                    logging.info(f"Código simple: {res}")
                    self.event.awake("EstablecerCodigo", [json.dumps(res)])

            except:
                return

    # --------------------------------------------------
    # AUTO TURNO
    # --------------------------------------------------
    def _auto_turno(self, cedula):
        

        if not self.event.isLoaded or not self.event.page:
                logging.warning("JS bloqueado: WebView no lista")
                return
        
        print("EVENT STATUS:", self.event.isLoaded, self.event.page is not None)
        self.event.page.runJavaScript('alert("FUNCIONA")')
        self.event.page.runJavaScript("""
        console.log([...document.querySelectorAll('button, a, div')].map(b => b.innerText));
        """)

        js = f"""
            console.log("AUTO TURNO → {cedula}");

            let intentos = 0;

            function flujoTurno() {{

                intentos++;

                if (intentos > 30) {{
                    console.log("❌ Timeout flujo turno");
                    return;
                }}

                // 🔥 buscar cualquier botón clickeable real
                let botones = [...document.querySelectorAll('button, a, div')];

                // 1. CONTINUAR
                let continuar = botones.find(el =>
                    (el.innerText || "").trim().toLowerCase() === "continuar"
                );

                if (continuar) {{
                    console.log("➡️ CLICK CONTINUAR");
                    continuar.click();
                    setTimeout(flujoTurno, 600);
                    return;
                }}

                // 2. CÉDULA
                let cedulaBtn = botones.find(el =>
                    (el.innerText || "").toLowerCase().includes("cédula")
                );

                if (cedulaBtn) {{
                    console.log("➡️ CLICK CÉDULA");
                    cedulaBtn.click();
                    setTimeout(flujoTurno, 600);
                    return;
                }}

                // 3. INPUT REAL (más específico)
                let input = document.querySelector('input[type="text"], input:not([type])');

                if (input && input.offsetParent !== null) {{
                    console.log("➡️ INPUT LISTO");

                    input.focus();
                    input.value = "{cedula}";

                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));

                    setTimeout(() => {{
                        input.dispatchEvent(new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                        }}));

                        console.log("✅ TURNO ENVIADO");
                    }}, 300);

                    return;
                }}

                setTimeout(flujoTurno, 600);
            }}

            flujoTurno();
            """
        
        self.event.awake_js(js)
        
        

    # --------------------------------------------------
    # PARSER SIMPLIFICADO (ROBUSTO)
    # --------------------------------------------------
    def _parsear_cedula(self, byte):
        try:
            texto = byte.decode("utf-8", errors="ignore")

            import re

            # 🔹 Buscar donde empieza el nombre (letras en mayúscula)
            nombre_match = re.search(r'[A-Z]{3,}', texto)

            if not nombre_match:
                return None

            inicio_nombre = nombre_match.start()

            # 🔹 Tomar solo lo que está ANTES del nombre
            zona_numeros = texto[:inicio_nombre]

            # 🔹 Buscar bloques de números largos
            numeros = re.findall(r'\d{8,12}', zona_numeros)

            if not numeros:
                return None

            candidato = numeros[-1]  # el más cercano al nombre

            # 🔥 REGLA TUYA
            if candidato.startswith("0"):
                numero = candidato[-8:]   # tomar últimos 8
            else:
                numero = candidato[-10:]  # tomar últimos 10

            return {
                "TipoDocumento": "0",
                "Numero": numero
            }

        except Exception as e:
            logging.error(f"Error parseando cédula: {e}")
            return None
    # --------------------------------------------------
    def disconnect(self):
        self.killThread = True
        if self.reader:
            self.reader.disconnect()
        if self.thread:
            self.thread.join(timeout=2)
