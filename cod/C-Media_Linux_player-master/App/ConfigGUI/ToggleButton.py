from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

class ToggleButton(QWidget):
    """
    Clase de botones de palanca
    :param boolVar: bool. Variable booleana con el valor inicial del boton
    """
    def __init__(self, boolVar):
        """
        Clase de botones de palanca
        :param boolVar: bool. Variable booleana con el valor inicial del boton
        """
        super().__init__()
        self.boolVar = boolVar

        #Set Layout
        self.mainLayout = QGridLayout()
        self.setLayout(self.mainLayout)
        
        #Creacion de botones
        self.on = QPushButton("On", self)
        self.on.clicked.connect(self.toggle)
        self.mainLayout.addWidget(self.on, 0,0)
        self.off = QPushButton("Off", self)
        self.off.clicked.connect(self.toggle)
        self.mainLayout.addWidget(self.off, 0,1)

        #Inicializacion del estado de los botones
        if self.boolVar:
            self.on.setEnabled(False)
            self.off.setEnabled(True)
        else:
            self.off.setEnabled(False)
            self.on.setEnabled(True)
            
    
    def get(self): 
        """
        Obtiene el estado del boton
        :return: bool. Estado del  boton
        """
        return self.boolVar

    def toggle(self):
        """
        Cambia el estado del boton
        """
        self.boolVar = not self.boolVar
        if self.on.isEnabled():
            self.on.setEnabled(False)
            self.off.setEnabled(True)
        else:
            self.off.setEnabled(False)
            self.on.setEnabled(True)