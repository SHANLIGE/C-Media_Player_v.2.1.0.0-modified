import json
import serial
import threading
import logging
from ...Event import Event

print("Controlador Honeywell 3320g cargado")
# Puerto fijo del lector físico
PUERTO_SERIAL = "/dev/ttyACM0"

#sufijo b"\r" o b"\r\n"
SUFIJO = b"\r"

class BarCodeReader():
    """
    Lector de código de barras / documentos en presentation mode
    conectado via puerto serial /dev/ttyACM0.
    Soporta:
      - Cédula antigua (PDF417 binario, prefix=0x50/'P')
      - Nueva cédula digital 2022+ (MRZ TD1, 3 líneas de 30 chars, texto plano)
      - Cédula de extranjería (MRZ TD1 similar a la digital)
      - QR / código de barras simple (todo imprimible)
    Utiliza pyserial directamente.
    :param device: dic. Datos del lector (opcional).
    """

    def __init__(self, device=None):
        self.device = device
        self.result = None
        self.reader = None          # serial.Serial
        self.thread = None
        self.killThread = False

        self.event = Event("Omnidireccional.Honeywell")

        self.connect()

        self.detalle = "Lector Universal /dev/ttyACM0 presentation mode"
      
    # Api publica
    def get_result(self):
        return self.result

    def get_event(self):
        return self.event

    def clear_result(self):
        self.result = None

    def clear_event(self):
        self.event.clear()

   
    def connect(self):
        """
        Abre el puerto /dev/ttyACM0 con pyserial e inicia el hilo lector.
        """
        puerto = PUERTO_SERIAL
        if self.device and self.device.get("NombrePuerto "):
            p = self.device["NombrePuerto "]
            if p.startswith("/dev/"):
                puerto = p
        print(f"Honeywell: intentando conectar en {puerto}...")
       
        try:
            self.reader = serial.Serial(
                port=puerto,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=None,
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

 
    def receiveData(self):
        """
        Lee bytes del puerto en un bucle continuo (presentation mode).
        Acumula hasta encontrar el sufijo configurado, luego procesa.
        Para tramas largas (QR cédula nueva) que pueden no terminar en \\r,
        se usa un timeout de inactividad de 150 ms como delimitador adicional.
        """
        buffer = bytearray()
        TIMEOUT_INACTIVIDAD = 0.15  # segundos sin bytes nuevos → fin de trama

        while not self.killThread:
            try:
                # Intentar leer 1 byte con timeout breve
                self.reader.timeout = TIMEOUT_INACTIVIDAD
                byte = self.reader.read(1)
            except Exception as e:
                if self.killThread:
                    break
                print(f"Honeywell error lectura: {e}")
                self.event.awake("NotificarError", [json.dumps("Error al leer los datos")])
                break

            if not byte:
                # Timeout: si hay datos acumulados sin sufijo, procesarlos igual
                if buffer:
                    datos = buffer
                    buffer = bytearray()
                    if datos:
                        try:
                            self.procesar_datos(datos[0], datos[1:])
                        except Exception as e:
                            print(f"Honeywell error procesando trama (timeout): {e}")
                            self.event.awake(
                                "NotificarError",
                                [json.dumps("Error al interpretar la lectura")]
                            )
                        print("Esperando siguiente lectura...")
                continue

            buffer += byte

            if buffer.endswith(SUFIJO):
                datos = buffer[: -len(SUFIJO)]
                buffer = bytearray()

                if not datos:
                    continue

                try:
                    self.procesar_datos(datos[0], datos[1:])
                except Exception as e:
                    print(f"Honeywell error procesando trama: {e}")
                    self.event.awake(
                        "NotificarError",
                        [json.dumps("Error al interpretar la lectura")]
                    )
                    self.result = {
                        "error": str(e),
                        "byte": list(datos[1:])
                    }
                print("Esperando siguiente lectura...")

 
    def procesar_datos(self, prefix, byte):
        """
        Despacha la trama según su tipo:
          - MRZ nueva cédula / extranjería  → _procesar_mrz_td1
          - Cédula antigua PDF417 (prefix=P) → bloque original
          - QR cédula nueva cifrado          → _procesar_qr_cedula_nueva
          - QR / barcode simple              → EstablecerCodigo
          - Cédula binaria prefix≠P          → _procesar_cedula_alternativa
        """
        print(f"Honeywell: trama recibida, prefix={prefix}, bytes={list(byte)}")

        full = bytearray([prefix]) + bytearray(byte)

        # ── 1. Detectar MRZ (nueva cédula digital / cédula de extranjería / pasaporte)
        #    El MRZ TD1 de Colombia llega como texto puro (~90 chars más separadores).
        #    La primera línea empieza con "ID" (0x49, 0x44).
        if self._es_mrz(full):
            return self._procesar_mrz_td1(full)

        # ── 2. Cédula antigua PDF417 binaria (prefix == ord('P') == 0x50)
        if prefix == 80:  # ord('P')
            return self._procesar_cedula_pdf417(byte)

        # ── 3. Todo imprimible → puede ser QR simple o QR cédula nueva cifrado
        all_printable = all(0x20 <= elem <= 0x7E for elem in full)
        if all_printable:
            try:
                result = full.decode("utf-8").strip()
                # El QR de la nueva cédula colombiana (policarbonato 2022+) está
                # cifrado con criptografía de la Registraduría.  El lector entrega
                # el contenido binario/base64 tal cual; no es parseable en campo.
                # Se distingue porque es significativamente más largo que un código
                # de barras normal (> 100 chars) y empieza con indicadores típicos
                # del estándar ICAO/Registraduría (ej. "COL", dígitos, base64).
                if self._es_qr_cedula_nueva(result):
                    return self._procesar_qr_cedula_nueva(result)
                # Barcode / QR simple
                self.event.awake("EstablecerCodigo", [json.dumps(result)])
                return result
            except Exception:
                return

        # ── 4. Cédula binaria con prefix distinto a 'P'
        return self._procesar_cedula_alternativa(byte)

   
    def _es_mrz(self, full: bytearray) -> bool:
        """
        Detecta si la trama es un MRZ TD1 (3 líneas de ~30 chars).
        Criterios:
          - Empieza con 'I' (0x49), que es la primera letra de 'ID' o 'IR'
          - Es todo texto imprimible (incluyendo '<' = 0x3C y LF/CR como separador)
          - Longitud total entre 85 y 105 bytes (con separadores) o exactamente
            90 bytes (bloque continuo sin separadores, formato habitual del 3320g)
        """
        if len(full) < 85 or len(full) > 105:
            return False
        if full[0] != ord('I'):
            return False
        # Permitir imprimibles + LF (0x0A) / CR (0x0D) como separador de líneas MRZ
        for b in full:
            if b == 0x0A or b == 0x0D:
                continue
            if b < 0x20 or b > 0x7E:
                return False
        return True

    def _es_qr_cedula_nueva(self, texto: str) -> bool:
        """
        Heurística para distinguir el QR cifrado de la cédula nueva colombiana
        (policarbonato 2022+) de un código de barras / QR simple.

        Características observadas del QR de la cédula nueva:
          - Longitud > 100 caracteres (típicamente 200-500 chars).
          - Contiene caracteres base64/hex: letras, dígitos, '+', '/', '=', '-'.
          - NO tiene el formato legible de un turno, URL, etc.
        """
        if len(texto) < 100:
            return False
        # Si tiene espacios o caracteres tipicos de texto normal, no es QR cifrado
        palabras = texto.split()
        if len(palabras) > 5:
            return False
        # Caracteres fuera del conjunto base64/hex son señal de QR normal
        import re
        if re.match(r'^[A-Za-z0-9+/=\-_]+$', texto):
            return True
        return False

    def _procesar_qr_cedula_nueva(self, texto: str) -> dict:
        """
        Maneja el QR cifrado de la cédula colombiana digital (policarbonato 2022+).

        IMPORTANTE: El QR de la cédula nueva colombiana está cifrado con
        criptografía de la Registraduría Nacional (estándar ICAO/eID).
        No es posible extraer datos personales de él sin la clave privada
        de la Registraduría. Lo que sí puede hacer el lector es:
          1. Capturar el blob cifrado para verificación posterior via API.
          2. Usar la zona MRZ del reverso (que el lector sí lee como texto
             plano OCR-B) para obtener los datos básicos — ese flujo ya está
             cubierto por _procesar_mrz_td1.

        Este método emite el evento 'EstablecerQRCedulaNueva' con el payload
        crudo para que el sistema receptor lo use como requiera (p.ej. enviarlo
        a un servicio de verificación de la Registraduría).
        """
        print(f"Honeywell: QR cédula nueva detectado ({len(texto)} chars)")

        # El QR de la cédula digital colombiana (policarbonato 2022+) está
        # completamente cifrado con criptografía de la Registraduría Nacional.
        # Los 576 bytes del payload son cifrado puro — no es posible extraer
        # nombre, número u otros campos sin la clave privada de la Registraduría.
        #
        # Acción: emitir EstablecerJsonDocumento con TipoDocumento="NUEVA_CEDULA"
        # y RequiereMRZ=True para que el sistema/UI le indique al operador que
        # voltee la cédula y escanee la zona MRZ (letras OCR-B del reverso),
        # que sí es legible con el Honeywell 3320g y entrega todos los datos.
        resultado = {
            "TipoDocumento":    "NUEVA_CEDULA",
            "Numero":           "",
            "PrimerApellido":   "",
            "SegundoApellido":  "",
            "PrimerNombre":     "",
            "SegundoNombre":    "",
            "Sexo":             "",
            "FechaDeNacimiento": "",
            "RH":               "",
            "Departamento":     "",
            "Ciudad":           "",
            "LugarNacimiento":  "",
            "Pais":             "COL",
            "RequiereMRZ":      True,
            "MensajeOperador":  "Cédula digital nueva: gire el documento y escanee las letras MRZ del reverso para leer los datos.",
        }
        ret = json.dumps(resultado).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
        self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
        return resultado

    def _procesar_mrz_td1(self, full: bytearray) -> dict:
        """
        Parsea el MRZ TD1 de la nueva cédula digital colombiana (2022+)
        y de la cédula de extranjería.

        Formato TD1 ICAO 9303 – 3 líneas de 30 caracteres:

        Línea 1 (pos 0-29):
          [0-1]   Tipo documento  ('ID')
          [2-4]   País emisor     ('COL' o 'COL'/'AUT'/etc.)
          [5-14]  Número documento (rellenado con '<')
          [15]    Dígito verificador número
          [16-29] Datos opcionales (rellenados con '<')

        Línea 2 (pos 30-59):
          [0-5]   Fecha nacimiento AAMMDD
          [6]     Dígito verificador fecha nac.
          [7]     Sexo ('M'/'F'/'<')
          [8-13]  Fecha expiración AAMMDD
          [14]    Dígito verificador expiración
          [15-28] Nacionalidad + datos opcionales
          [29]    Dígito verificador línea 2

        Línea 3 (pos 60-89):
          Apellidos<<Nombres (separados por '<<', campos por '<')

        Nota: el lector envía las líneas separadas por LF (0x0A) o CR (0x0D).
        """
        try:
            texto = full.decode("ascii", errors="replace").replace("\r", "").replace("\n", "")
            print(f"Honeywell MRZ raw: [{texto}]")

            # Separar las 3 líneas (pueden venir con LF o como bloque continuo de 90)
            raw = full.decode("ascii", errors="replace")
            lineas = [l for l in raw.replace("\r", "\n").split("\n") if len(l.strip()) >= 28]

            if len(lineas) < 3:
                # Intentar como bloque continuo de 90 chars
                bloque = texto.replace("\r", "").replace("\n", "")
                if len(bloque) >= 90:
                    lineas = [bloque[0:30], bloque[30:60], bloque[60:90]]
                else:
                    print(f"Honeywell MRZ: no se pudieron extraer 3 líneas (len={len(texto)})")
                    self.event.awake("NotificarError", [json.dumps("MRZ incompleto")])
                    return None

            l1 = lineas[0].ljust(30)
            l2 = lineas[1].ljust(30)
            l3 = lineas[2].ljust(30)

            # ── Línea 1
            tipo_doc_raw = l1[0:2].strip("<").strip()
            pais_emisor  = l1[2:5].strip("<").strip()
            numero_raw   = l1[5:14].replace("<", "").strip()
            datos_op1    = l1[15:30].replace("<", "").strip()

            # ── Determinar TipoDocumento
            # 'ID' = cédula de ciudadanía digital
            # 'IR' = cédula de extranjería (o 'IX' según versión)
            # 'IP' = pasaporte
            if tipo_doc_raw in ("ID",):
                tipo_doc = "2"   # Cédula de Ciudadanía
            elif tipo_doc_raw in ("IR", "IX", "IA"):
                tipo_doc = "4"   # Cédula de Extranjería
            else:
                tipo_doc = "2"   # Por defecto CC

            # ── Línea 2
            fecha_nac_raw  = l2[0:6]   # AAMMDD
            sexo_raw       = l2[7]
            fecha_exp_raw  = l2[8:14]  # AAMMDD

            # Sexo
            sexo = sexo_raw if sexo_raw in ("M", "F") else ""

            # Fecha de nacimiento AAMMDD → AAAAMMDD
            fecha_nac = self._mrz_fecha(fecha_nac_raw)

            # ── Línea 3 – Nombres y apellidos
            # Formato: APELLIDO1<<APELLIDO2<<PRIMER_NOMBRE<SEGUNDO_NOMBRE
            nombres_part = l3.rstrip("<")
            partes = nombres_part.split("<<")

            primer_apellido  = partes[0].replace("<", " ").strip() if len(partes) > 0 else ""
            segundo_apellido = partes[1].replace("<", " ").strip() if len(partes) > 1 else ""
            nombres_raw      = partes[2].replace("<", " ").strip() if len(partes) > 2 else ""

            nombres_split  = nombres_raw.split(" ")
            primer_nombre  = nombres_split[0] if len(nombres_split) > 0 else ""
            segundo_nombre = nombres_split[1] if len(nombres_split) > 1 else ""

            cedula = {
                "TipoDocumento":    tipo_doc,
                "Numero":           numero_raw.lstrip("0") or numero_raw,
                "PrimerApellido":   primer_apellido,
                "SegundoApellido":  segundo_apellido,
                "PrimerNombre":     primer_nombre,
                "SegundoNombre":    segundo_nombre,
                "Sexo":             sexo,
                "FechaDeNacimiento": fecha_nac,
                "RH":               "",
                "Departamento":     "",
                "Ciudad":           "",
                "LugarNacimiento":  "",
                "Pais":             pais_emisor if pais_emisor else "COL",
            }

            print(f"Honeywell MRZ parseado → {cedula['Numero']} {cedula['PrimerNombre']} {cedula['PrimerApellido']}")

            ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
            self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
            return cedula

        except Exception as e:
            print(f"Honeywell error parseando MRZ: {e}")
            self.event.awake("NotificarError", [json.dumps("Error al interpretar MRZ")])
            return None

    def _mrz_fecha(self, aammdd: str) -> str:
        """
        Convierte fecha MRZ AAMMDD a AAAAMMDD.
        Asume que AA < 30 → 20AA, AA >= 30 → 19AA (ajustable).
        """
        try:
            if len(aammdd) != 6:
                return ""
            aa, mm, dd = aammdd[0:2], aammdd[2:4], aammdd[4:6]
            year = (2000 + int(aa)) if int(aa) < 30 else (1900 + int(aa))
            return f"{year}{mm}{dd}"
        except Exception:
            return aammdd



    def _procesar_cedula_pdf417(self, byte: bytearray) -> dict:
        """
        Procesa cédulas con PDF417 binario (cédula amarilla con hologramas).
        Este era el bloque 'else' original cuando prefix == 80.
        """
        cedula = {}

        if byte[32:34] == b"CE":
            # Cédula de Ciudadanía (PDF417)
            cedula["TipoDocumento"] = "2"
            b = 34
            cedula_byte = bytearray()
            while byte[b] < 0x3A and byte[b] > 0x2F:
                cedula_byte.append(byte[b])
                b += 1
            cedula["Numero"] = cedula_byte.decode("utf-8").replace("\0", "").lstrip("0")

            primer_apellido = bytearray(byte[i + 52] for i in range(30))
            cedula["PrimerApellido"] = self.replaces(primer_apellido)

            segundo_apellido = bytearray(byte[i + 82] for i in range(30))
            cedula["SegundoApellido"] = self.replaces(segundo_apellido)

            primer_nombre = bytearray()
            segundo_nombre = bytearray()
            b = 0
            while byte[b + 112] != 0x20:
                primer_nombre.append(byte[b + 112])
                b += 1
            while byte[b + 112] != 0:
                segundo_nombre.append(byte[b + 112])
                b += 1

            cedula["PrimerNombre"] = self.replaces(primer_nombre)
            cedula["SegundoNombre"] = self.replaces(segundo_nombre)
            cedula["Sexo"] = chr(byte[200])

            cedula["FechaDeNacimiento"] = bytearray(byte[i + 192] for i in range(8)).decode("utf-8")
            cedula["RH"] = bytearray(byte[i + 217] for i in range(2)).decode("utf-8")
            cedula["Pais"] = self.replaces(bytearray(byte[i + 220] for i in range(30)))

            dept = bytearray(byte[i + 160] for i in range(2)).decode("utf-8").replace("\0", "")
            city = bytearray(byte[i + 162] for i in range(3)).decode("utf-8").replace("\0", "")
            cedula["Departamento"] = dept
            cedula["Ciudad"] = city
            cedula["LugarNacimiento"] = dept + city

        elif byte[0] == ord("I"):
            # Tarjeta de Identidad
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

            cedula["PrimerApellido"] = self.replaces(bytearray(byte[i + tempOffset] for i in range(23)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 81] for i in range(23)))
            cedula["PrimerNombre"] = self.replaces(bytearray(byte[i + 104] for i in range(23)))
            cedula["SegundoNombre"] = self.replaces(bytearray(byte[i + 127] for i in range(23)))
            cedula["Sexo"] = chr(byte[152])
            cedula["FechaDeNacimiento"] = bytearray(byte[i + 153] for i in range(8)).decode("utf-8")
            cedula["RH"] = bytearray(byte[i + 167] for i in range(2)).decode("utf-8")
            cedula["Departamento"] = bytearray(byte[i + 161] for i in range(2)).decode("utf-8")
            cedula["Ciudad"] = bytearray(byte[i + 163] for i in range(3)).decode("utf-8")
            cedula["LugarNacimiento"] = cedula["Departamento"] + cedula["Ciudad"]
            cedula["Pais"] = "COL"

        elif byte[0] == ord("0") and byte[1] == ord("0") and byte[2] == ord("0"):
            # Cédula antigua
            cedula["TipoDocumento"] = "3"
            cedula_byte = bytearray()
            b = 0
            while byte[b] == ord("0"):
                b += 1
            while byte[b] < 0x3A and byte[b] > 0x2F:
                cedula_byte.append(byte[b])
                b += 1
            cedula["Numero"] = cedula_byte.decode("UTF-8")
            cedula["PrimerApellido"] = self.replaces(bytearray(byte[i + 31] for i in range(25)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 56] for i in range(25)))
            cedula["PrimerNombre"] = self.replaces(bytearray(byte[i + 81] for i in range(25)))
            cedula["SegundoNombre"] = ""
            cedula["Ciudad"] = ""
            cedula["Departamento"] = ""
            cedula["FechaDeNacimiento"] = ""
            cedula["RH"] = ""
            cedula["Pais"] = "COL"
            cedula["Sexo"] = ""
            cedula["LugarNacimiento"] = ""

        else:
            # Cédula formato alternativo
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
            cedula["Numero"] = cedula_byte.decode("utf-8")
            cedula["PrimerApellido"] = self.replaces(bytearray(byte[i + 58] for i in range(23)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 81] for i in range(23)))
            cedula["PrimerNombre"] = self.replaces(bytearray(byte[i + 104] for i in range(23)))
            cedula["SegundoNombre"] = self.replaces(bytearray(byte[i + 127] for i in range(23)))
            cedula["Sexo"] = chr(byte[151])
            cedula["FechaDeNacimiento"] = bytearray(byte[i + 152] for i in range(8)).decode("utf-8")
            cedula["RH"] = bytearray(byte[i + 166] for i in range(2)).decode("utf-8")
            cedula["Departamento"] = bytearray(byte[i + 160] for i in range(2)).decode("utf-8")
            cedula["Ciudad"] = bytearray(byte[i + 162] for i in range(3)).decode("utf-8")
            cedula["LugarNacimiento"] = cedula["Departamento"] + cedula["Ciudad"]
            cedula["Pais"] = "COL"
            print(f"Honeywell: cédula procesada: {cedula}")

        ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
        self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
        return cedula

    def _procesar_cedula_alternativa(self, byte: bytearray) -> dict:
        """
        Parsea cédulas cuya trama no empieza con 'P' (0x50) y no es MRZ.
        """
        try:
            cedula = {}
            cedula["TipoDocumento"] = "2"

            raw_numero = bytearray(byte[47:57]).decode("utf-8")
            if raw_numero[0] == "0":
                cedula["Numero"] = raw_numero.lstrip("0")
            else:
                cedula["Numero"] = raw_numero

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

            print(f"Honeywell: cédula alt. parseada → {cedula['Numero']} {cedula['PrimerNombre']} {cedula['PrimerApellido']}")

            ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")
            self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
            return cedula

        except Exception as e:
            print(f"Honeywell: error parseando cédula alternativa: {e}")
            self.event.awake("NotificarError", [json.dumps("Error al interpretar la cédula")])
            return None

   
    def replaces(self, byte):
        """Reemplaza caracteres no-UTF8 (ñ, etc.) en bytearray."""
        for i in range(len(byte)):
            if byte[i] == 0xD1:
                byte[i:] = "Ñ".encode("utf-8") + byte[i + 1:]
        string = byte.decode("utf-8")
        string = string.replace("\0", "").strip()
        if "?" in string:
            string = string.replace("?", "Ñ")
        return string

    def disconnect(self):
        """Detiene el hilo lector y cierra el puerto serial."""
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