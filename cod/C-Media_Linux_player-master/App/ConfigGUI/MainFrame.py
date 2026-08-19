from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *

from .CodeReaderTabFrame import CodeReaderTabFrame
from .GeneralTabFrame import GeneralTabFrame
from .WebTabFrame import WebTabFrame
from .PrinterTabFrame import PrinterTabFrame

from .TitleBar import TitleBar

import os
import inspect

# ---------------------------------------------------------------------------
# Paleta de colores (misma base que GeneralTabFrame / TerminalTabFrame)
# ---------------------------------------------------------------------------
COLOR_NARANJA = "#f99f04"
COLOR_NARANJA_HOVER = "#ff8c00"
COLOR_NARANJA_PRESSED = "#f99f04"
COLOR_FONDO = "#FFFFFF"
COLOR_INPUT_BG = "#F2F4F6"
COLOR_BORDE = "#E4E6E9"
COLOR_TEXTO = "#313336"
COLOR_TEXTO_SUAVE = "#5B6066"

RUTA_BASE = os.path.expanduser("~") + "/.config/Ciel/C-Media_Player"
RUTA_ICONOS = RUTA_BASE + "/images"

ALTO_TITLEBAR = 36

# ---------------------------------------------------------------------------
# Iconos de cada pestana.
# Si el archivo no existe la pestana simplemente queda sin icono, no falla.
# Ajusta los nombres a los SVG/PNG que tengas en la carpeta images/.
# ---------------------------------------------------------------------------
ICONOS_TABS = {
    "General":        "settings_24dp_FFFFFF_FILL0_wght400_GRAD-25_opsz24.svg",
    "Contenedor Web": "public_24dp_FFFFFF_FILL0_wght400_GRAD-25_opsz24.svg",
    "Impresora":      "print_24dp_FFFFFF_FILL0_wght400_GRAD-25_opsz24.svg",
    "Lector":         "barcode_scanner_24dp_FFFFFF_FILL0_wght400_GRAD-25_opsz24.svg",
    "Terminales":     "desktop_windows_24dp_FFFFFF_FILL0_wght400_GRAD-25_opsz24.svg",
}


def icono_pestana(nombre_archivo, color_normal=COLOR_TEXTO_SUAVE, color_activo=COLOR_NARANJA):
    """
    Carga un icono desde images/ y lo recolorea para que combine con la pestana:
    gris cuando esta inactiva y naranja cuando esta seleccionada.

    Los iconos del proyecto son blancos (pensados para botones naranjas), asi que
    sobre el fondo blanco de las pestanas se verian invisibles: por eso se
    repintan con QPainter en lugar de usarlos tal cual.

    Devuelve un QIcon vacio si el archivo no existe (la pestana queda sin icono).
    """
    ruta = os.path.join(RUTA_ICONOS, nombre_archivo)
    if not os.path.exists(ruta):
        return QIcon()

    base = QPixmap(ruta)
    if base.isNull():
        return QIcon()

    base = base.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def recolorear(color):
        pix = QPixmap(base.size())
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.drawPixmap(0, 0, base)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pix.rect(), QColor(color))
        painter.end()
        return pix

    icono = QIcon()
    icono.addPixmap(recolorear(color_normal), QIcon.Normal)
    # Qt dibuja la pestana seleccionada en modo Active
    icono.addPixmap(recolorear(color_activo), QIcon.Active)
    icono.addPixmap(recolorear(color_activo), QIcon.Selected)
    icono.addPixmap(recolorear(COLOR_BORDE), QIcon.Disabled)
    return icono


