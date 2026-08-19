import json
import pathlib #Libreria de control de directorios
from ..Connection.UsbConnection import UsbConnection #Libreria de conexion usb
from ..Connection.SerialConnection import SerialConnection #Libreria de conexion serial
import time #Libreria control de tiempo (hilo principal)
import math #Libreria de matematicas
import cv2 #Libreria de manipulacion de imagenes
from ...Event import Event


