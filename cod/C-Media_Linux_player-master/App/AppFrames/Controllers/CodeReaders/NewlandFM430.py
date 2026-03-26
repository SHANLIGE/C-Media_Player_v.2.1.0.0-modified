import json
from ..Connection.SerialConnection import SerialConnection
import threading
import logging
from ...Event import Event

class BarCodeReader():
    """
    Clase de lector de codigo de barras NewlandFM430 con conexion mediante puerto serial.
    :param device: dic. Datos del lector.
    """
    def __init__(self, device=None):
        """
        Constructor de clase.
        :param device: dic. Datos del lector.
        """

        self.device = device
        self.result = None
        self.reader = None
        self.thread = None
        self.killThread = False

        self.event = Event("Omnidireccional.NewLand")

        self.connect()

        
        #Constructor
        self.detalle = "Manejo de puerto serial"

    def get_result(self):
        """
        Obtiene el resultado del lector.
        :return: resultado del lector.
        """
        return self.result

    def get_event(self):
        return self.event

    def connect(self):
        """
        Conecta el lector e inicia el hilo del lector.
        """
        try:
            if self.device:
                self.reader = SerialConnection(self.device["NombrePuerto"], parity=0, stopbits=1, baudrate=9600) #/dev/ttyACM0
            else:
                self.reader = SerialConnection("0C2E:0B6A", parity=0, stopbits=1, baudrate=9600) #/dev/ttyACM0
        except Exception as e:
            logging.error(str(e))
            return str(e)

        if(self.thread == None and self.reader.device):
            self.thread = threading.Thread(target=self.receiveData)
            self.thread.start()
        else:
            self.event.awake("NotificarError", [json.dumps("Lector No Encontrado")])
            self.reader = None
            
        
    def receiveData(self):
        """
        Recibe los datos provenientes del puerto y llama a la funcion que los procesa.
        """
        if self.reader.device:
            while not self.killThread:
                try:
                    b = self.reader.read() 
                except Exception as e:
                    self.event.awake("NotificarError", [json.dumps("Error al leer los datos")])
                    logging.error(str(e)) 
                if(self.killThread):
                    break
                byte = bytearray()
                byte+=b
                while (not self.killThread) and (b != b"\r" or byte[-1] != ord("\r")):
                    b = self.reader.read()
                    byte+=b
                try:
                    self.procesar_datos(byte[0], byte[1:-1])
                except Exception as e:
                    self.event.awake("NotificarError", [json.dumps("Error al interpretar la lectura")])
                    logging.error(str(e))
                    self.result = {
                        "error" : str(e), 
                        "byte" :list(byte[1:])
                        }
            

    def procesar_datos(self, prefix, byte):
        """
        Procesa los datos del lector Documentos de identidad, codigos QR o de barras y lo guarda en la variable resultado.
        En caso de error guarda en la variable un arreglo de enteros correspondientes a la lectura de bytes en hexadecimal.
        """
        if(prefix == 0x4F):
            cedula = {}
            cedula["TipoDocumento"] = "0"
            raw = bytearray(byte).decode("utf-8")
            ced = raw.split("\t")
            nombres = ced[3].split(" ")

            if(len(nombres) > 1):
                ced[5:] = ced[4:]
                ced[3:5] = nombres[:] 
            else:
                ced[5:] = ced[4:]
                ced[3] = nombres
                ced[4] = ""
            
            #Numero
            if("\0" in ced[0]):
                ced[0].replace("\0", "")
            if("O" in ced[0]):
                ced[0].replace("O", "0")
            if(ced[0][:2] == "00"):
                ced[0] = cedula[2:]
            cedula["Numero"] = ced[0]

            #Primer Apellido
            cedula["PrimerApellido"] = self.replaces(ced[1])

            #Segundo Apellido
            cedula["SegundoApellido"] = self.replaces(ced[2])

            #Primer Nombre
            cedula["PrimerNombre"] = self.replaces(ced[3])

            #Segundo Nombre
            cedula["SegundoNombre"] = self.replaces(ced[4])

            if(len(ced[5]) > 1):
                cedula["Sexo"] = ced[5][0]
                cedula["FechaDeNacimiento"] = ced[5][4:]
            elif (ced[5] == "0"):
                cedula["Sexo"] =ced[6][0]
                cedula["FechaDeNacimiento"] = ced[6]
            else:
                cedula["Sexo"] = ced[5]
                cedula["FechaDeNacimiento"] = ced[6]
            
            cedula["Pais"] = "COL"

            
        elif(prefix != 114):
            try:
                res = ""
                #print(byte)
                for elem in byte:
                    if elem <=32 or elem >= 126:
                        return
                    res += chr(elem)
                    
                result = res
                #print(result)
                self.event.awake("EstablecerCodigo", [json.dumps(result)])
                return result
            except:
                return
        else:
            cedula = {}
            if(byte[32:34] == b"CE"):
                cedula["TipoDocumento"] = "2"
                b=34
                cedula_byte = bytearray()
                while (byte[b] < 0x3A and byte[b] > 0x2F):
                    cedula_byte.append(byte[b])
                    b+=1
                cedula["Numero"] = cedula_byte.decode('utf-8').replace('\0', "").lstrip("0")
                primer_apellido = bytearray()
                for i in range(30):
                    primer_apellido.append(byte[i+52])
                cedula["PrimerApellido"] = self.replaces(primer_apellido)
                
                segundo_apellido = bytearray()
                for i in range(30):
                    segundo_apellido.append(byte[i+82])
                cedula["SegundoApellido"] = self.replaces(segundo_apellido)

                primer_nombre = bytearray()
                segundo_nombre = bytearray()
                b = 0
                while byte[b + 112] != 0x20:
                    primer_nombre.append(byte[b+112])
                    b+=1
                
                while byte[b + 112] != 0:
                    segundo_nombre.append(byte[b+112])
                    b+=1
                
                cedula["PrimerNombre"] = self.replaces(primer_nombre)

                cedula["SegundoNombre"] = self.replaces(segundo_nombre)
                
                cedula["Sexo"] = chr(byte[200])

                cumpleanos = bytearray()
                for i in range(8):
                    cumpleanos.append(byte[i+192])
                cedula["FechaDeNacimiento"] = cumpleanos.decode('utf-8')

                sangre = bytearray()
                for i in range(2):
                    sangre.append(byte[i+217])
                cedula["RH"] = sangre.decode('utf-8')

                pais = bytearray()
                for i in range(30):
                    pais.append(byte[i+220])

                cedula["Pais"] = self.replaces(pais)    


                department = bytearray()
                for i in range(2):
                    department.append(byte[i+160])
                
                cedula["Departamento"] = department.decode('utf-8')
                cedula["Departamento"] = cedula["Departamento"].replace("\0", "")

                city = bytearray() 
                for i in range(3):
                    city.append(byte[i+162])
                
                cedula["Ciudad"] = city.decode('utf-8')
                cedula["Ciudad"] = cedula["Ciudad"].replace("\0", "")
                
                cedula["LugarNacimiento"] = cedula["Departamento"] + cedula["Ciudad"]


            elif(byte[0] == ord("I")):
                cedula["TipoDocumento"] = "1"
                cedula_byte = bytearray()
                if(byte[48] == ord('0') and byte[49] == ord('0')):
                    b = 50
                    while byte[b] < 0x3A and byte[b] > 0x2F:
                        cedula_byte.append(byte[b])
                        b+=1
                else:
                    b = 48
                    while byte[b] <0x3A and byte[b] > 0x2F:
                        cedula_byte.append(byte[b])
                        b+=1
                    tempOffset = b
                cedula["Numero"] = cedula_byte.decode('utf-8')
                
                primer_apellido = bytearray()
                for i in range(23):
                    primer_apellido.append(byte[i+tempOffset])

                cedula["PrimerApellido"] = self.replaces(primer_apellido)

                segundo_apellido = bytearray()
                for i in range(23):
                    segundo_apellido.append(byte[i+81])

                cedula["SegundoApellido"] = self.replaces(segundo_apellido)

                primer_nombre = bytearray()
                for i in range(23):
                    primer_nombre.append(byte[i+104])

                cedula["PrimerNombre"] = self.replaces(primer_nombre)
                
                segundo_nombre = bytearray()
                for i in range(23):
                    segundo_nombre.append(byte[i+127])
                
                cedula["SegundoNombre"] = self.replaces(segundo_nombre)
                
                cedula["Sexo"] = chr(byte[152])

                cumpleanos = bytearray()
                for i in range(8):
                    cumpleanos.append(byte[i+153])

                cedula["FechaDeNacimiento"] = cumpleanos.decode('utf-8')

                sangre = bytearray()
                for i in range(2):
                    sangre.append(byte[i+167])
                
                cedula["RH"] = sangre.decode('utf-8')

                department = bytearray()
                for i in range(2):
                    department.append(byte[i+161])

                cedula["Departamento"] = department.decode('utf-8')

                city = bytearray()
                for i in range(3):
                    city.append(byte[i+163])

                cedula["Ciudad"] = city.decode('utf-8')

                cedula["LugarNacimiento"] = cedula["Departamento"] + cedula["Ciudad"]

                cedula["Pais"] = "COL"

            elif (byte[0]== ord("0") and byte[1]== ord("0") and  byte[2] == ord("0")):
                cedula["TipoDocumento"] = "3"
                cedula_byte = bytearray()
                b = 0
                while byte[b] == ord("0"):
                    b+=1
                while byte[b] < 0x3A and byte[b] > 0x2F:
                    cedula_byte.append(byte[b])
                    b+=1

                cedula["Numero"] = cedula_byte.decode("UTF-8")

                primer_apellido = bytearray()
                for i in range(25):
                    primer_apellido.append(byte[i+31])

                cedula["PrimerApellido"] = self.replaces(primer_apellido)

                segundo_apellido = bytearray()
                for i in range(25):
                    segundo_apellido.append(byte[i+56])

                cedula["SegundoApellido"] = self.replaces(segundo_apellido)

                primer_nombre = bytearray()
                for i in range(25):
                    primer_nombre.append(byte[i+81])

                cedula["PrimerNombre"] = self.replaces(primer_nombre)
                
                cedula["SegundoNombre"] = ""

                cedula["Ciudad"] = ""
                cedula["Departamento"] = ""
                cedula["FechaDeNacimiento"] = ""
                cedula["RH"] = ""
                cedula["Pais"] = "COL"
                cedula["Sexo"] = ""
                cedula["LugarNacimiento"] = ""
            else:
                cedula["TipoDocumento"] = "0"
                cedula_byte = bytearray()
                if(byte[48] == ord('0') and byte[49] == ord('0')):
                    b = 50
                    while byte[b] < 0x3A and byte[b] > 0x2F:
                        cedula_byte.append(byte[b])
                        b+=1
                else:
                    b = 48
                    while byte[b] <0x3A and byte[b] > 0x2F:
                        cedula_byte.append(byte[b])
                        b+=1
                cedula["Numero"] = cedula_byte.decode('utf-8')
                
                primer_apellido = bytearray()
                for i in range(23):
                    primer_apellido.append(byte[i+58])

                cedula["PrimerApellido"] = self.replaces(primer_apellido)

                segundo_apellido = bytearray()
                for i in range(23):
                    segundo_apellido.append(byte[i+81])

                cedula["SegundoApellido"] = self.replaces(segundo_apellido)

                primer_nombre = bytearray()
                for i in range(23):
                    primer_nombre.append(byte[i+104])

                cedula["PrimerNombre"] = self.replaces(primer_nombre)
                
                segundo_nombre = bytearray()
                for i in range(23):
                    segundo_nombre.append(byte[i+127])
                
                cedula["SegundoNombre"] = self.replaces(segundo_nombre)
                
                cedula["Sexo"] = chr(byte[151])

                cumpleanos = bytearray()
                for i in range(8):
                    cumpleanos.append(byte[i+152])

                cedula["FechaDeNacimiento"] = cumpleanos.decode('utf-8')

                sangre = bytearray()
                for i in range(2):
                    sangre.append(byte[i+166])
                
                cedula["RH"] = sangre.decode('utf-8')

                department = bytearray()
                for i in range(2):
                    department.append(byte[i+160])

                cedula["Departamento"] = department.decode('utf-8')

                city = bytearray()
                for i in range(3):
                    city.append(byte[i+162])

                cedula["Ciudad"] = city.decode('utf-8')

                cedula["LugarNacimiento"] = cedula["Departamento"] + cedula["Ciudad"]

                cedula["Pais"] = "COL"
            ret = json.dumps(cedula).replace("{", "$#$").replace("}", "#$#").replace(",", "%#")           
            self.event.awake("EstablecerJsonDocumento", [json.dumps(ret)])
            return cedula
        

    def replaces(self, byte):
        """
        Reemplaza caracteres en otros formatos a utf-8.
        :param byte: bytearray. Datos con caracteres a reemplazar.
        :return: Datos con caracteres cambiados.
        """
        
        for i in range(len(byte)):
            if byte[i] == 0xd1: 
                byte[i:]='Ñ'.encode("utf-8")+byte[i+1:]
        string = byte.decode("utf-8")
        if "\0" in string:
            string = string.replace("\0", "")
        elif " " in string:
            string = string.replace(" ", "")
        if "?" in string:
            string = string.replace("?", "Ñ")
        return string

    def disconnect (self):

        """
        Desconecta el lector y destruye el hilo
        """
        
        self.killThread = True
        if self.reader:
            self.reader.device.cancel_read()
        if self.thread:
            self.thread.join()
        
    def clear_result(self):
        """
        Limpia el resultado de la clase
        """
        self.result = None

    def clear_event(self):
        self.event.clear()
