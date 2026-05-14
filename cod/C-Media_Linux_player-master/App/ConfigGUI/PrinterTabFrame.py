import json
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *


import os

class PrinterTabFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.setEnabled(False)
        self.path = ""
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
        self.path_label = QLabel("Logo")
        self.mainLayout.addWidget(self.path_label, 0, 0, 1, 1)
        self.path_label.setFixedHeight(50)
        self.path_entry = QLineEdit(self.path)
        self.mainLayout.addWidget(self.path_entry, 0, 1, 1, 4)
        self.file_name_button = QPushButton("Cargar")
        self.file_name_button.clicked.connect(self.select_file)
        self.mainLayout.addWidget(self.file_name_button, 0, 5)
        self.file_name_button.setStyleSheet("background-color : rgb(88, 102, 108); padding: 6px; border-radius: 3px;color: white")

        #Fila2
        self.printers = ["UniversalPrinter"]
        self.printer_label = QLabel("Impresora")
        self.mainLayout.addWidget(self.printer_label, 1, 0, 1, 1)
        self.path_label.setFixedHeight(50)
        self.combo_box_printer = QComboBox()
        self.combo_box_printer.addItems(self.printers)
        self.combo_box_printer.setCurrentIndex(self.index)
        self.mainLayout.addWidget(self.combo_box_printer, 1, 1, 1, 5)
        self.combo_box_printer.setStyleSheet("color : black; background-color : white; selection-background-color: rgb(88, 102, 108);") 

        #Fila3
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_settings)
        self.mainLayout.addWidget(self.save_button, 2, 2, 1, 2) 
        self.save_button.setStyleSheet("QPushButton{background-color : rgb(88, 102, 108); padding: 6px; border-radius: 3px;color: white}   QPushButton::pressed{background-color : rgb(62, 72, 77); padding: 6px; border-radius: 3px;color: white}") # 58666c 

        #Imagen 
        img =  QLabel()
        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/Media/LOGO-CMedia.png"
        pixmap = QPixmap(path)
        img.setPixmap(pixmap)

        self.mainLayout.addWidget(img, 2, 5, 1, 1, Qt.AlignRight | Qt.AlignBottom)


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
                    if "Control.Impresion.dll" in controller["NombreArchivo"]:
                        self.setEnabled(True)
                        self.path = controller["ObjetoBase"]["RutaLogo"]["Path"]
                        self.index = controller["ObjetoBase"]["TipoImpresora"] 

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
                    if "Control.Impresion.dll" in settings["Pantallas"][pantalla]["Controles"][controller]["NombreArchivo"]:
                        settings["Pantallas"][pantalla]["Controles"][controller]["ObjetoBase"]["RutaLogo"]["Path"] = self.path_entry.text()
                        settings["Pantallas"][pantalla]["Controles"][controller]["ObjetoBase"]["TipoImpresora"] = self.combo_box_printer.currentIndex()
        
        with open(path, "w", encoding="utf-8-sig") as file:
            file.write(json.dumps(settings))

    def select_file(self):
        """
        Abre un cuadro de dialogo para la seleccion del archivo de configuracion ccmj y lo guarda en la variable
        """
        file_name = QFileDialog().getOpenFileName(self, "Seleccionar Archivo", filter="Config files (*bmp)")[0]
        if file_name != "":
            self.file_name = file_name
            self.path_entry.clear()
            self.path_entry.insert(file_name)
