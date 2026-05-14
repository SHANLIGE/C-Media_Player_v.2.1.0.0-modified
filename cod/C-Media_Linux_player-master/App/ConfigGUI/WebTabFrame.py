from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from .TerminalTabFrame import TerminalTabFrame
from .ToggleButton import ToggleButton
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
    def __init__(self, terminal_tab: TerminalTabFrame = None):
        super().__init__()

        self._terminal_tab = terminal_tab
        self.setEnabled(False)
        self.url = ""
        self.url_terminal = ""
        self.nav_bar = False
        self.filas_url = []       # [{"widget","check","entry","combo","indice"}, ...]
        self.get_settings()

        # Fondo
        bg = QPalette()
        bg.setColor(QPalette.Window, "#dae7ef")
        self.setAutoFillBackground(True)
        self.setPalette(bg)

        # Layout
        self.mainLayout = QGridLayout()
        self.setLayout(self.mainLayout)

        # Fila 1 – URL Selector + toggle barra de navegacion
        self.url_label = QLabel("Url")
        self.url_label.setFixedHeight(50)
        self.mainLayout.addWidget(self.url_label, 0, 0, 1, 1)
        self.url_entry = QLineEdit(self.url)
        self.mainLayout.addWidget(self.url_entry, 0, 1, 1, 5)
     

        self.terminal_label = QLabel("Terminal")
        self.terminal_label.setFixedHeight(50)
        self.mainLayout.addWidget(self.terminal_label, 1, 0, 1, 1)
        self.url_entry_terminal = QLineEdit()
        self.mainLayout.addWidget(self.url_entry_terminal, 1, 1, 1, 5)
        self.url_entry_terminal.textChanged.connect(self._sync_terminal_url)
        # Asignar después de conectar → dispara _sync_terminal_url con la URL cargada
        if self.url_terminal:
            self.url_entry_terminal.setText(self.url_terminal)

        # Fila 2 – Barra de Navegación
        self.nav_bar_label = QLabel("Barra de Navegación")
        self.nav_bar_label.setFixedHeight(50)   
        self.mainLayout.addWidget(self.nav_bar_label, 2, 0, 1, 2)
        #self.nav_bar_button = ToggleButton(self.nav_bar)
        self.nav_bar_button = QCheckBox(self)
        self.nav_bar_button.setChecked(self.nav_bar)
        #self.nav_bar_button.toggled.connect(self.funcionnb) # CAMBIAR FUNCION
        self.mainLayout.addWidget(self.nav_bar_button, 2, 2)

        # Fila 3 – Guardar
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_settings)
        self.mainLayout.addWidget(self.save_button, 3, 2, 1, 2)
        self.save_button.setStyleSheet(
            "QPushButton{background-color: rgb(88, 102, 108); padding: 6px; "
            "border-radius: 3px; color: white}"
            "QPushButton::pressed{background-color: rgb(62, 72, 77); padding: 6px; "
            "border-radius: 3px; color: white}"
        )

        # Imagen
        img = QLabel()
        path = os.path.expanduser("~") + "/.config/Ciel/C-Media_Player/Media/LOGO-CMedia.png"
        img.setPixmap(QPixmap(path))
        self.mainLayout.addWidget(img, 3, 5, 1, 1, Qt.AlignRight | Qt.AlignBottom)



    def set_terminal_tab(self, terminal_tab):
        """
        Permite vincular el TerminalTabFrame después de la construcción,
        útil cuando el orden de creación no permite pasarlo en __init__.
        """
        self._terminal_tab = terminal_tab
        url = self.url_entry_terminal.text().strip()
        if url:
            self._terminal_tab.set_api_base(url, reload=True)

    def _sync_terminal_url(self, text: str):
        """Llamado cada vez que cambia el texto de url_entry_terminal."""
        if self._terminal_tab and text.strip():
            # reload=True → dispara _cargar_oficinas internamente
            self._terminal_tab.set_api_base(text.strip(), reload=True)

    def _get_config_path(self):
        """Devuelve la ruta real del archivo de configuracion (.ccmj)."""
        base = os.path.expanduser("~") + "/.config/Ciel/C-Media_Player/configs/config.json"
        with open(base, "r") as f:
            settings = json.load(f)
        ruta = settings["Ruta"]
        if ruta.startswith("$"):
            var_end = ruta.find("/")
            var = os.environ[ruta[1:var_end]]
            ruta = var + ruta[var_end:]
        return ruta

    def get_settings(self):
        """Carga la configuracion desde el archivo .ccmj."""
        try:
            path = self._get_config_path()
            with open(path, "r", encoding="utf-8-sig") as f:
                settings = json.load(f)
            for pantalla in settings["Pantallas"]:
                for controller in pantalla["Controles"]:
                    if "Control.NavegadorWebChrome.dll" in controller["NombreArchivo"]:
                        self.setEnabled(True)
                        self.url          = controller["ObjetoBase"].get("UrlInicio", "")
                        self.nav_bar      = controller["ObjetoBase"].get("MostrarBarraNavegacion", False)
                        self.url_terminal = controller["ObjetoBase"].get("UrlTerminal", "")
        except Exception as e:
            print(f"[WebTabFrame] get_settings error: {e}")

    def save_settings(self):
        """Guarda la URL, nav_bar y URL terminal en el archivo .ccmj."""
        try:
            path = self._get_config_path()

            with open(path, "r", encoding="utf-8-sig") as f:
                settings = json.load(f)

            for pantalla in settings["Pantallas"]:
                for controller in pantalla["Controles"]:
                    if "Control.NavegadorWebChrome.dll" in controller["NombreArchivo"]:
                        controller["ObjetoBase"]["UrlInicio"]             = self.url_entry.text().strip()
                        controller["ObjetoBase"]["MostrarBarraNavegacion"] = self.nav_bar_button.get()
                        controller["ObjetoBase"]["UrlTerminal"]            = self.url_entry_terminal.text().strip()

            with open(path, "w", encoding="utf-8-sig") as f:
                json.dump(settings, f, ensure_ascii=False)

            # Sincronizar con el tab de terminales
            url_terminal = self.url_entry_terminal.text().strip()
            if self._terminal_tab and url_terminal:
                self._terminal_tab.set_api_base(url_terminal, reload=True)

        except Exception as e:
            print(f"[WebTabFrame] save_settings error: {e}")
            QMessageBox.critical(self, "Error al guardar", str(e))



   