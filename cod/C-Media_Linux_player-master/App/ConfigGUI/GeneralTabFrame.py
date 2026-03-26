#Librerias de GUI
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

#Clases Externas
#from .ToggleButton import ToggleButton

#Otras librerias
import os
import json

class GeneralTabFrame(QWidget):
    """
    Clase de vista de configuracion General
    """ 
    def __init__(self):
        """
        Clase de vista de configuracion General
        """ 
        super().__init__()
        self.settings = {}
        self.get_settings()

        #Iniciacion de variables
        
        if "$" == self.settings["Ruta"][0]:
            var =  os.environ[self.settings["Ruta"][1:self.settings["Ruta"].find("/")]]
            file_name = var + self.settings["Ruta"][self.settings["Ruta"].find("/"):]
            self.file_name = file_name
        else:
            self.file_name = self.settings["Ruta"]
        self.fullscreen = self.settings["PantallaCompleta"]
        self.window_border = self.settings["MostrarBordeVentana"]
        self.on_top = self.settings["SiempreVisible"]
        self.w = self.settings["AnchoRequerido"]
        self.h = self.settings["AltoRequerido"]
        self.t = self.settings["TopRequerido"]
        self.l = self.settings["LeftRequerido"]

        #Seleccionar el fondo
        bg = QPalette()
        bg.setColor(QPalette.Window, "#dae7ef") #AR
        self.setAutoFillBackground(True)
        self.setPalette(bg)

        #Configuracion del Layout
        self.mainLayout = QGridLayout()
        self.setLayout(self.mainLayout)
        
        #Fila1
        self.mainLayout.addWidget(QLabel("Archivo de recursos"), 0, 0, 1, 2)
        self.file_name_entry =  QLineEdit(self.file_name)
        self.file_name_entry.setReadOnly(True)
        self.mainLayout.addWidget(self.file_name_entry, 0, 2, 1, 6)
        self.file_name_button = QPushButton("Cargar")
        self.file_name_button.clicked.connect(self.select_file)
        self.mainLayout.addWidget(self.file_name_button, 0, 8)
        self.file_name_button.setStyleSheet("background-color : rgb(88, 102, 108); padding: 6px; border-radius: 3px;color: white")
        #self.file_name_button.setMaximumWidth(25) 

        #Fila2 Columna1-2
        self.mainLayout.addWidget(QLabel("Pantalla completa"), 1, 0, 1, 2)
        #self.fullscreen_button = ToggleButton(self.fullscreen)
        self.fullscreen_button = QCheckBox(self)
        self.fullscreen_button.setChecked(self.fullscreen)
        #self.fullscreen_button.toggled.connect(self.funcionfs) # CAMBIAR FUNCION
        self.mainLayout.addWidget(self.fullscreen_button, 1, 2)

        #Fila2 Columna 3-4
        self.mainLayout.addWidget(QLabel("Borde Ventana"), 1, 3, 1, 2)
        #self.window_border_button = ToggleButton(self.window_border)
        self.window_border_button = QCheckBox(self)
        self.window_border_button.setChecked(self.window_border)
        #self.window_border_button.toggled.connect(self.funcionwb) # CAMBIAR FUNCION
        self.mainLayout.addWidget(self.window_border_button, 1, 5)
        
        #Fila2Columna 5-6
        self.mainLayout.addWidget(QLabel("Siempre Visible"), 1, 6, 1, 2)
        #self.on_top_button = ToggleButton(self.on_top)
        self.on_top_button = QCheckBox(self)
        self.on_top_button.setChecked(self.on_top)
        #self.on_top_button.toggled.connect(self.funcionot) # CAMBIAR FUNCION
        self.mainLayout.addWidget(self.on_top_button, 1, 8)

        #Fila5
        self.mainLayout.addWidget(QLabel("Ancho pxls"), 2, 0, alignment= Qt.AlignRight)
        self.width_entry = QLineEdit(str(self.w))
        self.mainLayout.addWidget(self.width_entry, 2, 1, alignment= Qt.AlignLeft)
        self.width_entry.setMaximumWidth(50) 

        self.mainLayout.addWidget(QLabel("Alto pxls"), 3, 0, alignment= Qt.AlignRight)
        self.height_entry = QLineEdit(str(self.h))
        self.mainLayout.addWidget(self.height_entry, 3, 1, alignment= Qt.AlignLeft)
        self.height_entry.setMaximumWidth(50) 

        self.mainLayout.addWidget(QLabel("Superior"), 2, 3, alignment= Qt.AlignRight)
        self.top_entry = QLineEdit(str(self.t))
        self.mainLayout.addWidget(self.top_entry, 2, 4, alignment= Qt.AlignLeft)
        self.top_entry.setMaximumWidth(50) 

        self.mainLayout.addWidget(QLabel("Izquierda"), 3, 3, alignment= Qt.AlignRight)
        self.left_entry = QLineEdit(str(self.l))
        self.mainLayout.addWidget(self.left_entry, 3, 4, alignment= Qt.AlignLeft)
        self.left_entry.setMaximumWidth(50) 

        #Fila6
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save)
        self.mainLayout.addWidget(self.save_button, 4, 3, 1, 3) 
        self.save_button.setStyleSheet("QPushButton{background-color : rgb(88, 102, 108); padding: 6px; border-radius: 3px;color: white}   QPushButton::pressed{background-color : rgb(62, 72, 77); padding: 6px; border-radius: 3px;color: white}") # 58666c 
        #self.save_button.setStyleSheet(    border-style: outset;)

        #Imagen
        img =  QLabel()
        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/Media/LOGO-CMedia.png"
        pixmap = QPixmap(path)
        img.setPixmap(pixmap)

        self.mainLayout.addWidget(img, 4, 8, 1, 1, Qt.AlignRight | Qt.AlignBottom)

    def select_file(self):
        """
        Abre un cuadro de dialogo para la seleccion del archivo de configuracion ccmj y lo guarda en la variable
        """
        file_name = QFileDialog().getOpenFileName(self, "Seleccionar Archivo", filter="Config files (*.ccmj)")[0]
        if file_name != "":
            self.file_name = file_name
            self.file_name_entry.clear()
            self.file_name_entry.insert(file_name)
            


    def save(self): 
        """
        Guarda la informacion en el archivo json de configuracion
        """

        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/configs/config.json"
        
        with open(path, "w") as file:
            
            settings = {
                "Ruta" : self.file_name,
                "PantallaCompleta" : self.fullscreen_button.isChecked(), 
                "SiempreVisible" : self.on_top_button.isChecked(),
                "MostrarBordeVentana" : self.window_border_button.isChecked(), 
                "AnchoRequerido" : int(self.width_entry.text()),
                "AltoRequerido" : int(self.height_entry.text()),
                "TopRequerido" : int(self.top_entry.text()),
                "LeftRequerido" : int(self.left_entry.text())
            }

            file.write(json.dumps(settings))

    def get_settings(self):
        """
        Obtiene la configuracion del archivo json y las guarda en un atributo de la clase
        """

        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/configs/config.json"
        with open(path, "r") as file:
            self.settings = json.loads(file.read())
