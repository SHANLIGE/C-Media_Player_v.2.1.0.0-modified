from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

from .CodeReaderTabFrame import CodeReaderTabFrame
from .GeneralTabFrame import GeneralTabFrame
from .WebTabFrame import WebTabFrame
from .PrinterTabFrame import PrinterTabFrame
import os

class MainFrame(QWidget):
    """
    Clase de pantalla principal (configuracion)
    """
    def __init__(self):
        """
        Constructor de clase
        """
        super().__init__()
        icon = QIcon()
        path = os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/Media/Logo-CMedia_C.png"
        icon.addFile(path, QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)
        #Nombre de la Aplicacion
        self.setWindowTitle("C-Media Player Lx - Configuración")
        self.setMinimumSize(800, 500)
        self.setMaximumSize(800, 500)
        QCoreApplication.setApplicationName("C-Media Player Lx - Configuration")
        #Background
        bg = QPalette()
        bg.setColor(QPalette.Window, "#dae7ef") #AR
        self.setAutoFillBackground(True)
        self.setPalette(bg)
        
        #Set Layout
        self.mainLayout = QGridLayout()
        self.mainLayout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(self.mainLayout)

        #TabFrame
        self.tabWidget = QTabWidget(self)
        self.generalTab = GeneralTabFrame()
        self.webTab = WebTabFrame()
        self.printerTab = PrinterTabFrame()
        self.readerTab = CodeReaderTabFrame()
        self.tabWidget.addTab(self.generalTab, "General")
        self.tabWidget.addTab(self.webTab, "Contenedor Web")
        self.tabWidget.addTab(self.printerTab, "Impresora")
        self.tabWidget.addTab(self.readerTab, "Lector")
        self.mainLayout.addWidget(self.tabWidget)
        
        palette = QPalette() # PANTONE
        palette.setColor(QPalette.Window, "#ffffff") 
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.AlternateBase, QColor(218, 231, 239))
        palette.setColor(QPalette.ToolTipBase, Qt.black)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, "#58666c")
        palette.setColor(QPalette.Button, "#ffffff")
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, "#2a82da")
        palette.setColor(QPalette.Highlight, "#2a82da")
        palette.setColor(QPalette.HighlightedText, Qt.black)
        palette.setColor(QPalette.Disabled, QPalette.Base, QColor(44, 44, 45)) 
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(88, 102, 108))
        palette.setColor(QPalette.Disabled, QPalette.Button, QColor(193, 196, 199))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(88, 89, 91))
        #palette.setColor(QPalette.Disabled, QPalette.Window, QColor(49, 49, 49))
        #palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(57, 57, 57))
        self.setPalette(palette)