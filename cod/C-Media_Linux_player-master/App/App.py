# Librerias de GUI - PySide6
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# Otras librerias
import sys
import logging
import os

import traceback, sys

def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)

sys.excepthook = excepthook
    
argv = sys.argv
debug = "--debug" in sys.argv

#arquitectura aarch64 arm linaro
import platform
arch = platform.machine()
is_arm = arch in ("aarch64", "arm64", "armv7l")

if debug:
    #Clases internas - Pruebas 
    #Descomentar para realizar pruebas con python
    from ConfigGUI.MainFrame import MainFrame as Configuration
    from Player import Player as Player
    argv.remove("--debug")
else:
    #Clases internas - Compilación
    #Descomentar para realizar compilacion de la aplicacion
    from App.ConfigGUI.MainFrame import MainFrame as Configuration
    from App.Player import Player as Player



#Creacion del archivo de logs
logging.basicConfig(filename=os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/logs/log.log", level=logging.DEBUG, format=("%(asctime)s:%(levelname)s:%(message)s"), datefmt="%m/%d/%Y %I:%M:%S %p")

# Descomentarear la siguiente línea para activar depuración remota (chrome://inspect)
# os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

#Creacion aplicacion
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-pinch"
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
root = QApplication()
QCoreApplication.setApplicationName("C-Media Player Lx")
#Creacion del SplashScreen
pixmap = QPixmap(os.path.expanduser('~')+"/.config/Ciel/C-Media_Player/Media/SplashScreen.png")
splash = QSplashScreen(pixmap)
splash.show()
root.processEvents()

    
#Iniciacion
if len(argv) == 1:
    try:
        player = Player(debug)

        splash.finish(player)
        player.show()
    except Exception as e:
        logging.error(str(e))
        sys.exit(1)
elif "--config" in argv:
    try:
        config = Configuration()
        splash.finish(config)
        config.show()
    except Exception as e:
        logging.error(str(e))
        sys.exit(1)
else:
    logging.error("Opcion no permitida: %s", argv)
    sys.exit(1)

root.lastWindowClosed.connect(root.quit)

# Fin de la aplicación
sys.exit(root.exec())


