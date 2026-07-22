#Librerias de GUI
import sys

from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
#Otras librerias
import os
import logging
import json
import threading
import time

class Player(QMainWindow):
    """
    Clase principal de la aplicacion
    """
    def __init__(self, debug = False):
        """
        Clase principal de la aplicacion
        """ 
        if debug:
            from AppFrames.MainFrame import MainFrame
        else:
            from .AppFrames.MainFrame import MainFrame
        super().__init__()
        self.flags = Qt.WindowFlags()
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        #Icono de la Aplicacion
        icon = QIcon()
        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/Media/Logo-CMedia_lx.png"
        icon.addFile(path, QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        #Nombre de la Aplicacion
        QCoreApplication.setApplicationName("C-Media Player v2.2")

        self.screen_disconnected = False
        self.close = False
        self.app = QApplication.instance() 

        #Obtencion de configuracion
        self.sett = self.get_sett()
        if "$" == self.sett["Ruta"][0]:
            var =  os.environ[self.sett["Ruta"][1:self.sett["Ruta"].find("/")]]
            file_name = var + self.sett["Ruta"][self.sett["Ruta"].find("/"):]
        else:
            file_name = self.sett["Ruta"]
        self.screen_config = self.get_screen_config(file_name)
        
        #Ventana siempre visible (Top Most)
        if self.sett["SiempreVisible"]:
            self.flags |= Qt.WindowStaysOnTopHint
        

        #Mostrar Borde de la Ventana
        if not(self.sett["MostrarBordeVentana"]):
            self.flags |= Qt.FramelessWindowHint
        
        self.setWindowFlags(self.flags)
        
        self.setGeometry(self.sett["LeftRequerido"],self.sett["TopRequerido"] , self.sett["AnchoRequerido"], self.sett["AltoRequerido"])        
        self.thread = threading.Thread(target=self.print_screens)
        self.thread.start()
	
        #Creacion de las pantallas
        pantallas = {}
        for pantalla in self.screen_config["Pantallas"]:
            pantallas[pantalla["ScreenNumber"]] = MainFrame(pantalla["Controles"])
            if(pantalla["ScreenNumber"]==1):
                self.setWindowTitle(pantalla["TitleName"])

        #setCentralWidget
        self.setCentralWidget(pantallas[1])

        # Poner la ventana en pantalla completa
        if self.sett["PantallaCompleta"]:
            #print("Pantalla Completa")
            self.showFullScreen()


    def closeEvent(self, event):
        """
        Evento de cierre de la aplicacion
        """
        self.close = True
        self.centralWidget().closeEvent()
        event.accept()

    def get_screen_config(self, ruta):
        """
        Obtiene la informacion de las pantallas y su configuracion
        :param ruta: str. Ruta donde se encuentra el archivo de configuracion
        :return: dic. Configuracion extraida del archivo json
        """
        try:
            with open(ruta, 'r', encoding="utf-8-sig") as file:
                screen_config = json.load(file)
            return screen_config
        except Exception as e:
            logging.error(str(e))
            QMessageBox.warning(self, "Advertencia", "Ha ocurrido un problema con el archivo de las pantallas, seleccione uno válido desde la aplicación de configuración.")    
            sys.exit()

    def get_sett(self):
        """
        Obtiene la informacion de configuracion de la aplicacion
        :return: dic. Configuracion extraida del archivo json
        """
        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/configs/config.json"
        try:
            with open(path, "r") as file:
                sett = json.load(file)
            return sett
        except Exception as e:
            logging.error(str(e))
            QMessageBox.warning(self, "Advertencia", "Uno de los archivos de la aplicacción no fue instalado correctamente. Por favor reinstale la aplicación")
            sys.exit()

    

        
    def focus_changed(self):
        if self.sett["PantallaCompleta"]:
            if self.isActiveWindow():
                self.showFullScreen()
        if self.sett["SiempreVisible"]:
            self.centralWidget().focus_changed()
            qApp.setActiveWindow(self)
            
    def print_screens(self):
        while not self.close:
            if self.app.screens()[0].name() == ":0.0" and not self.screen_disconnected:
                self.screen_disconnected = True
                self.showNormal()
                
            elif self.screen_disconnected and self.app.screens()[0].name() != ":0.0":
                time.sleep(0.5)
                self.showFullScreen()
                self.screen_disconnected = False
        
