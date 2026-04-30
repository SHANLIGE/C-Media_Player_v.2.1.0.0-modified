# Librerias de GUI
import sys
import importlib.util

from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# Otras librerias
import os
import logging
import json
import threading
import time
import platform

# --- Detección de arquitectura ---
arch = platform.machine()
is_arm = arch in ("aarch64", "arm64", "armv7l")


def _import_local(module_name, rel_path, base_dir):
    """Importa un módulo local usando ruta absoluta.
    Resuelve problemas de imports relativos en ARM64/Linaro."""
    full_path = os.path.join(base_dir, rel_path)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class Player(QMainWindow):
    """
    Clase principal de la aplicacion
    """
    def __init__(self, debug=False):
        """
        Clase principal de la aplicacion
        """
        super().__init__()

        # --- Import de MainFrame según modo ---
        base_dir = os.path.dirname(os.path.abspath(__file__))

        if debug:
            # En debug/ARM64 usamos import explícito por ruta para evitar
            # fallos de resolución de paquetes relativos en Linaro
            _mf_mod = _import_local(
                "AppFrames.MainFrame",
                os.path.join("AppFrames", "MainFrame.py"),
                base_dir
            )
            MainFrame = _mf_mod.MainFrame
        else:
            from .AppFrames.MainFrame import MainFrame

        self.flags = Qt.WindowFlags()
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)

        # Icono de la Aplicacion
        icon = QIcon()
        path = os.path.expanduser("~/.config/Ciel/C-Media_Player/Media/Logo-CMedia_lx.png")
        icon.addFile(path, QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        # Nombre de la Aplicacion
        QCoreApplication.setApplicationName("C-Media Player v2.0")

        self.screen_disconnected = False
        self._closing = False          # renombrado para no colisionar con QMainWindow.close()
        self.app = QApplication.instance()

        # Obtención de configuración
        self.sett = self.get_sett()
        ruta = self.sett["Ruta"]
        if ruta.startswith("$"):
            env_key   = ruta[1:ruta.find("/")]
            file_name = os.environ[env_key] + ruta[ruta.find("/"):]
        else:
            file_name = ruta
        self.screen_config = self.get_screen_config(file_name)

        # Ventana siempre visible (Top Most)
        if self.sett["SiempreVisible"]:
            self.flags |= Qt.WindowStaysOnTopHint

        # Mostrar Borde de la Ventana
        if not self.sett["MostrarBordeVentana"]:
            self.flags |= Qt.FramelessWindowHint

        self.setWindowFlags(self.flags)
        self.setGeometry(
            self.sett["LeftRequerido"],
            self.sett["TopRequerido"],
            self.sett["AnchoRequerido"],
            self.sett["AltoRequerido"]
        )

        # Hilo de monitoreo de pantallas
        self.thread = threading.Thread(target=self.print_screens, daemon=True)
        self.thread.start()

        # Creacion de las pantallas
        pantallas = {}
        for pantalla in self.screen_config["Pantallas"]:
            pantallas[pantalla["ScreenNumber"]] = MainFrame(pantalla["Controles"])
            if pantalla["ScreenNumber"] == 1:
                self.setWindowTitle(pantalla["TitleName"])

        self.setCentralWidget(pantallas[1])

        # Pantalla completa
        if self.sett["PantallaCompleta"]:
            self.showFullScreen()

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        """Evento de cierre de la aplicacion"""
        self._closing = True
        self.centralWidget().closeEvent()
        event.accept()

    def get_screen_config(self, ruta):
        """
        Obtiene la informacion de las pantallas y su configuracion
        :param ruta: str. Ruta donde se encuentra el archivo de configuracion
        :return: dic. Configuracion extraida del archivo json
        """
        try:
            with open(ruta, "r", encoding="utf-8-sig") as file:
                screen_config = json.load(file)
            return screen_config
        except Exception as e:
            logging.error(str(e))
            QMessageBox.warning(
                self, "Advertencia",
                "Ha ocurrido un problema con el archivo de las pantallas, "
                "seleccione uno válido desde la aplicación de configuración."
            )
            sys.exit(1)

    def get_sett(self):
        """
        Obtiene la informacion de configuracion de la aplicacion
        :return: dic. Configuracion extraida del archivo json
        """
        path = os.path.expanduser("~/.config/Ciel/C-Media_Player/configs/config.json")
        try:
            with open(path, "r") as file:
                sett = json.load(file)
            return sett
        except Exception as e:
            logging.error(str(e))
            QMessageBox.warning(
                self, "Advertencia",
                "Uno de los archivos de la aplicación no fue instalado correctamente. "
                "Por favor reinstale la aplicación"
            )
            sys.exit(1)

    def focus_changed(self):
        if self.sett["PantallaCompleta"]:
            if self.isActiveWindow():
                self.showFullScreen()
        if self.sett["SiempreVisible"]:
            self.centralWidget().focus_changed()
            QApplication.instance().setActiveWindow(self)

    def print_screens(self):
        """
        Hilo que monitorea la reconexión/desconexión de pantallas.
        El nombre de pantalla ':0.0' es específico de Linaro/X11 en ARM.
        """
        while not self._closing:
            screens = self.app.screens()
            if screens and screens[0].name() == ":0.0" and not self.screen_disconnected:
                self.screen_disconnected = True
                self.showNormal()
            elif self.screen_disconnected and screens and screens[0].name() != ":0.0":
                time.sleep(0.5)
                self.showFullScreen()
                self.screen_disconnected = False
            time.sleep(0.2)   # evita busy-wait que agota CPU en ARM de baja potencia
        
