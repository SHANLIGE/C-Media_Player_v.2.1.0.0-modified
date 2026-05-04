+++++++++# Librerias de GUI - PySide6
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# Otras librerias
import sys
import logging
import os
from PySide6.QtPrintSupport import QPrinterInfo

def debug_printers():
    print("IMPRESORAS DISPONIBLES:")
    print(QPrinterInfo.availablePrinters())
    
argv = sys.argv
debug = "--debug" in sys.argv

#arquitectura aarch64 arm linaro
import platform
arch = platform.machine()
is_arm = arch in ("aarch64", "arm64", "armv7l")

if debug:
    #desarrollo
    import importlib.util

    def _import_local(module_name, rel_path):
        """Importa un módulo local usando su ruta relativa al script actual.
        Esto resuelve problemas de resolución de imports en ARM64/Linaro."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, rel_path)
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod

    _cfg_mod = _import_local("ConfigGUI.MainFrame",
                             os.path.join("ConfigGUI", "MainFrame.py"))
    Configuration = _cfg_mod.MainFrame

    _player_mod = _import_local("Player",
                                os.path.join("Player.py"))
    Player = _player_mod.Player

else:
    #compilado
    from App.ConfigGUI.MainFrame import MainFrame as Configuration
    from App.Player import Player as Player


#config logs
CONFIG_DIR = os.path.expanduser("~/.config/Ciel/C-Media_Player")
LOG_DIR    = os.path.join(CONFIG_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)   # Crea el directorio si no existe (necesario en Linaro fresh install)

#creacion de logs
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "log.log"),
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p"
)

if is_arm:
    logging.info(f"Iniciando en arquitectura ARM: {arch}")

# Descomentarear la siguiente línea para activar depuración remota (chrome://inspect)
# os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

#flags de Chromium compatibles con arm64
chromium_flags = "--disable-pinch"
if is_arm:
    #desabilidar aceleracion gpu y qtwebengine sandbox
    chromium_flags += " --disable-gpu --no-sandbox --disable-dev-shm-usage"

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = chromium_flags

#compatibilidad
if is_arm:
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")

# Creación de la aplicación
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
root = QApplication(argv)   # <-- pasar argv limpio (sin --debug) a QApplication
QCoreApplication.setApplicationName("C-Media Player Lx")

# Eliminar --debug del argv antes de pasarlo a Qt
if "--debug" in argv:
    argv.remove("--debug")

# Creación del SplashScreen
splash_path = os.path.join(CONFIG_DIR, "Media", "SplashScreen.png")
pixmap = QPixmap(splash_path)
splash = QSplashScreen(pixmap)
splash.show()
root.processEvents()

# Iniciación
if len(argv) == 1:
    try:
        player = Player(debug)
        splash.finish(player)
        player.show()

        #imprimir ticket Nulo
        try:
            from printer_test import UniversalESCPrinter
            _p = UniversalESCPrinter(port="/dev/ttyUSB0", baudrate=9600)
            _p.print(["NULL"])
            _p.close()
        except Exception as e:
            logging.warning("Impresión de prueba fallida: " + str(e))


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
