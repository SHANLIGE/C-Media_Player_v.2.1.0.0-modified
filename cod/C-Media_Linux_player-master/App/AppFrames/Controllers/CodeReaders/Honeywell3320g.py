import base64
import json
import re
import serial
import threading
from ...Event import Event

print("Controlador Honeywell 3320g cargado")

# Puerto por defecto del Honeywell (USB-CDC → /dev/ttyUSB0).
# Se puede sobreescribir via device["NombrePuerto "]
PUERTO_SERIAL = "/dev/ttyACM0"

SUFIJO = b"\r\n"

#deteccion de JPEG para cedulas digitales
JPEG_SOI = bytes([0xFF, 0xD8])


TIMEOUT_INACTIVIDAD = 0.20

CODE_ID_OCR_B     = ord('S')   # 0x53
CODE_ID_PASSPORT  = ord('O')   # 0x4F


class BarCodeReader():
    """
    Configuracion Universal compatible con cedulas Nuevas solo con Newland FM430

    Modos de operación soportados:

    Nota: class name 'BarCodeReader' y firma de eventos son idénticos al
    driver Honeywell para compatibilidad total con el servidor.
    """

    def __init__(self, device=None):
        self.device     = device
        self.result     = None
        self.reader     = None
        self.thread     = None
        self.killThread = False

        #Listado MRZ
        # Acumulamos aquí hasta tener el bloque completo.
        self._mrz_buffer = []      # lista de str, cada elemento = 1 línea MRZ
        self._mrz_tipo   = None    # 'TD1' (3 líneas×30) o 'TD3' (2 líneas×44)

        self._esperando_mrz = False

        self.event  = Event("Omnidireccional.Honeywell")
        self.connect()
        self.detalle = "Lector Universal /dev/ttyACM0 presentation mode"

    #Api publica

    def get_result(self):   return self.result
    def get_event(self):    return self.event
    def clear_result(self): self.result = None
    def clear_event(self):  self.event.clear()

    #conexion

    def connect(self):
        puerto = PUERTO_SERIAL
        if self.device and self.device.get("NombrePuerto "):
            p = self.device["NombrePuerto "]
            if p.startswith("/dev/"):
                puerto = p

        print(f"Honeywell: intentando conectar en {puerto}...")
        try:
            self.reader = serial.Serial(
                port      = puerto,
                baudrate  = 9600,
                bytesize  = serial.EIGHTBITS,
                parity    = serial.PARITY_NONE,
                stopbits  = serial.STOPBITS_ONE,
                timeout   = None,
            )
            print(f"Honeywell: puerto {puerto} abierto correctamente")
        except Exception as e:
            print(f"Honeywell: no se pudo abrir {puerto}: {e}")
            self.event.awake("NotificarError", [json.dumps("Lector No Encontrado")])
            self.reader = None
            return

        if self.reader and self.reader.is_open:
            self.thread = threading.Thread(target=self.receiveData, daemon=True)
            self.thread.start()
        else:
            self.event.awake("NotificarError", [json.dumps("Lector No Encontrado")])
            self.reader = None

    #lectura y procesamiento de datos

    def receiveData(self):
        """
        Acumula bytes del puerto serial.

        Delimitadores:
          1. SUFIJO = CRLF (\\r\\n) → tramas de texto (barcode, cada línea MRZ, QR).
          2. Timeout 200 ms sin bytes → fin de trama de imagen JPEG u otras
             tramas grandes que el Honeywell no termina con CRLF.
        """
        buffer = bytearray()

        while not self.killThread:
            try:
                self.reader.timeout = TIMEOUT_INACTIVIDAD
                byte = self.reader.read(1)
            except Exception as e:
                if self.killThread:
                    break
                print(f"Honeywell error lectura: {e}")
                self.event.awake("NotificarError", [json.dumps("Error al leer los datos")])
                break

            if not byte:
                # Timeout: procesar lo acumulado (p.ej. JPEG sin terminador)
                if buffer:
                    datos  = bytes(buffer)
                    buffer = bytearray()
                    self._despachar(datos)
                    print("Honeywell: esperando siguiente lectura...")
                continue

            buffer += byte

            #Delimitador CRLF estándar de lectores
            if buffer.endswith(SUFIJO):
                datos  = bytes(buffer[: -len(SUFIJO)])
                buffer = bytearray()
                if datos:
                    self._despachar(datos)
                    print("Lector Universal: esperando siguiente lectura...")

    

    def _despachar(self, datos: bytes):
        """Llama a _procesar con manejo de excepciones centralizado."""
        try:
            self._procesar(datos)
        except Exception as e:
            print(f"Honeywell error procesando trama: {e}")
            self._mrz_buffer.clear()
            self.event.awake("NotificarError", [json.dumps("Error al interpretar la lectura")])

    def _procesar(self, datos: bytes):
        """
        Árbol de decisión principal.

        Orden de evaluación:
          0. Imagen JPEG cruda (SOI 0xFF 0xD8)
          1. Code ID 'S' u 'O' al inicio (si el usuario activó Code ID Prefix)
          2. Línea MRZ parcial → acumular en _mrz_buffer
             (el Honeywell con OCR-B/Passport OCR envía cada línea por separado)
          3. Bloque MRZ completo de una sola vez (raro, pero posible)
          4. PDF417 binario (prefix 'P' = 0x50)
          5. Todo imprimible:
             a. QR cédula nueva cifrado → activar espera MRZ
             b. Barcode / QR simple     → EstablecerCodigo
          6. Binario no-JPEG            → _procesar_cedula_alternativa
        """
        print(f"Honeywell: trama recibida  len={len(datos)}  "
              f"prefix=0x{datos[0]:02X} ({chr(datos[0]) if 0x20<=datos[0]<=0x7E else '?'})")

        #Img cruda
        if datos[:2] == JPEG_SOI:
            self._mrz_buffer.clear()
            return self._procesar_imagen_jpeg(datos)

        #procesar Code ID prefix (si está activo en configuración)
        if datos[0] == CODE_ID_OCR_B and len(datos) > 1:
            # 'S' + resto → Specific OCR-B (MRZ TD1 o texto OCR-B)
            return self._procesar_ocr_con_code_id(datos[1:], tipo_esperado="TD1")
        if datos[0] == CODE_ID_PASSPORT and len(datos) > 1:
            # 'O' + resto → Passport OCR (MRZ TD3)
            return self._procesar_ocr_con_code_id(datos[1:], tipo_esperado="TD3")

        #lineas parciales MRZ
        if self._es_linea_mrz_parcial(datos):
            return self._acumular_linea_mrz(datos)

        if self._mrz_buffer:
            print(f"Honeywell: descartando buffer MRZ parcial ({len(self._mrz_buffer)} líneas) "
                  f"— trama nueva no compatible")
            self._mrz_buffer.clear()
            self._mrz_tipo = None

       
        if self._es_mrz_completo(datos):
            self._esperando_mrz = False
            return self._procesar_mrz_td1(datos)

        
        if datos[0] == 0x50:
            return self._procesar_cedula_pdf417(datos[1:])

      
        if all(0x20 <= b <= 0x7E for b in datos):
            try:
                texto = datos.decode("utf-8").strip()
            except Exception:
                return

             
            if self._esperando_mrz:
                self.event.awake(
                    "NotificarError",
                    [json.dumps(
                        "Cédula digital: escanee las 3 líneas de texto OCR-B "
                        "(zona MRZ) en la parte inferior del reverso, no el QR."
                    )]
                )
                return None

            if self._es_qr_cedula_nueva(texto):
                return self._procesar_qr_cedula_nueva(texto)

            # Barcode / QR simple
            print(f"Honeywell: barcode simple → EstablecerCodigo: {texto[:60]}")
            self.event.awake("EstablecerCodigo", [json.dumps(texto)])
            return texto

       
        return self._procesar_cedula_alternativa(datos[1:])

    #multi linea MRZ (OCR-B / Passport OCR)

    def _es_linea_mrz_parcial(self, datos: bytes) -> bool:
        """
        Detecta si la trama es una LÍNEA INDIVIDUAL de un MRZ (no el bloque completo).

        Criterios:
          - Todo imprimible: letras, dígitos, '<' y espacio.
          - Longitud compatible con una línea MRZ:
              TD1 (cédula):   30 chars por línea
              TD3 (pasaporte): 44 chars por línea
          - No tiene caracteres de control (LF, CR ya fueron stripados por SUFIJO).
        """
        largo = len(datos)
        if largo not in range(28, 48):   # margen ±2 chars
            return False
        # Solo caracteres MRZ válidos
        for b in datos:
            if not (b == 0x3C or              # '<'
                    0x41 <= b <= 0x5A or      # A-Z
                    0x30 <= b <= 0x39 or      # 0-9
                    b == 0x20):               # espacio (raro pero posible)
                return False
        return True

    def _acumular_linea_mrz(self, datos: bytes):
        """
        Agrega la línea recibida al buffer MRZ y, si está completo, lo procesa.

        TD1 (cédulas):   3 líneas de ~30 chars → completo en 3 eventos
        TD3 (pasaporte): 2 líneas de ~44 chars → completo en 2 eventos
        """
        linea = datos.decode("ascii", errors="replace").strip()
        largo = len(linea)

        # Detectar tipo según longitud de la primera línea
        if not self._mrz_buffer:
            self._mrz_tipo = "TD3" if largo >= 40 else "TD1"
            print(f"Honeywell: inicio buffer MRZ ({self._mrz_tipo}): [{linea}]")
        else:
            print(f"Honeywell: línea MRZ {len(self._mrz_buffer)+1}: [{linea}]")

        self._mrz_buffer.append(linea)

        lineas_necesarias = 2 if self._mrz_tipo == "TD3" else 3

        if len(self._mrz_buffer) >= lineas_necesarias:
            bloque = "\n".join(self._mrz_buffer)
            self._mrz_buffer.clear()
            self._mrz_tipo   = None
            self._esperando_mrz = False
            return self._procesar_mrz_td1(bloque.encode("ascii"))

        # Aún faltan líneas; avisar al operador para que no mueva la cédula
        faltantes = lineas_necesarias - len(self._mrz_buffer)
        print(f"Honeywell: MRZ parcial acumulado — faltan {faltantes} línea(s)")
        return None

    def _procesar_ocr_con_code_id(self, datos: bytes, tipo_esperado: str):
        """
        Maneja la trama cuando el Honeywell envía Code ID prefix ('S' u 'O').
        El resto puede ser una línea parcial o el bloque completo.
        """
        if self._es_linea_mrz_parcial(datos):
            return self._acumular_linea_mrz(datos)
        if self._es_mrz_completo(datos):
            return self._procesar_mrz_td1(datos)
        # Fallback: tratar como texto
        try:
            texto = datos.decode("utf-8").strip()
            self.event.awake("EstablecerCodigo", [json.dumps(texto)])
        except Exception:
            pass

    # ── Handlers específicos ───────────────────────────────────────────────

    def _procesar_imagen_jpeg(self, datos: bytes):
        """
        El Honeywell envió un JPEG crudo (modo Image Output, configurado via EasySet).
        Se encapsula en base64 y se emite EstablecerJsonDocumento para que el
        software externo (OpenCV / Tesseract / motor ICAO) haga OCR/MRZ.

        Payload:
          { "TipoCaptura": "imagen", "Formato": "jpeg",
            "TipoDocumento": "pendiente_ocr", "Datos": "<base64 JPEG>" }
        """
        print(f"Honeywell: JPEG recibido ({len(datos)} bytes) → EstablecerJsonDocumento")
        payload = {
            "TipoCaptura":   "imagen",
            "Formato":       "jpeg",
            "TipoDocumento": "pendiente_ocr",
            "Datos":         base64.b64encode(datos).decode("ascii"),
        }
        self._emitir_json(payload)
        return payload

    def _procesar_qr_cedula_nueva(self, texto: str):
        """
        QR cifrado cédula colombiana digital (policarbonato 2022+).
        Activa _esperando_mrz para el flujo de doble escaneo.
        """
        print(f"Honeywell: QR cédula nueva ({len(texto)} chars) — activando espera MRZ")
        self._esperando_mrz = True
        self.event.awake(
            "NotificarError",
            [json.dumps(
                "Cédula digital nueva: escanee las 3 líneas de texto (zona MRZ) "
                "en la parte inferior del reverso de la cédula para leer los datos."
            )]
        )
        return None

    def _procesar_mrz_td1(self, datos: bytes) -> dict:
        """
        Parsea MRZ TD1 (ICAO 9303, 3 líneas × 30 chars) o TD3 (2 × 44 chars).
        Admite bloques continuos de 90 bytes, o líneas separadas por LF/CR.
        Emite EstablecerJsonDocumento con los campos estructurados.
        """
        try:
            raw    = datos.decode("ascii", errors="replace")
            lineas = [l for l in raw.replace("\r", "\n").split("\n") if len(l.strip()) >= 28]

            if len(lineas) < 2:
                bloque = raw.replace("\r", "").replace("\n", "")
                if len(bloque) >= 90:
                    lineas = [bloque[0:30], bloque[30:60], bloque[60:90]]
                elif len(bloque) >= 88:      # TD3: 2 × 44
                    lineas = [bloque[0:44], bloque[44:88]]
                else:
                    print(f"Honeywell MRZ: bloque insuficiente (len={len(bloque)})")
                    self.event.awake("NotificarError", [json.dumps("MRZ incompleto")])
                    return None

            # TD3 (pasaporte) o TD1 (cédula / extranjería)
            es_td3 = len(lineas) == 2 and len(lineas[0].strip()) >= 40

            if es_td3:
                l1 = lineas[0].ljust(44)
                l2 = lineas[1].ljust(44)
                tipo_doc_raw = l1[0:2].strip("<").strip()
                pais_emisor  = l1[2:5].strip("<").strip()
                numero_raw   = l1[5:14].replace("<", "").strip()
                fecha_nac_raw = l2[0:6]
                sexo_raw      = l2[7]
                nombres_part  = l1[13:44].rstrip("<")
                partes        = nombres_part.split("<<")
            else:
                l1 = lineas[0].ljust(30)
                l2 = lineas[1].ljust(30)
                l3 = lineas[2].ljust(30) if len(lineas) > 2 else ""
                tipo_doc_raw  = l1[0:2].strip("<").strip()
                pais_emisor   = l1[2:5].strip("<").strip()
                numero_raw    = l1[5:14].replace("<", "").strip()
                fecha_nac_raw = l2[0:6]
                sexo_raw      = l2[7]
                nombres_part  = l3.rstrip("<")
                partes        = nombres_part.split("<<")

            if tipo_doc_raw in ("ID",):
                tipo_doc = "2"
            elif tipo_doc_raw in ("IR", "IX", "IA"):
                tipo_doc = "4"
            elif tipo_doc_raw in ("P", "PA"):
                tipo_doc = "5"
            else:
                tipo_doc = "2"

            sexo = sexo_raw if sexo_raw in ("M", "F") else ""

            primer_apellido  = partes[0].replace("<", " ").strip() if len(partes) > 0 else ""
            segundo_apellido = partes[1].replace("<", " ").strip() if len(partes) > 1 else ""
            nombres_raw      = partes[2].replace("<", " ").strip() if len(partes) > 2 else ""
            nombres_split    = nombres_raw.split(" ")
            primer_nombre    = nombres_split[0] if len(nombres_split) > 0 else ""
            segundo_nombre   = nombres_split[1] if len(nombres_split) > 1 else ""

            cedula = {
                "TipoDocumento":     tipo_doc,
                "Numero":            numero_raw.lstrip("0") or numero_raw,
                "PrimerApellido":    primer_apellido,
                "SegundoApellido":   segundo_apellido,
                "PrimerNombre":      primer_nombre,
                "SegundoNombre":     segundo_nombre,
                "Sexo":              sexo,
                "FechaDeNacimiento": self._mrz_fecha(fecha_nac_raw),
                "RH":                "",
                "Departamento":      "",
                "Ciudad":            "",
                "LugarNacimiento":   "",
                "Pais":              pais_emisor if pais_emisor else "COL",
            }
            print(f"Honeywell MRZ → {cedula['Numero']} {cedula['PrimerNombre']} {cedula['PrimerApellido']}")
            self._emitir_json(cedula)
            return cedula

        except Exception as e:
            print(f"Honeywell error parseando MRZ: {e}")
            self.event.awake("NotificarError", [json.dumps("Error al interpretar MRZ")])
            return None

    def _procesar_cedula_pdf417(self, byte: bytearray) -> dict:
        """Parsea cédula PDF417 binaria (cédula amarilla con hologramas)."""
        cedula = {}
        try:
            if byte[32:34] == b"CE":
                cedula["TipoDocumento"] = "2"
                b = 34
                buf = bytearray()
                while byte[b] < 0x3A and byte[b] > 0x2F:
                    buf.append(byte[b]); b += 1
                cedula["Numero"]          = buf.decode("utf-8").replace("\0","").lstrip("0")
                cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i+52]  for i in range(30)))
                cedula["SegundoApellido"] = self.replaces(bytearray(byte[i+82]  for i in range(30)))
                pn = bytearray(); sn = bytearray(); b = 0
                while byte[b+112] != 0x20: pn.append(byte[b+112]); b += 1
                while byte[b+112] != 0:    sn.append(byte[b+112]); b += 1
                cedula["PrimerNombre"]      = self.replaces(pn)
                cedula["SegundoNombre"]     = self.replaces(sn)
                cedula["Sexo"]              = chr(byte[200])
                cedula["FechaDeNacimiento"] = bytearray(byte[i+192] for i in range(8)).decode("utf-8")
                cedula["RH"]                = bytearray(byte[i+217] for i in range(2)).decode("utf-8")
                cedula["Pais"]              = self.replaces(bytearray(byte[i+220] for i in range(30)))
                dept = bytearray(byte[i+160] for i in range(2)).decode("utf-8").replace("\0","")
                city = bytearray(byte[i+162] for i in range(3)).decode("utf-8").replace("\0","")
                cedula["Departamento"]    = dept
                cedula["Ciudad"]          = city
                cedula["LugarNacimiento"] = dept + city

            elif byte[0] == ord("I"):
                cedula["TipoDocumento"] = "1"
                buf = bytearray(); tempOffset = 0
                if byte[48] == ord("0") and byte[49] == ord("0"):
                    b = 50
                    while byte[b] < 0x3A and byte[b] > 0x2F: buf.append(byte[b]); b += 1
                else:
                    b = 48
                    while byte[b] < 0x3A and byte[b] > 0x2F: buf.append(byte[b]); b += 1
                    tempOffset = b
                cedula["Numero"]          = buf.decode("utf-8")
                cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i+tempOffset] for i in range(23)))
                cedula["SegundoApellido"] = self.replaces(bytearray(byte[i+81]  for i in range(23)))
                cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i+104] for i in range(23)))
                cedula["SegundoNombre"]   = self.replaces(bytearray(byte[i+127] for i in range(23)))
                cedula["Sexo"]              = chr(byte[152])
                cedula["FechaDeNacimiento"] = bytearray(byte[i+153] for i in range(8)).decode("utf-8")
                cedula["RH"]                = bytearray(byte[i+167] for i in range(2)).decode("utf-8")
                cedula["Departamento"]      = bytearray(byte[i+161] for i in range(2)).decode("utf-8")
                cedula["Ciudad"]            = bytearray(byte[i+163] for i in range(3)).decode("utf-8")
                cedula["LugarNacimiento"]   = cedula["Departamento"] + cedula["Ciudad"]
                cedula["Pais"]              = "COL"

            elif byte[0] == ord("0") and byte[1] == ord("0") and byte[2] == ord("0"):
                cedula["TipoDocumento"] = "3"
                buf = bytearray(); b = 0
                while byte[b] == ord("0"): b += 1
                while byte[b] < 0x3A and byte[b] > 0x2F: buf.append(byte[b]); b += 1
                cedula["Numero"]          = buf.decode("UTF-8")
                cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i+31] for i in range(25)))
                cedula["SegundoApellido"] = self.replaces(bytearray(byte[i+56] for i in range(25)))
                cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i+81] for i in range(25)))
                cedula["SegundoNombre"]   = ""
                cedula["Ciudad"] = cedula["Departamento"] = cedula["FechaDeNacimiento"] = ""
                cedula["RH"] = cedula["Sexo"] = cedula["LugarNacimiento"] = ""
                cedula["Pais"] = "COL"

            else:
                cedula["TipoDocumento"] = "0"
                buf = bytearray()
                if byte[48] == ord("0") and byte[49] == ord("0"):
                    b = 50
                    while byte[b] < 0x3A and byte[b] > 0x2F: buf.append(byte[b]); b += 1
                else:
                    b = 48
                    while byte[b] < 0x3A and byte[b] > 0x2F: buf.append(byte[b]); b += 1
                cedula["Numero"]          = buf.decode("utf-8")
                cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i+58]  for i in range(23)))
                cedula["SegundoApellido"] = self.replaces(bytearray(byte[i+81]  for i in range(23)))
                cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i+104] for i in range(23)))
                cedula["SegundoNombre"]   = self.replaces(bytearray(byte[i+127] for i in range(23)))
                cedula["Sexo"]              = chr(byte[151])
                cedula["FechaDeNacimiento"] = bytearray(byte[i+152] for i in range(8)).decode("utf-8")
                cedula["RH"]                = bytearray(byte[i+166] for i in range(2)).decode("utf-8")
                cedula["Departamento"]      = bytearray(byte[i+160] for i in range(2)).decode("utf-8")
                cedula["Ciudad"]            = bytearray(byte[i+162] for i in range(3)).decode("utf-8")
                cedula["LugarNacimiento"]   = cedula["Departamento"] + cedula["Ciudad"]
                cedula["Pais"]              = "COL"

            self._emitir_json(cedula)
            return cedula

        except Exception as e:
            print(f"Honeywell error PDF417: {e}")
            self.event.awake("NotificarError", [json.dumps("Error al interpretar la cédula")])
            return None

    def _procesar_cedula_alternativa(self, byte: bytearray) -> dict:
        """Parsea cédulas binarias no-JPEG, no-PDF417, no-MRZ."""
        try:
            cedula = {"TipoDocumento": "2"}
            raw    = bytearray(byte[47:57]).decode("utf-8")
            cedula["Numero"]          = raw.lstrip("0") if raw[0] == "0" else raw
            cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i+57]  for i in range(23)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i+80]  for i in range(23)))
            cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i+103] for i in range(23)))
            cedula["SegundoNombre"]   = self.replaces(bytearray(byte[i+126] for i in range(23)))
            cedula["Sexo"] = cedula["FechaDeNacimiento"] = cedula["RH"] = ""
            cedula["Departamento"] = cedula["Ciudad"] = cedula["LugarNacimiento"] = ""
            cedula["Pais"] = "COL"
            self._emitir_json(cedula)
            return cedula
        except Exception as e:
            print(f"Honeywell error cédula alternativa: {e}")
            self.event.awake("NotificarError", [json.dumps("Error al interpretar la cédula")])
            return None

    # ── Helpers ────────────────────────────────────────────────────────────

    def _emitir_json(self, payload: dict):
        """Serializa con la codificación del servidor y emite EstablecerJsonDocumento."""
        ret = json.dumps(payload).replace("{","$#$").replace("}","#$#").replace(",","%#")
        self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])

    def _es_mrz_completo(self, datos: bytes) -> bool:
        """
        Detecta bloque MRZ completo (TD1: 85-105 bytes, comienza con 'I').
        Permite LF/CR como separadores de línea.
        """
        if len(datos) < 85 or len(datos) > 105:
            return False
        if datos[0] != ord('I'):
            return False
        for b in datos:
            if b in (0x0A, 0x0D):
                continue
            if b < 0x20 or b > 0x7E:
                return False
        return True

    def _es_qr_cedula_nueva(self, texto: str) -> bool:
        """
        Heurística: QR cifrado cédula colombiana nueva (policarbonato 2022+).
        >100 chars, contenido base64/hex sin espacios significativos.
        """
        if len(texto) < 100 or len(texto.split()) > 5:
            return False
        return bool(re.match(r'^[A-Za-z0-9+/=\-_]+$', texto))

    def _mrz_fecha(self, aammdd: str) -> str:
        """Convierte fecha MRZ AAMMDD → AAAAMMDD."""
        try:
            if len(aammdd) != 6: return ""
            aa, mm, dd = aammdd[0:2], aammdd[2:4], aammdd[4:6]
            year = (2000 + int(aa)) if int(aa) < 30 else (1900 + int(aa))
            return f"{year}{mm}{dd}"
        except Exception:
            return aammdd

    def replaces(self, byte: bytearray) -> str:
        """Reemplaza caracteres no-UTF8 (ñ, etc.) en bytearray."""
        for i in range(len(byte)):
            if byte[i] == 0xD1:
                byte[i:] = "Ñ".encode("utf-8") + byte[i+1:]
        s = byte.decode("utf-8").replace("\0","").strip()
        return s.replace("?","Ñ") if "?" in s else s

    # ── Desconexión ────────────────────────────────────────────────────────

    def disconnect(self):
        """Detiene el hilo lector y cierra el puerto serial."""
        self.killThread = True
        if self.reader and self.reader.is_open:
            try: self.reader.cancel_read()
            except Exception: pass
            try: self.reader.close()
            except Exception: pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)