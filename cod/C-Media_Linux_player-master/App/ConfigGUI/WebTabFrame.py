from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

#Clases Externas
from .ToggleButton import ToggleButton

#Otras librerías
import json
import os
import copy
import logging


# ---------------------------------------------------------------------------
# Paleta de colores
# ---------------------------------------------------------------------------
COLOR_NARANJA = "#f99f04"
COLOR_NARANJA_HOVER = "#ff8c00"
COLOR_NARANJA_PRESSED = "#f99f04"
COLOR_ROJO = "#d9534f"
COLOR_ROJO_HOVER = "#c9302c"
COLOR_FONDO = "#FFFFFF"
COLOR_INPUT_BG = "#F2F4F6"
COLOR_BORDE = "#E4E6E9"
COLOR_TEXTO = "#313336"
COLOR_TEXTO_SUAVE = "#5B6066"
COLOR_BACKGROUND = "#F2F4F6"
COLOR_SCROLLBAR_BG = "#D0D0D3"

# Nombre del archivo del control web dentro del JSON de pantallas
CONTROL_WEB = "Control.NavegadorWebChrome.dll"

# Llave que se agrega a cada pantalla para recordar en que monitor va
LLAVE_MONITOR = "MonitorAsignado"


class WebTabFrame(QWidget):
    def __init__(self):
        super().__init__()

        self._terminal_tab = terminal_tab
        self.setEnabled(False)
        self.url = ""
        self.nav_bar = False
        self.filas_url = []       # [{"widget","check","entry","combo","indice"}, ...]
        self.get_settings()

        
        

        #Seleccionar el fondo
        bg = QPalette()
        bg.setColor(QPalette.Window, "#dae7ef") #AR
        self.setAutoFillBackground(True)
        self.setPalette(bg)

        #Configuracion del Layout
        self.mainLayout = QGridLayout()
        self.setLayout(self.mainLayout)

        #Fila1
        self.url_label = QLabel("Url")
        self.mainLayout.addWidget(self.url_label, 0, 0, 1, 1)
        self.url_label.setFixedHeight(50)
        self.url_entry = QLineEdit(self.url)
        self.mainLayout.addWidget(self.url_entry, 0, 1, 1, 5)

        #Fila2
        self.nav_bar_label = QLabel("Barra de Navegación")
        self.nav_bar_label.setFixedHeight(50)   
        self.mainLayout.addWidget(self.nav_bar_label, 1, 0, 1, 2)
        #self.nav_bar_button = ToggleButton(self.nav_bar)
        self.nav_bar_button = QCheckBox(self)
        self.nav_bar_button.setChecked(self.nav_bar)
        #self.nav_bar_button.toggled.connect(self.funcionnb) # CAMBIAR FUNCION
        self.mainLayout.addWidget(self.nav_bar_button, 1, 2)

        #Fila3
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_settings)
        self.mainLayout.addWidget(self.save_button, 3, 2, 1, 2)
        self.save_button.setStyleSheet("QPushButton{background-color : rgb(88, 102, 108); padding: 6px; border-radius: 3px;color: white}   QPushButton::pressed{background-color : rgb(62, 72, 77); padding: 6px; border-radius: 3px;color: white}") # 58666c 

        #Imagen 
        img =  QLabel()
        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/Media/LOGO-CMedia.png"
        pixmap = QPixmap(path)
        img.setPixmap(pixmap)

        self.mainLayout.addWidget(img, 3, 5, 1, 1, Qt.AlignRight | Qt.AlignBottom)

    def get_settings(self):
        """
        Obtiene la configuracion del archivo json y las guarda en un atributo de la clase
        """

        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/configs/config.json"
        with open(path, "r") as file:
            settings = json.loads(file.read())
        if "$" == settings["Ruta"][0]:
            var =  os.environ[settings["Ruta"][1:settings["Ruta"].find("/")]]
            path = var + settings["Ruta"][settings["Ruta"].find("/"):]
        else:
            path = settings["Ruta"]
        with open(path, "r", encoding="utf-8-sig") as file:
            settings = json.load(file)
            for pantalla in settings["Pantallas"]:
                for controller in pantalla["Controles"]:
                    if "Control.NavegadorWebChrome.dll" in controller["NombreArchivo"]:
                        self.setEnabled(True)
                        self.url = controller["ObjetoBase"]["UrlInicio"]
                        self.nav_bar = controller["ObjetoBase"]["MostrarBarraNavegacion"]

    def save_settings(self):
        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/configs/config.json"
        with open(path, "r") as file:
            settings = json.loads(file.read())

        if "$" == settings["Ruta"][0]:
            var =  os.environ[settings["Ruta"][1:settings["Ruta"].find("/")]]
            path = var + settings["Ruta"][settings["Ruta"].find("/"):]
        else:
            path = settings["Ruta"]
        with open(path, "r", encoding="utf-8-sig") as file:
            settings = json.load(file)
            for pantalla in range(len(settings["Pantallas"])):
                for controller in range(len(settings["Pantallas"][pantalla]["Controles"])):
                    if "Control.NavegadorWebChrome.dll" in settings["Pantallas"][pantalla]["Controles"][controller]["NombreArchivo"]:
                        settings["Pantallas"][pantalla]["Controles"][controller]["ObjetoBase"]["UrlInicio"] = self.url_entry.text()
                        settings["Pantallas"][pantalla]["Controles"][controller]["ObjetoBase"]["MostrarBarraNavegacion"] = self.nav_bar_button.isChecked()
        
        with open(path, "w", encoding="utf-8-sig") as file:
            file.write(json.dumps(settings))



   