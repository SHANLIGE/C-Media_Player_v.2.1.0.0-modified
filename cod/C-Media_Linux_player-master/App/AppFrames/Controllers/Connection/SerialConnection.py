
import serial
import serial.tools.list_ports
import logging

class SerialConnection():
    """
    Clase para conexión a dispositivos por puerto serial.
    """
    def __init__(self, port, timeout=2, baudrate=9600, bytesize=8, parity='N', stopbits=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        # Convierte a valores pyserial
        self.bytesize = {
            5: serial.FIVEBITS,
            6: serial.SIXBITS,
            7: serial.SEVENBITS,
            8: serial.EIGHTBITS
        }.get(bytesize, serial.EIGHTBITS)

        self.parity = {
            'N': serial.PARITY_NONE,
            'E': serial.PARITY_EVEN,
            'O': serial.PARITY_ODD,
            'M': serial.PARITY_MARK,
            'S': serial.PARITY_SPACE
        }.get(parity, serial.PARITY_NONE)

        self.stopbits = {
            1: serial.STOPBITS_ONE,
            1.5: serial.STOPBITS_ONE_POINT_FIVE,
            2: serial.STOPBITS_TWO
        }.get(stopbits, serial.STOPBITS_ONE)

        self.device = None

        self.connect()

    def connect(self):
        try:
            if "/dev/" not in self.port:
                # Buscar puerto por hwid
                ports = serial.tools.list_ports.comports()
                for port, desc, hwid in sorted(ports):
                    if self.port in hwid:
                        self.port = port
            self.device = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            print("Serial conectado correctamente:", self.device)
        except Exception as e:
            self.device = None
            logging.error("Error abriendo serial: " + str(e))
            print("Error abriendo serial:", e)

    def write(self, data):
        if self.device:
            try:
                self.device.write(data)
            except Exception as e:
                logging.error(str(e))
                print("Error escribiendo:", e)

    def read(self):
        if self.device:
            try:
                return self.device.read()
            except Exception as e:
                logging.error(str(e))
                return None

    def readline(self):
        if self.device:
            try:
                return self.device.readline()
            except Exception as e:
                logging.error(str(e))
                return None

    def disconnect(self):
        if self.device:
            try:
                self.device.close()
                self.device = None
            except Exception as e:
                logging.error(str(e))

"""import serial #libreria que permite la conexion con puerto serial
import logging #libreria de logging
from serial.serialutil import PARITY_NAMES #Libreria con los nombres de paridad
import serial.tools.list_ports

class SerialConnection():
   
    def __init__(self, port, timeout = 2000, baudrate = 9600, bytesize=8, parity=0,stopbits = 1 ):
        
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = list(PARITY_NAMES.keys())[parity] 
        self.stopbits = stopbits
        self.timeout = timeout

        self.device = None

        self.connect()



    def connect(self):
        
        try:
            if "/dev/" not in self.port:
                ports = serial.tools.list_ports.comports()
                for port, desc, hwid in sorted(ports):
                    if self.port in hwid:
                        self.port = port
            self.device = serial.Serial(port=self.port, baudrate=self.baudrate, bytesize=self.bytesize, parity=self.parity, stopbits=self.stopbits, timeout=self.timeout)
        except Exception as e:
            self.device = None
            logging.error(str(e))
            #raise str(e)

    def write(self, data):
        
        if self.device:
            try:
                self.device.write(data)
            except Exception as e:
                logging.error(str(e))
                return str(e)

    def read(self):
        
        if self.device:
            try:
                return self.device.read()
            except Exception as e:
                logging.error(str(e))
                return str(e)

    def read_line(self):
        
        if self.device:
            try:
                return self.device.readline()
            except Exception as e:
                logging.error(str(e))
                return str(e)

    def diconnect(self):
       
        if self.device:
            try:
                self.device.close()
            except Exception as e:
                logging.error(str(e))
                return str(e)
"""