import json
import serial
import threading
import logging
from ...Event import Event

print("Controlador Newland cargado")

PUERTO_SERIAL = "/dev/ttyACM0"
SUFIJO = b"\r"


class BarCodeReader():
    """
    Lector de código de barras / documentos Newland en presentation mode.
    Maneja:
      - Cédulas tradicionales (PDF417, prefijo 'P'/0x50)
      - Cédulas antiguas (prefijo '0')
      - Tarjeta de identidad (prefijo 'I')
      - Cédulas nuevas colombianas 2022+ (formato ASCII delimitado)
      - QR / códigos de barras simples
    :param device: dic. Datos del lector (opcional).
    """

    def __init__(self, device=None):
        self.device = device
        self.result = None
        self.reader = None
        self.thread = None
        self.killThread = False

        self.event = Event("Omnidireccional.Newland")

        self.connect()

        self.detalle = "Lector Newland /dev/ttyACM0 presentation mode"

    # ------------------------------------------------------------------ #
    #  API pública                                                         #
    # ------------------------------------------------------------------ #

    def get_result(self):
        return self.result

    def get_event(self):
        return self.event

    def clear_result(self):
        self.result = None

    def clear_event(self):
        self.event.clear()

    # ------------------------------------------------------------------ #
    #  Conexión                                                            #
    # ------------------------------------------------------------------ #

    def connect(self):
        puerto = PUERTO_SERIAL
        if self.device and self.device.get("NombrePuerto", "").startswith("/dev/"):
            puerto = self.device["NombrePuerto"]

        print(f"Newland: intentando conectar en {puerto}...")

        try:
            self.reader = serial.Serial(
                port=puerto,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                inter_byte_timeout=0.1,
            )
            print(f"Newland: puerto {puerto} abierto correctamente")
        except Exception as e:
            print(f"Newland: no se pudo abrir {puerto}: {e}")
            self.event.awake("NotificarError", [json.dumps("Lector No Encontrado")])
            self.reader = None
            return

        if self.reader and self.reader.is_open:
            self.thread = threading.Thread(target=self.receiveData, daemon=True)
            self.thread.start()
        else:
            self.event.awake("NotificarError", [json.dumps("Lector No Encontrado")])
            self.reader = None

    # ------------------------------------------------------------------ #
    #  Recepción                                                           #
    # ------------------------------------------------------------------ #

    def receiveData(self):
        while not self.killThread:
            try:
                trama = self.reader.read(4096)
            except Exception as e:
                if self.killThread:
                    break
                print(f"Newland error lectura: {e}")
                self.event.awake("NotificarError", [json.dumps("Error al leer los datos")])
                break

            if not trama:
                continue

            datos = trama.rstrip(b"\r\n")
            if not datos:
                continue

            print(f"Newland: trama recibida {len(trama)} bytes, prefix={datos[0]}")

            try:
                self.procesar_datos(datos[0], datos[1:])
            except Exception as e:
                print(f"Newland error procesando trama: {e}")
                self.event.awake("NotificarError", [json.dumps("Error al interpretar la lectura")])
                self.result = {"error": str(e), "byte": list(datos[1:])}

            print("Esperando siguiente lectura...")

    # ------------------------------------------------------------------ #
    #  Router principal                                                    #
    # ------------------------------------------------------------------ #

    def procesar_datos(self, prefix, byte):
        """
        Detecta el tipo de documento y llama al parser correspondiente.
        Tipos soportados:
          - prefix=0x50 ('P') → cédula tradicional PDF417
          - prefix=0x30 ('0'), '0','0' siguientes → cédula antigua
          - prefix=0x49 ('I') → tarjeta de identidad
          - prefix=0x30 con datos no imprimibles → cédula alternativa (offsets confirmados)
          - payload ASCII con delimitadores → cédula nueva 2022+
          - todo imprimible → QR / código de barras
        """
        full = bytearray([prefix]) + bytearray(byte)

        # ── 1. Cédula nueva 2022+ ────────────────────────────────────────
        # El Newland envía las cédulas nuevas como texto ASCII con campos
        # separados por caracteres de control (0x1C, 0x1D, 0x1E, 0x1F, etc.)
        # o con marcadores de campo tipo ANSI/AAMVA.
        if self._es_cedula_nueva(full):
            return self._procesar_cedula_nueva(full)

        # ── 2. Cédula tradicional PDF417 (prefijo 'P') ───────────────────
        if prefix == 0x50:  # 'P'
            return self._procesar_cedula_pdf417(byte)

        # ── 3. QR / código de barras simple (todo imprimible) ───────────
        all_printable = all(32 < b < 127 for b in full)
        if all_printable:
            try:
                res = full.decode("ascii").strip()
                print(f"Newland: QR/barcode leído: {res}")
                self.event.awake("EstablecerCodigo", [json.dumps(res)])
                return res
            except Exception:
                return

        # ── 4. Cédula con offsets conocidos (prefijo '0', formato Newland) 
        return self._procesar_cedula_alternativa(byte)

    # ------------------------------------------------------------------ #
    #  Detección de cédula nueva 2022+                                    #
    # ------------------------------------------------------------------ #

    def _es_cedula_nueva(self, full):
        """
        Detecta el formato de cédula nueva colombiana (2022+).
        El Newland la envía como texto ASCII con separadores de campo
        del estándar ANSI (0x1C, 0x1D, 0x1E, 0x1F) o simplemente como
        campos separados por pipe '|' u otros delimitadores.
        Criterios de detección:
          - Contiene separadores ANSI (0x1C–0x1F)
          - O contiene marcadores conocidos como 'DL', 'ANSI'
          - Y los datos son mayormente ASCII imprimible
        """
        has_ansi_sep = any(0x1C <= b <= 0x1F for b in full)
        has_dl_marker = b'DL' in full or b'ANSI' in full
        # Marcador de cédula digital colombiana: arranca con dígitos + texto legible sin nulos masivos
        printable_ratio = sum(1 for b in full if 32 <= b <= 126) / max(len(full), 1)

        if has_ansi_sep or has_dl_marker:
            return True

        # Si >85% imprimible y tiene más de 30 bytes, probablemente es cédula nueva en texto plano
        if printable_ratio > 0.85 and len(full) > 30 and any(b < 32 or b > 126 for b in full):
            # Tiene algunos bytes de control pero es mayormente texto → cédula nueva
            return True

        return False

    def _procesar_cedula_nueva(self, full):
        """
        Parsea cédulas colombianas nuevas (2022+).

        El Newland puede enviarlas en varios sub-formatos:
          A) Separadores ANSI (0x1C–0x1F): campos delimitados en orden estándar
          B) Pipe-delimited: campos separados por '|'
          C) Texto plano con estructura posicional

        IMPORTANTE: Los offsets exactos dependen de la configuración del Newland.
        Si el lector no está configurado y la salida no coincide, se imprime
        el contenido en consola para poder mapear los campos manualmente.
        """
        try:
            cedula = {}
            cedula["TipoDocumento"] = "2"  # Cédula de Ciudadanía nueva
            cedula["Pais"] = "COL"

            # Intentar parseo por separadores ANSI (más común en lectores configurados)
            if any(0x1C <= b <= 0x1F for b in full):
                return self._parsear_ansi(full, cedula)

            # Intentar parseo por pipe
            try:
                texto = full.decode("utf-8", errors="replace").strip()
            except Exception:
                texto = full.decode("latin-1", errors="replace").strip()

            if "|" in texto:
                return self._parsear_pipe(texto, cedula)

            # Formato desconocido → imprimir para diagnóstico y campos vacíos
            print("=" * 60)
            print("NEWLAND: cédula nueva - formato no reconocido")
            print(f"Texto legible: {repr(texto)}")
            print(f"Bytes: {list(full)}")
            print("Por favor comparte este output para mapear los campos.")
            print("=" * 60)

            # Intentar extracción básica por posición para no bloquear el flujo
            cedula = self._parsear_posicional_nuevo(full, cedula)
            ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
            self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
            return cedula

        except Exception as e:
            print(f"Newland: error en cédula nueva: {e}")
            self.event.awake("NotificarError", [json.dumps("Error al interpretar cédula nueva")])
            return None

    def _parsear_ansi(self, full, cedula):
        """
        Parsea formato ANSI/AAMVA con separadores 0x1C–0x1F.
        Orden estándar de la Registraduría en el PDF417:
          Campo 1: número de documento
          Campo 2: primer apellido
          Campo 3: segundo apellido
          Campo 4: primer nombre
          Campo 5: segundo nombre
          Campo 6: fecha nacimiento (YYYYMMDD)
          Campo 7: sexo (M/F)
          Campo 8: RH
          Campo 9: departamento + ciudad (código DIVIPOL)
        """
        campos = []
        campo_actual = bytearray()
        for b in full:
            if 0x1C <= b <= 0x1F:
                campos.append(campo_actual.decode("utf-8", errors="replace").strip().replace("\x00", ""))
                campo_actual = bytearray()
            else:
                campo_actual.append(b)
        if campo_actual:
            campos.append(campo_actual.decode("utf-8", errors="replace").strip().replace("\x00", ""))

        campos = [c for c in campos if c]  # quitar vacíos
        print(f"Newland ANSI: {len(campos)} campos detectados: {campos}")

        # Mapear según el orden estándar (ajustar si el Newland los envía diferente)
        def get(i): return campos[i] if i < len(campos) else ""

        cedula["Numero"]           = get(0).lstrip("0")
        cedula["PrimerApellido"]   = get(1)
        cedula["SegundoApellido"]  = get(2)
        cedula["PrimerNombre"]     = get(3)
        cedula["SegundoNombre"]    = get(4)
        cedula["FechaDeNacimiento"]= get(5)
        cedula["Sexo"]             = get(6)
        cedula["RH"]               = get(7)
        cedula["LugarNacimiento"]  = get(8)
        cedula["Departamento"]     = ""
        cedula["Ciudad"]           = ""

        print(f"Newland: cédula nueva ANSI → {cedula['Numero']} {cedula['PrimerNombre']} {cedula['PrimerApellido']}")

        ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
        self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
        return cedula

    def _parsear_pipe(self, texto, cedula):
        """Parsea formato separado por pipes: num|ap1|ap2|nom1|nom2|fecha|sexo|rh"""
        campos = texto.split("|")
        def get(i): return campos[i].strip() if i < len(campos) else ""

        print(f"Newland pipe: {len(campos)} campos: {campos}")

        cedula["Numero"]            = get(0).lstrip("0")
        cedula["PrimerApellido"]    = get(1)
        cedula["SegundoApellido"]   = get(2)
        cedula["PrimerNombre"]      = get(3)
        cedula["SegundoNombre"]     = get(4)
        cedula["FechaDeNacimiento"] = get(5)
        cedula["Sexo"]              = get(6)
        cedula["RH"]                = get(7)
        cedula["LugarNacimiento"]   = ""
        cedula["Departamento"]      = ""
        cedula["Ciudad"]            = ""

        print(f"Newland: cédula nueva pipe → {cedula['Numero']} {cedula['PrimerNombre']} {cedula['PrimerApellido']}")

        ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
        self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
        return cedula

    def _parsear_posicional_nuevo(self, full, cedula):
        """
        Intento de parseo posicional para cédulas nuevas cuando el formato
        es desconocido. Extrae texto legible como fallback.
        """
        try:
            # Extraer secuencias de texto legible separadas por nulos/control
            segmentos = []
            seg = ""
            for b in full:
                if 32 <= b <= 126:
                    seg += chr(b)
                elif seg.strip():
                    if len(seg.strip()) > 1:
                        segmentos.append(seg.strip())
                    seg = ""
            if seg.strip():
                segmentos.append(seg.strip())

            print(f"Newland: segmentos texto nuevo: {segmentos}")

            # Buscar el número: secuencia de 8-10 dígitos
            numero = ""
            for s in segmentos:
                limpio = s.lstrip("0")
                if limpio.isdigit() and 7 <= len(limpio) <= 10:
                    numero = limpio
                    break

            cedula["Numero"]            = numero
            cedula["PrimerApellido"]    = ""
            cedula["SegundoApellido"]   = ""
            cedula["PrimerNombre"]      = ""
            cedula["SegundoNombre"]     = ""
            cedula["Sexo"]              = ""
            cedula["FechaDeNacimiento"] = ""
            cedula["RH"]                = ""
            cedula["Departamento"]      = ""
            cedula["Ciudad"]            = ""
            cedula["LugarNacimiento"]   = ""
        except Exception:
            pass

        return cedula

    # ------------------------------------------------------------------ #
    #  Cédula tradicional PDF417 (prefijo 'P')                           #
    # ------------------------------------------------------------------ #

    def _procesar_cedula_pdf417(self, byte):
        cedula = {}

        if byte[32:34] == b"CE":
            cedula["TipoDocumento"] = "2"
            b = 34
            cedula_byte = bytearray()
            while byte[b] < 0x3A and byte[b] > 0x2F:
                cedula_byte.append(byte[b])
                b += 1
            cedula["Numero"] = cedula_byte.decode("utf-8").replace("\0", "").lstrip("0")

            cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i + 52] for i in range(30)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 82] for i in range(30)))

            primer_nombre = bytearray()
            segundo_nombre = bytearray()
            b = 0
            while byte[b + 112] != 0x20:
                primer_nombre.append(byte[b + 112])
                b += 1
            while byte[b + 112] != 0:
                segundo_nombre.append(byte[b + 112])
                b += 1
            cedula["PrimerNombre"]  = self.replaces(primer_nombre)
            cedula["SegundoNombre"] = self.replaces(segundo_nombre)
            cedula["Sexo"]          = chr(byte[200])

            cedula["FechaDeNacimiento"] = bytearray(byte[i + 192] for i in range(8)).decode("utf-8")
            cedula["RH"]   = bytearray(byte[i + 217] for i in range(2)).decode("utf-8")
            cedula["Pais"] = self.replaces(bytearray(byte[i + 220] for i in range(30)))

            dept = bytearray(byte[i + 160] for i in range(2)).decode("utf-8").replace("\0", "")
            city = bytearray(byte[i + 162] for i in range(3)).decode("utf-8").replace("\0", "")
            cedula["Departamento"]  = dept
            cedula["Ciudad"]        = city
            cedula["LugarNacimiento"] = dept + city

        elif byte[0] == ord("I"):
            cedula["TipoDocumento"] = "1"
            cedula_byte = bytearray()
            tempOffset = 0
            if byte[48] == ord("0") and byte[49] == ord("0"):
                b = 50
                while byte[b] < 0x3A and byte[b] > 0x2F:
                    cedula_byte.append(byte[b])
                    b += 1
            else:
                b = 48
                while byte[b] < 0x3A and byte[b] > 0x2F:
                    cedula_byte.append(byte[b])
                    b += 1
                tempOffset = b
            cedula["Numero"] = cedula_byte.decode("utf-8")

            cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i + tempOffset] for i in range(23)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 81] for i in range(23)))
            cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i + 104] for i in range(23)))
            cedula["SegundoNombre"]   = self.replaces(bytearray(byte[i + 127] for i in range(23)))
            cedula["Sexo"]            = chr(byte[152])
            cedula["FechaDeNacimiento"] = bytearray(byte[i + 153] for i in range(8)).decode("utf-8")
            cedula["RH"]              = bytearray(byte[i + 167] for i in range(2)).decode("utf-8")
            cedula["Departamento"]    = bytearray(byte[i + 161] for i in range(2)).decode("utf-8")
            cedula["Ciudad"]          = bytearray(byte[i + 163] for i in range(3)).decode("utf-8")
            cedula["LugarNacimiento"] = cedula["Departamento"] + cedula["Ciudad"]
            cedula["Pais"]            = "COL"

        elif byte[0] == ord("0") and byte[1] == ord("0") and byte[2] == ord("0"):
            cedula["TipoDocumento"] = "3"
            cedula_byte = bytearray()
            b = 0
            while byte[b] == ord("0"):
                b += 1
            while byte[b] < 0x3A and byte[b] > 0x2F:
                cedula_byte.append(byte[b])
                b += 1
            cedula["Numero"]          = cedula_byte.decode("UTF-8")
            cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i + 31] for i in range(25)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 56] for i in range(25)))
            cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i + 81] for i in range(25)))
            cedula["SegundoNombre"]   = ""
            cedula["Ciudad"]          = ""
            cedula["Departamento"]    = ""
            cedula["FechaDeNacimiento"] = ""
            cedula["RH"]              = ""
            cedula["Pais"]            = "COL"
            cedula["Sexo"]            = ""
            cedula["LugarNacimiento"] = ""

        else:
            cedula["TipoDocumento"] = "0"
            cedula_byte = bytearray()
            if byte[48] == ord("0") and byte[49] == ord("0"):
                b = 50
                while byte[b] < 0x3A and byte[b] > 0x2F:
                    cedula_byte.append(byte[b])
                    b += 1
            else:
                b = 48
                while byte[b] < 0x3A and byte[b] > 0x2F:
                    cedula_byte.append(byte[b])
                    b += 1
            cedula["Numero"]          = cedula_byte.decode("utf-8")
            cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i + 58] for i in range(23)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 81] for i in range(23)))
            cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i + 104] for i in range(23)))
            cedula["SegundoNombre"]   = self.replaces(bytearray(byte[i + 127] for i in range(23)))
            cedula["Sexo"]            = chr(byte[151])
            cedula["FechaDeNacimiento"] = bytearray(byte[i + 152] for i in range(8)).decode("utf-8")
            cedula["RH"]              = bytearray(byte[i + 166] for i in range(2)).decode("utf-8")
            cedula["Departamento"]    = bytearray(byte[i + 160] for i in range(2)).decode("utf-8")
            cedula["Ciudad"]          = bytearray(byte[i + 162] for i in range(3)).decode("utf-8")
            cedula["LugarNacimiento"] = cedula["Departamento"] + cedula["Ciudad"]
            cedula["Pais"]            = "COL"

        print(f"Newland: PDF417 → {cedula.get('Numero')} {cedula.get('PrimerNombre')} {cedula.get('PrimerApellido')}")
        ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
        self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
        return cedula

    # ------------------------------------------------------------------ #
    #  Cédula alternativa (offsets confirmados con Newland/Honeywell)     #
    # ------------------------------------------------------------------ #

    def _procesar_cedula_alternativa(self, byte):
        """
        Parsea cédulas cuya trama no empieza con 'P'.
        Offsets confirmados empíricamente:
          byte[47:57]   : número (10 dígitos, o 8 con padding de ceros)
          byte[57..79]  : primer apellido  (23 bytes, null-terminated)
          byte[80..102] : segundo apellido (23 bytes, null-terminated)
          byte[103..125]: primer nombre   (23 bytes, null-terminated)
          byte[126..148]: segundo nombre  (23 bytes, null-terminated)
        """
        try:
            cedula = {}
            cedula["TipoDocumento"] = "2"

            raw_numero = bytearray(byte[47:57]).decode("utf-8")
            cedula["Numero"] = raw_numero.lstrip("0") if raw_numero[0] == "0" else raw_numero

            cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i + 57]  for i in range(23)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 80]  for i in range(23)))
            cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i + 103] for i in range(23)))
            cedula["SegundoNombre"]   = self.replaces(bytearray(byte[i + 126] for i in range(23)))

            cedula["Sexo"]              = ""
            cedula["FechaDeNacimiento"] = ""
            cedula["RH"]                = ""
            cedula["Departamento"]      = ""
            cedula["Ciudad"]            = ""
            cedula["LugarNacimiento"]   = ""
            cedula["Pais"]              = "COL"

            print(f"Newland: alternativa → {cedula['Numero']} {cedula['PrimerNombre']} {cedula['PrimerApellido']} {cedula['SegundoApellido']}")

            ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
            self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
            return cedula

        except Exception as e:
            print(f"Newland: error parseando cédula alternativa: {e}")
            self.event.awake("NotificarError", [json.dumps("Error al interpretar la cédula")])
            return None

    # ------------------------------------------------------------------ #
    #  Utilidades                                                          #
    # ------------------------------------------------------------------ #

    def replaces(self, byte):
        for i in range(len(byte)):
            if byte[i] == 0xD1:
                byte[i:] = "Ñ".encode("utf-8") + byte[i + 1:]
        string = byte.decode("utf-8")
        string = string.replace("\x00", "").strip()
        if "?" in string:
            string = string.replace("?", "Ñ")
        return string

    def disconnect(self):
        self.killThread = True
        if self.reader and self.reader.is_open:
            try:
                self.reader.cancel_read()
            except Exception:
                pass
            try:
                self.reader.close()
            except Exception:
                pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)