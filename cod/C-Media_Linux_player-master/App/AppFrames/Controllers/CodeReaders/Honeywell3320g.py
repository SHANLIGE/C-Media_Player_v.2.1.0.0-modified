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
    Lector de código de barras / documentos Magellan en presentation mode
    conectado via puerto serial /dev/ttyACM0.
    Utiliza pyserial directamente para no interferir con la conexión
    de la impresora ni con JSBridge/WebViewFrame.
    :param device: dic. Datos del lector (opcional, se ignora el puerto si se pasa).
    """

    def __init__(self, device=None):
        self.device = device
        self.result = None
        self.reader = None          # serial.Serial
        self.thread = None
        self.killThread = False

        self.event = Event("Omnidireccional.Honeywell")

        self.connect()

        self.detalle = "Lector Honeywell /dev/ttyACM0 presentation mode"
      
    # Api publica
    def get_result(self):
        return self.result

    def get_event(self):
        return self.event

    def clear_result(self):
        self.result = None

    def clear_event(self):
        self.event.clear()

    #conexion y lectura

    def connect(self):
        """
        Abre el puerto /dev/ttyACM0 con pyserial e inicia el hilo lector.
        Usa los parámetros estándar del Honeywell en presentation mode:
        9600 baudios, 8N1, sin timeout (bloquea hasta recibir datos).
        """
        puerto = PUERTO_SERIAL
        if self.device and self.device.get("NombrePuerto "):
            # Si la config externa especifica otro puerto, respetarlo
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
                timeout=None,       #bloqueo hasta recibir presentation mode
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

    #recepción de datos

    def receiveData(self):
        """
        Lee bytes del puerto en un bucle continuo (presentation mode).
        Acumula hasta encontrar el sufijo configurado, luego procesa.
        """
        buffer = bytearray()

        while not self.killThread:
            try:
                byte = self.reader.read(1)
            except Exception as e:
                if self.killThread:
                    break
                print(f"Honeywell error lectura: {e}")
                self.event.awake("NotificarError", [json.dumps("Error al leer los datos")])
                break

            if not byte:
                continue

            buffer += byte

            # ¿Terminó la trama? (sufijo al final del buffer)
            if buffer.endswith(SUFIJO):
                # Quitar el sufijo antes de procesar
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
        Procesa documentos de identidad, QR o códigos de barras.
        prefix = primer byte de la trama; byte = resto de la trama (bytearray).
        """
        print(f"Honeywell: trama recibida, prefix={prefix}, bytes={list(byte)}")
        if prefix != 80:
            # Verificar si todos los bytes son imprimibles (QR / código de barras simple)
            # Si contiene bytes no imprimibles es una cédula con prefijo distinto a 'P'
            full = bytearray([prefix]) + bytearray(byte)
            all_printable = all(32 < elem < 127 for elem in full)
            if all_printable:
                try:
                    res = ""
                    for elem in byte:
                        if elem <= 32 or elem >= 126:
                            return
                        res += chr(elem)
                    result = res
                    self.event.awake("EstablecerCodigo", [json.dumps(result)])
                    return result
                except Exception:
                    return
            else:
                # Cédula con formato alternativo (prefix != 'P')
                # Usar byte directamente; el prefijo no forma parte del payload del documento
                return self._procesar_cedula_alternativa(byte)
        else:
            #cedula colombiana 
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
    
    #utilidades

    def _procesar_cedula_alternativa(self, byte):
        """
        Parsea cédulas cuya trama no empieza con 'P' (0x50).
        Offsets confirmados empíricamente del Honeywell 3320g (trama ~532 bytes):
          byte[47:57]   : número de cédula (10 dígitos ASCII)
          byte[57..79]  : primer apellido  (23 bytes, null-terminated)
          byte[80..102] : segundo apellido (23 bytes, null-terminated)
          byte[103..125]: primer nombre   (23 bytes, null-terminated)
          byte[126..148]: segundo nombre  (23 bytes, null-terminated) — pendiente confirmar
        Sexo, FechaDeNacimiento, RH, Departamento, Ciudad: pendientes de confirmar offsets.
        """
        try:
            cedula = {}
            cedula["TipoDocumento"] = "2"  # Cédula de Ciudadanía

            # Número: 10 dígitos en byte[47:57], justo antes del primer apellido.
            # Si empieza por '0' es cédula antigua de 8 dígitos → quitar ceros de relleno.
            # Si empieza por otro dígito es cédula moderna de 10 dígitos → conservar completo.
            raw_numero = bytearray(byte[47:57]).decode("utf-8")
            if raw_numero[0] == "0":
                cedula["Numero"] = raw_numero.lstrip("0")   # 8 dígitos
            else:
                cedula["Numero"] = raw_numero               # 10 dígitos

            # Apellidos y nombre — offsets confirmados
            cedula["PrimerApellido"]  = self.replaces(bytearray(byte[i + 57]  for i in range(23)))
            cedula["SegundoApellido"] = self.replaces(bytearray(byte[i + 80]  for i in range(23)))
            cedula["PrimerNombre"]    = self.replaces(bytearray(byte[i + 103] for i in range(23)))
            cedula["SegundoNombre"]   = self.replaces(bytearray(byte[i + 126] for i in range(23)))

            # Campos pendientes de confirmar offsets con más capturas
            cedula["Sexo"]              = ""
            cedula["FechaDeNacimiento"] = ""
            cedula["RH"]                = ""
            cedula["Departamento"]      = ""
            cedula["Ciudad"]            = ""
            cedula["LugarNacimiento"]   = ""
            cedula["Pais"]              = "COL"

            print(f"Honeywell: cédula parseada → {cedula['Numero']} {cedula['PrimerNombre']} {cedula['PrimerApellido']} {cedula['SegundoApellido']}")

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
