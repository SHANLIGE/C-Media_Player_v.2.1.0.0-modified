import sys

from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
# Otras librerias
import os
import logging
import json
import threading
import time


# Llave que guarda el monitor asignado a cada pantalla (0 = automatico)
LLAVE_MONITOR = "MonitorAsignado"


class ScreenWindow(QMainWindow):
    """
    Ventana independiente para una pantalla del archivo de configuracion
    :param frame: MainFrame. Contenido de la pantalla
    :param titulo: str. Titulo de la ventana
    :param flags: Qt.WindowFlags. Banderas heredadas de la ventana principal
    :param icono: QIcon. Icono de la aplicacion
    """

    def __init__(self, frame, titulo, flags, icono):
        super().__init__()
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setWindowIcon(icono)
        self.setWindowTitle(titulo)
        self.setWindowFlags(flags)
        self.frame = frame
        self.setCentralWidget(frame)

    def closeEvent(self, event):
        """
        Cierra el contenido de la pantalla
        """
        try:
            self.frame.closeEvent()
        except Exception as e:
            logging.error(str(e))
        event.accept()


class Player(QMainWindow):
    """
    Clase principal de la aplicacion.
    Es la ventana de la primera pantalla y administra una ventana adicional
    por cada pantalla restante, repartidas entre los monitores conectados.
    """

    # Señal para cambiar el estado de las ventanas desde el hilo de monitoreo
    estado_pantalla = Signal(bool)

    def __init__(self, debug=False):
        """
        Clase principal de la aplicacion
        """
        if debug:
            from AppFrames.MainFrame import MainFrame
        else:
            from .AppFrames.MainFrame import MainFrame
        super().__init__()
        self.flags = Qt.WindowFlags()
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)

        # Icono de la Aplicacion
        self.icono = QIcon()
        path = os.path.expanduser('~') + "/.config/Ciel/C-Media_Player/Media/Logo-CMedia_lx.png"
        self.icono.addFile(path, QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(self.icono)

        # Nombre de la Aplicacion
        QCoreApplication.setApplicationName("C-Media Player v2.2")

        self.screen_disconnected = False
        # Se usa "cerrando" y no "close" para no pisar el metodo close() de QWidget
        self.cerrando = False
        self.app = QApplication.instance()

        # Obtencion de configuracion
        self.sett = self.get_sett()
        if "$" == self.sett["Ruta"][0]:
            var = os.environ[self.sett["Ruta"][1:self.sett["Ruta"].find("/")]]
            file_name = var + self.sett["Ruta"][self.sett["Ruta"].find("/"):]
        else:
            file_name = self.sett["Ruta"]
        self.screen_config = self.get_screen_config(file_name)

        # Ventana siempre visible (Top Most)
        if self.sett["SiempreVisible"]:
            self.flags |= Qt.WindowStaysOnTopHint

        # Mostrar Borde de la Ventana
        if not (self.sett["MostrarBordeVentana"]):
            self.flags |= Qt.FramelessWindowHint

        self.setWindowFlags(self.flags)

        self.estado_pantalla.connect(self._aplicar_estado_pantalla)

        # ------------------------------------------------------------------
        # Creacion de las pantallas: una ventana por cada una
        # ------------------------------------------------------------------
        self.frames = {}
        self.titulos = {}
        self.asignaciones = {}   # numero de pantalla -> monitor pedido (0 = auto)
        self.ventanas = {}       # ventanas secundarias (pantalla 2 en adelante)

        for pantalla in self.screen_config["Pantallas"]:
            numero = pantalla.get("ScreenNumber", len(self.frames) + 1)
            self.frames[numero] = MainFrame(pantalla["Controles"])
            self.titulos[numero] = pantalla.get("TitleName", f"C-Media Player {numero}")
            self.asignaciones[numero] = pantalla.get(LLAVE_MONITOR, 0)

        numeros = sorted(self.frames)

        # La primera pantalla es esta misma ventana
        principal = numeros[0]
        self.setWindowTitle(self.titulos[principal])
        self.setCentralWidget(self.frames[principal])
        self.numero_principal = principal

        # El resto se abre en ventanas propias
        for numero in numeros[1:]:
            self.ventanas[numero] = ScreenWindow(self.frames[numero],
                                                 self.titulos[numero],
                                                 self.flags, self.icono)

        logging.info(f"Player - {len(numeros)} pantalla(s) configurada(s), "
                     f"{len(self.app.screens())} monitor(es) detectado(s)")

        # Ubicacion inicial (aun sin mostrar)
        self._aplicar_ubicaciones()

        # Reacomodo automatico cuando se conecta o desconecta un monitor
        self.app.screenAdded.connect(self._monitores_cambiaron)
        self.app.screenRemoved.connect(self._monitores_cambiaron)

        # Hilo de monitoreo (compatibilidad con el comportamiento anterior)
        self.thread = threading.Thread(target=self.print_screens, daemon=True)
        self.thread.start()

    # ------------------------------------------------------------------
    # Reparto de ventanas entre monitores
    # ------------------------------------------------------------------
    def _pares_ventanas(self):
        """
        Ventanas de la aplicacion en orden de pantalla
        :return: list[tuple]. [(numero, ventana), ...]
        """
        pares = [(self.numero_principal, self)]
        pares += [(n, self.ventanas[n]) for n in sorted(self.ventanas)]
        return pares

    def _calcular_monitores(self):
        """
        Decide en que monitor va cada pantalla.
        Primero respeta las asignaciones explicitas; las que estan en automatico
        se reparten en los monitores que queden libres.
        :return: dict. numero de pantalla -> QScreen
        """
        monitores = self.app.screens()
        principal = self.app.primaryScreen()
        resultado = {}
        usados = set()

        # 1. Asignaciones explicitas y validas
        for numero, _ in self._pares_ventanas():
            pedido = self.asignaciones.get(numero, 0)
            if pedido and pedido <= len(monitores):
                resultado[numero] = monitores[pedido - 1]
                usados.add(pedido - 1)
            elif pedido:
                logging.warning(f"Player - pantalla {numero}: el monitor {pedido} "
                                "no está conectado")

        # 2. El resto toma los monitores libres, en orden
        libres = [i for i in range(len(monitores)) if i not in usados]
        for numero, _ in self._pares_ventanas():
            if numero in resultado:
                continue
            if libres:
                indice = libres.pop(0)
                resultado[numero] = monitores[indice]
            else:
                resultado[numero] = principal

        return resultado

    def _aplicar_ubicaciones(self):
        """
        Mueve cada ventana a su monitor. En pantalla completa la deja
        ocupando todo ese monitor; si no, usa el tamaño de config.json.
        """
        asignados = self._calcular_monitores()
        completa = self.sett["PantallaCompleta"]

        ancho = self.sett["AnchoRequerido"]
        alto = self.sett["AltoRequerido"]
        izquierda = self.sett["LeftRequerido"]
        arriba = self.sett["TopRequerido"]

        ocupacion = {}   # cuantas ventanas van ya en cada monitor

        for numero, ventana in self._pares_ventanas():
            monitor = asignados.get(numero)
            if monitor is None:
                continue

            area = monitor.geometry()
            repetidas = ocupacion.get(monitor.name(), 0)
            ocupacion[monitor.name()] = repetidas + 1

            # Se fija el monitor destino de la ventana nativa
            handle = ventana.windowHandle()
            if handle is not None:
                handle.setScreen(monitor)

            if completa:
                ventana.setGeometry(area)
                if ventana.isVisible():
                    ventana.showFullScreen()
            else:
                desplazamiento = 40 * repetidas
                ventana.setGeometry(area.x() + izquierda + desplazamiento,
                                    area.y() + arriba + desplazamiento,
                                    ancho, alto)

            logging.info(f"Player - pantalla {numero} -> monitor {monitor.name()} "
                         f"{area.width()}x{area.height()} en ({area.x()},{area.y()})")

    @Slot()
    def _monitores_cambiaron(self, *args):
        """
        Se llama cuando el sistema agrega o quita un monitor.
        Espera un momento a que el escritorio termine de reorganizarse
        y vuelve a repartir las ventanas.
        """
        if self.cerrando:
            return
        logging.info(f"Player - cambio de monitores: {len(self.app.screens())} conectado(s)")
        QTimer.singleShot(1200, self._reubicar)

    @Slot()
    def _reubicar(self):
        """
        Reaplica las ubicaciones despues de un cambio de monitores
        """
        if self.cerrando:
            return
        self._aplicar_ubicaciones()

    def show(self):
        """
        Muestra la ventana principal y todas las ventanas secundarias
        """
        super().show()
        for numero in sorted(self.ventanas):
            self.ventanas[numero].show()

        # Con las ventanas ya creadas se puede fijar el monitor nativo
        self._aplicar_ubicaciones()

    def ventanas_todas(self):
        """
        Devuelve la ventana principal junto con las secundarias
        :return: list[QMainWindow]
        """
        return [ventana for _, ventana in self._pares_ventanas()]

    @Slot(bool)
    def _aplicar_estado_pantalla(self, completa):
        """
        Aplica pantalla completa o ventana normal a todas las ventanas.
        Se ejecuta siempre en el hilo de la interfaz.
        :param completa: bool. True para pantalla completa
        """
        if completa:
            self._aplicar_ubicaciones()
        else:
            for ventana in self.ventanas_todas():
                ventana.showNormal()

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        """
        Evento de cierre de la aplicacion: cierra tambien las pantallas secundarias
        """
        self.cerrando = True
        for numero in sorted(self.ventanas, reverse=True):
            self.ventanas[numero].close()
        try:
            self.centralWidget().closeEvent()
        except Exception as e:
            logging.error(str(e))
        event.accept()

    def get_screen_config(self, ruta):
        """
        Obtiene la informacion de las pantallas y su configuracion
        :param ruta: str. Ruta donde se encuentra el archivo de configuracion
        :return: dic. Configuracion extraida del archivo json
        """
        try:
            with open(ruta, 'r', encoding="utf-8-sig") as file:
                screen_config = json.load(file)
            return screen_config
        except Exception as e:
            logging.error(str(e))
            QMessageBox.warning(self, "Advertencia",
                                "Ha ocurrido un problema con el archivo de las pantallas, "
                                "seleccione uno válido desde la aplicación de configuración.")
            sys.exit()

    def get_sett(self):
        """
        Obtiene la informacion de configuracion de la aplicacion
        :return: dic. Configuracion extraida del archivo json
        """
        path = os.path.expanduser('~') + "/.config/Ciel/C-Media_Player/configs/config.json"
        try:
            with open(path, "r") as file:
                sett = json.load(file)
            return sett
        except Exception as e:
            logging.error(str(e))
            QMessageBox.warning(self, "Advertencia",
                                "Uno de los archivos de la aplicacción no fue instalado correctamente. "
                                "Por favor reinstale la aplicación")
            sys.exit()

    def focus_changed(self):
        if self.sett["PantallaCompleta"]:
            if self.isActiveWindow():
                self.showFullScreen()
        if self.sett["SiempreVisible"]:
            for numero in sorted(self.frames):
                try:
                    self.frames[numero].focus_changed()
                except Exception as e:
                    logging.error(str(e))
            qApp.setActiveWindow(self)

    def print_screens(self):
        """
        Monitorea la conexion de monitores y ajusta todas las ventanas.
        No toca la interfaz directamente: emite una señal hacia el hilo principal.
        """
        while not self.cerrando:
            try:
                nombre = self.app.screens()[0].name()
            except Exception:
                time.sleep(0.5)
                continue

            if nombre == ":0.0" and not self.screen_disconnected:
                self.screen_disconnected = True
                self.estado_pantalla.emit(False)

            elif self.screen_disconnected and nombre != ":0.0":
                time.sleep(0.5)
                if self.sett["PantallaCompleta"]:
                    self.estado_pantalla.emit(True)
                self.screen_disconnected = False

            time.sleep(0.3)
        