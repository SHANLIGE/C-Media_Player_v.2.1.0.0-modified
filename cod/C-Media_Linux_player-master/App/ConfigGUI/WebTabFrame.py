from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

#Otras librerías
import json
import os


# ---------------------------------------------------------------------------
# Paleta de colores
# ---------------------------------------------------------------------------
COLOR_NARANJA = "#f99f04"
COLOR_NARANJA_HOVER = "#ff8c00"
COLOR_NARANJA_PRESSED = "#f99f04"
COLOR_FONDO = "#FFFFFF"
COLOR_INPUT_BG = "#F2F4F6"
COLOR_BORDE = "#E4E6E9"
COLOR_TEXTO = "#313336"
COLOR_TEXTO_SUAVE = "#5B6066"
COLOR_BACKGROUND = "#F2F4F6"


class WebTabFrame(QWidget):
    """
    Clase de vista de configuracion del Contenedor Web
    """
    def __init__(self):
        """
        Clase de vista de configuracion del Contenedor Web
        """
        super().__init__()
        self.setEnabled(False)
        self.url = ""
        self.nav_bar = False
        self.get_settings()

        # Fondo blanco
        bg = QPalette()
        bg.setColor(QPalette.Window, COLOR_FONDO)
        self.setAutoFillBackground(True)
        self.setPalette(bg)

        self.setStyleSheet(f"""
            QWidget {{
                color: {COLOR_TEXTO};
                font-family: "Segoe UI", "Noto Sans", sans-serif;
                font-size: 13px;
            }}
            QLineEdit, QSpinBox {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE};
                border-radius: 8px;
                padding: 8px 10px;
            }}
            QLineEdit:read-only {{
                color: {COLOR_TEXTO_SUAVE};
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {COLOR_BORDE};
                border-radius: 5px;
                background-color: white;
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLOR_NARANJA};
                border: 2px solid {COLOR_NARANJA};
            }}
            QFrame#separador {{
                background-color: {COLOR_BORDE};
                max-height: 1px;
                min-height: 1px;
            }}
            QLabel#tituloSeccion {{
                font-weight: 600;
                font-size: 14px;
            }}
            QLabel#cajaIcono {{
                background-color: {COLOR_BACKGROUND};
                border: 1px solid {COLOR_BORDE};
                border-radius: 5px;
                color: {COLOR_NARANJA};
                font-size: 16px;
                font-weight: bold;
            }}
        """)

        # Layout principal vertical
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(20, 18, 20, 18)
        self.mainLayout.setSpacing(14)
        self.setLayout(self.mainLayout)

        # ------------------------------------------------------------------
        # Fila 1: URL
        # ------------------------------------------------------------------
        titulo_url = QLabel("Url")
        titulo_url.setObjectName("tituloSeccion")
        self.mainLayout.addWidget(titulo_url)

        self.url_entry = QLineEdit(self.url)
        self.url_entry.setMinimumHeight(38)
        self.mainLayout.addWidget(self.url_entry)

        self.mainLayout.addWidget(self._crear_separador())

        # ------------------------------------------------------------------
        # Fila 2: Barra de navegacion
        # ------------------------------------------------------------------
        fila_navbar = QHBoxLayout()
        fila_navbar.setSpacing(28)

        self.nav_bar_button = QCheckBox()
        self.nav_bar_button.setChecked(self.nav_bar)
        # self.nav_bar_button.toggled.connect(self.funcionnb)  # CAMBIAR FUNCION
        fila_navbar.addLayout(self._crear_fila_opcion("🌐", "Barra de Navegación", self.nav_bar_button))
        fila_navbar.addStretch(1)

        self.mainLayout.addLayout(fila_navbar)
        self.mainLayout.addWidget(self._crear_separador())

        # ------------------------------------------------------------------
        # Fila 3: Guardar centrado
        # ------------------------------------------------------------------
        self.save_button = self._crear_boton("💾  Guardar")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setMinimumWidth(260)

        fila_guardar = QHBoxLayout()
        fila_guardar.addStretch(1)
        fila_guardar.addWidget(self.save_button)
        fila_guardar.addStretch(1)

        # ------------------------------------------------------------------
        # Fila 4: Logo a la derecha (igual que GeneralTabFrame)
        # ------------------------------------------------------------------
        img = QLabel()
        path = os.path.expanduser('~') + "/.config/Ciel/C-Media_Player/Media/LOGO-CMedia.png"
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(110, Qt.SmoothTransformation)
        img.setPixmap(pixmap)
        opacidad = QGraphicsOpacityEffect(img)
        opacidad.setOpacity(0.18)
        img.setGraphicsEffect(opacidad)

        fila_logo = QHBoxLayout()
        fila_logo.addStretch(1)
        fila_logo.addWidget(img, alignment=Qt.AlignRight | Qt.AlignBottom)

        self.mainLayout.addStretch(1)
        self.mainLayout.addLayout(fila_guardar)
        self.mainLayout.addLayout(fila_logo)

    # -----------------------------------------------------------------
    # Helpers visuales
    # -----------------------------------------------------------------
    def _crear_boton(self, texto):
        """
        Crea un boton con el estilo naranja redondeado
        """
        boton = QPushButton(texto)
        boton.setCursor(Qt.PointingHandCursor)
        boton.setMinimumHeight(40)
        boton.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_NARANJA};
                color: white;
                padding: 8px 18px;
                border-radius: 9px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLOR_NARANJA_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_NARANJA_PRESSED};
            }}
        """)
        return boton

    def _crear_separador(self):
        """
        Linea horizontal divisoria entre secciones
        """
        linea = QFrame()
        linea.setObjectName("separador")
        linea.setFrameShape(QFrame.HLine)
        return linea

    def _crear_caja_icono(self, caracter):
        """
        Caja cuadrada con icono unicode en naranja suave
        """
        caja = QLabel(caracter)
        caja.setObjectName("cajaIcono")
        caja.setFixedSize(36, 36)
        caja.setAlignment(Qt.AlignCenter)
        return caja

    def _crear_fila_opcion(self, caracter, texto, checkbox):
        """
        Fila: caja de icono + etiqueta + checkbox
        """
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(self._crear_caja_icono(caracter))
        layout.addWidget(QLabel(texto))
        layout.addSpacing(6)
        layout.addWidget(checkbox)
        return layout

    # -----------------------------------------------------------------
    # Logica original (sin cambios)
    # -----------------------------------------------------------------
    def get_settings(self):
        """
        Obtiene la configuracion del archivo json y las guarda en un atributo de la clase
        """
        path = os.path.expanduser('~') + "/.config/Ciel/C-Media_Player/configs/config.json"
        with open(path, "r") as file:
            settings = json.loads(file.read())
        if "$" == settings["Ruta"][0]:
            var = os.environ[settings["Ruta"][1:settings["Ruta"].find("/")]]
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
        path = os.path.expanduser('~') + "/.config/Ciel/C-Media_Player/configs/config.json"
        with open(path, "r") as file:
            settings = json.loads(file.read())

        if "$" == settings["Ruta"][0]:
            var = os.environ[settings["Ruta"][1:settings["Ruta"].find("/")]]
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