class MainFrame(QWidget):
    """Clase de pantalla principal (configuracion)"""

    def __init__(self):
        """
        Constructor de clase
        """
        super().__init__()

        # -------------------------------------------------------------------
        # Ventana
        # -------------------------------------------------------------------
        icon = QIcon()
        icon.addFile(RUTA_BASE + "/Media/Logo-CMedia_C.png", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.setWindowTitle("C-Media Player Lx · Configuración")
        self.setFixedSize(800, 500)
        QCoreApplication.setApplicationName("C-Media Player Lx · Configuration")

        self.setWindowFlags(Qt.FramelessWindowHint)

        # -------------------------------------------------------------------
        # Fondo blanco (antes era #dae7ef, que no combinaba con las pestanas)
        # -------------------------------------------------------------------
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
            QTabWidget::pane {{
                border: 1px solid {COLOR_BORDE};
                border-radius: 8px;
                background-color: {COLOR_FONDO};
                top: -1px;
            }}
            QTabBar {{
                background: transparent;
                qproperty-drawBase: 0;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {COLOR_TEXTO_SUAVE};
                padding: 8px 18px;
                margin-right: 2px;
                font-size: 14px;
                border: none;
                border-bottom: 2.5px solid transparent;
            }}
            QTabBar::tab:hover {{
                color: {COLOR_TEXTO};
                background-color: {COLOR_INPUT_BG};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                font-weight: bold;
                color: {COLOR_NARANJA};
                border-bottom: 2.5px solid {COLOR_NARANJA};
                background-color: transparent;
            }}
            QToolTip {{
                background-color: {COLOR_FONDO};
                color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE};
                padding: 4px;
            }}
        """)

        # -------------------------------------------------------------------
        # Barra de titulo personalizada
        # -------------------------------------------------------------------
        self.TitleBar = TitleBar(self)
        self.TitleBar.setGeometry(0, 0, self.width(), ALTO_TITLEBAR)
        self.TitleBar.show()
        self.TitleBar.raise_()

        # -------------------------------------------------------------------
        # Layout: el margen superior deja libre la barra de titulo
        # (antes era 10 y el QTabWidget quedaba por debajo de la TitleBar)
        # -------------------------------------------------------------------
        self.mainLayout = QGridLayout()
        self.mainLayout.setContentsMargins(10, ALTO_TITLEBAR + 8, 10, 10)
        self.setLayout(self.mainLayout)

        # -------------------------------------------------------------------
        # Pestanas
        # -------------------------------------------------------------------
       

        self.tabWidget = QTabWidget(self)
        self.tabWidget.setIconSize(QSize(18, 18))
        self.tabWidget.setDocumentMode(True)

        self.generalTab = GeneralTabFrame()
        self.printerTab = PrinterTabFrame()
        self.readerTab = CodeReaderTabFrame()

        pestanas = [
            (self.generalTab,  "General"),
            (self.webTab,      "Contenedor Web"),
            (self.printerTab,  "Impresora"),
            (self.readerTab,   "Lector"),
            (self.terminal_Tab, "Terminales"),
        ]

        for widget, titulo in pestanas:
            icono = icono_pestana(ICONOS_TABS.get(titulo, ""))
            self.tabWidget.addTab(widget, icono, titulo)

        self.mainLayout.addWidget(self.tabWidget)

        # -------------------------------------------------------------------
        # Paleta clara coherente con el resto de la aplicacion
        # -------------------------------------------------------------------
        palette = QPalette()
        palette.setColor(QPalette.Window, COLOR_FONDO)
        palette.setColor(QPalette.WindowText, COLOR_TEXTO)
        palette.setColor(QPalette.Base, COLOR_FONDO)
        palette.setColor(QPalette.AlternateBase, COLOR_INPUT_BG)
        palette.setColor(QPalette.ToolTipBase, COLOR_FONDO)
        palette.setColor(QPalette.ToolTipText, COLOR_TEXTO)
        palette.setColor(QPalette.Text, COLOR_TEXTO)
        palette.setColor(QPalette.Button, COLOR_FONDO)
        palette.setColor(QPalette.ButtonText, COLOR_TEXTO)
        palette.setColor(QPalette.BrightText, COLOR_NARANJA)
        palette.setColor(QPalette.Link, COLOR_NARANJA)
        palette.setColor(QPalette.Highlight, COLOR_NARANJA)
        palette.setColor(QPalette.HighlightedText, Qt.white)
        # Estados deshabilitados en claro (antes usaban grises oscuros de tema dark)
        palette.setColor(QPalette.Disabled, QPalette.Base, QColor(COLOR_INPUT_BG))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#9AA0A6"))
        palette.setColor(QPalette.Disabled, QPalette.Button, QColor(COLOR_BORDE))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#9AA0A6"))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#9AA0A6"))
        self.setPalette(palette)

    def _crear_web_tab(self, terminal_tab):
        """
        Crea el WebTabFrame enlazandolo con la pestana de terminales.

        Compatibilidad: las versiones antiguas de WebTabFrame no aceptan el
        parametro 'terminal_tab'. En ese caso se construye sin argumentos y el
        enlace se hace despues (set_terminal_tab o atributo directo), para que
        la configuracion abra igual en equipos con la version vieja del archivo.
        """
        try:
            parametros = inspect.signature(WebTabFrame.__init__).parameters
        except (TypeError, ValueError):
            parametros = {}

        acepta_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in parametros.values()
        )

        if "terminal_tab" in parametros or acepta_kwargs:
            return WebTabFrame(terminal_tab=terminal_tab)

        # Firma antigua: sin el parametro
        web = WebTabFrame()

        if hasattr(web, "set_terminal_tab"):
            web.set_terminal_tab(terminal_tab)
        else:
            web.terminal_tab = terminal_tab

        return web

    def resizeEvent(self, event):
        """
        Mantiene la barra de titulo del ancho de la ventana
        """
        super().resizeEvent(event)
        if hasattr(self, "TitleBar"):
            self.TitleBar.setGeometry(0, 0, self.width(), ALTO_TITLEBAR)