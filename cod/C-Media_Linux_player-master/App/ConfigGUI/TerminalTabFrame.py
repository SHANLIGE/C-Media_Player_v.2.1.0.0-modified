import json
import os

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QHeaderView, QAbstractItemView,
    QMessageBox, QScrollArea, QSizePolicy, QSpinBox, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtGui import QPalette, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QUrl, QByteArray, QJsonDocument

#reutilizables
_ACCENT       = "rgb(88, 102, 108)"
_ACCENT_PRESS = "rgb(62, 72, 77)"
_BG_COLOR     = "#dae7ef"

STYLE_COMBO = (
    "color: black; background-color: white; "
    f"selection-background-color: {_ACCENT};"
)
STYLE_LINE = (
    "color: black; background-color: white; "
    f"border: 1px solid {_ACCENT}; border-radius: 3px; padding: 3px;"
)
STYLE_BTN = (
    f"QPushButton{{background-color: {_ACCENT}; padding: 6px; "
    f"border-radius: 3px; color: white}}"
    f"QPushButton::pressed{{background-color: {_ACCENT_PRESS}; padding: 6px; "
    f"border-radius: 3px; color: white}}"
)
STYLE_BTN_DANGER = (
    "QPushButton{background-color: rgb(180,50,50); padding: 6px; "
    "border-radius: 3px; color: white}"
    "QPushButton::pressed{background-color: rgb(130,30,30); padding: 6px; "
    "border-radius: 3px; color: white}"
)
STYLE_GROUP = (
    f"QGroupBox{{font-weight: bold; border: 1px solid {_ACCENT}; "
    "border-radius: 4px; margin-top: 8px; padding-top: 6px;}}"
    f"QGroupBox::title{{subcontrol-origin: margin; left: 8px; color: {_ACCENT};}}"
)


API_BASE_DEFAULT = (
    "https://keraltylaboratoriospruebasd5.cielingenioparalavida.com:5512"
    "/HostServicioTerminalRest.svc"
)

# Endpoints
EP_OFICINAS        = "/ObtenerOficinas"
EP_TERMINALES      = "/ObtenerTerminales/{oficina}"
EP_AGREGAR         = "/AgregarTerminal"
EP_ELIMINAR        = "/EliminarTerminal/{id}"


class TerminalDialog(QDialog):
    """Ventana modal para capturar los datos de una nueva terminal."""

    def __init__(self, num_terminales: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva terminal")
        self.setModal(True)
        self.setMinimumWidth(340)

        form = QFormLayout(self)
        form.setSpacing(8)

        # Dirección de terminal (1..24)
        self.spin_dir = QSpinBox()
        self.spin_dir.setRange(1, 24)
        self.spin_dir.setValue(num_terminales + 1)
        self.spin_dir.setStyleSheet(STYLE_LINE)
        form.addRow("Dirección de terminal:", self.spin_dir)

        # Servicio
        self.line_servicio = QLineEdit()
        self.line_servicio.setPlaceholderText("Ej: Caja, Farmacia…")
        self.line_servicio.setStyleSheet(STYLE_LINE)
        form.addRow("Servicio:", self.line_servicio)

        # Prioridad
        self.spin_prioridad = QSpinBox()
        self.spin_prioridad.setRange(1, 99)
        self.spin_prioridad.setValue(1)
        self.spin_prioridad.setStyleSheet(STYLE_LINE)
        form.addRow("Prioridad:", self.spin_prioridad)

        # Botones OK / Cancelar
        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.button(QDialogButtonBox.Ok).setStyleSheet(STYLE_BTN)
        btns.button(QDialogButtonBox.Cancel).setStyleSheet(STYLE_BTN)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_data(self):
        return {
            "direccion":  self.spin_dir.value(),
            "servicio":   self.line_servicio.text().strip(),
            "prioridad":  self.spin_prioridad.value(),
        }



class TerminalTabFrame(QWidget):
    """
    Pestaña de gestión de terminales de llamado.

    Flujo:
      1. Se carga la lista de oficinas desde la API.
      2. Al seleccionar una oficina, se cargan sus terminales configuradas.
      3. La tabla muestra: Dirección | Servicio | Prioridad.
      4. Botones Agregar / Eliminar interactúan con la API y refrescan la tabla.

    La URL base de la API se lee del WebTabFrame (url_entry de la fila "Terminal").
    Si no está disponible, se usa API_BASE_DEFAULT.
    """

    def __init__(self, api_base: str = ""):
        super().__init__()

        self._api_base = (api_base or API_BASE_DEFAULT).rstrip("/")
        self._nam = QNetworkAccessManager(self)   # gestor de red Qt
        self._oficina_actual: str = ""
        self._oficina_actual_id: str = ""
        self._terminales: list = []               # datos en memoria

      
        bg = QPalette()
        bg.setColor(QPalette.Window, _BG_COLOR)
        self.setAutoFillBackground(True)
        self.setPalette(bg)

     
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border: none; background: transparent;}")
        root.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet(f"background: {_BG_COLOR};")
        scroll.setWidget(container)

        self.mainLayout = QVBoxLayout(container)
        self.mainLayout.setSpacing(10)

        grp_dir = QGroupBox("Dirección de terminal")
        grp_dir.setStyleSheet(STYLE_GROUP)
        gl_dir = QGridLayout(grp_dir)

        gl_dir.addWidget(QLabel("Terminal N°:"), 0, 0)
        self.spin_terminal_dir = QSpinBox()
        self.spin_terminal_dir.setRange(1, 24)
        self.spin_terminal_dir.setValue(1)
        self.spin_terminal_dir.setStyleSheet(STYLE_LINE)
        self.spin_terminal_dir.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        gl_dir.addWidget(self.spin_terminal_dir, 0, 1)

        lbl_hint = QLabel("Seleccione el número de terminal activa (1 – 24)")
        lbl_hint.setStyleSheet("color: #4a5568; font-size: 11px;")
        gl_dir.addWidget(lbl_hint, 1, 0, 1, 2)

        self.mainLayout.addWidget(grp_dir)

  
        grp_of = QGroupBox("Oficinas")
        grp_of.setStyleSheet(STYLE_GROUP)
        gl_of = QGridLayout(grp_of)

        gl_of.addWidget(QLabel("Oficina:"), 0, 0)
        self.combo_oficina = QComboBox()
        self.combo_oficina.setStyleSheet(STYLE_COMBO)
        self.combo_oficina.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_oficina.addItem("— Cargando oficinas… —")
        self.combo_oficina.setEnabled(False)
        self.combo_oficina.currentIndexChanged.connect(self._on_oficina_changed)
        gl_of.addWidget(self.combo_oficina, 0, 1)

        self.btn_reload_oficinas = QPushButton("↻ Recargar")
        self.btn_reload_oficinas.setStyleSheet(STYLE_BTN)
        self.btn_reload_oficinas.clicked.connect(self._cargar_oficinas)
        gl_of.addWidget(self.btn_reload_oficinas, 0, 2)

        self.mainLayout.addWidget(grp_of)

       
        grp_term = QGroupBox("Terminales configuradas")
        grp_term.setStyleSheet(STYLE_GROUP)
        vl_term = QVBoxLayout(grp_term)

        self.lbl_no_oficina = QLabel("Seleccione una oficina para ver las terminales.")
        self.lbl_no_oficina.setAlignment(Qt.AlignCenter)
        self.lbl_no_oficina.setStyleSheet("color: #6b7280; font-style: italic; padding: 8px;")
        vl_term.addWidget(self.lbl_no_oficina)

        self.table_terminales = QTableWidget(0, 3)
        self.table_terminales.setHorizontalHeaderLabels(["Terminal", "Id", "N°"])
        header = self.table_terminales.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_terminales.setStyleSheet(
            "QTableWidget{background-color:white;color:black;gridline-color:#b0bec5;}"
            "QTableWidget::item{background-color:white;color:black;}"
            "QTableWidget::item:selected{background-color:rgb(88,102,108);color:white;}"
            "QHeaderView::section{background-color:rgb(88,102,108);color:white;padding:4px;font-weight:bold;}"
        )
        self.table_terminales.setAlternatingRowColors(False)
        self.table_terminales.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_terminales.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_terminales.setMinimumHeight(160)
        self.table_terminales.hide()
        vl_term.addWidget(self.table_terminales)

        # Botones de la tabla
        btn_row = QHBoxLayout()

        self.btn_crear = QPushButton("✔ Crear asignación")
        self.btn_crear.setStyleSheet(STYLE_BTN)
        self.btn_crear.setEnabled(False)
        self.btn_crear.setToolTip("Asigna el N° físico del spin a la terminal seleccionada")
        self.btn_crear.clicked.connect(self._crear_asignacion)
        btn_row.addWidget(self.btn_crear)

        self.btn_eliminar = QPushButton("✕ Eliminar seleccionada")
        self.btn_eliminar.setStyleSheet(STYLE_BTN_DANGER)
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.clicked.connect(self._eliminar_terminal)
        btn_row.addWidget(self.btn_eliminar)

        btn_row.addStretch()
        vl_term.addLayout(btn_row)

        self.mainLayout.addWidget(grp_term)

        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #4a5568; font-size: 11px; padding: 2px;")
        self.mainLayout.addWidget(self.lbl_status)

        bottom = QHBoxLayout()
        bottom.addStretch()
        img_label = QLabel()
        logo_path = os.path.expanduser("~") + "/.config/Ciel/C-Media_Player/Media/LOGO-CMedia.png"
        pix = QPixmap(logo_path)
        if not pix.isNull():
            img_label.setPixmap(pix)
        bottom.addWidget(img_label)
        self.mainLayout.addLayout(bottom)
        self.mainLayout.addStretch()

        # Solo carga si se recibió una URL real 
        if api_base:
            self._cargar_oficinas()

    def set_api_base(self, url: str, reload: bool = False):
        """
        Actualiza la URL base.
        Si reload=True dispara _cargar_oficinas() inmediatamente.
        """
        self._api_base = url.rstrip("/")
        if reload:
            self._cargar_oficinas()

    def _get(self, endpoint: str, callback):
        """Realiza un GET a la API y llama callback(reply) al terminar."""
        url = QUrl(self._api_base + endpoint)
        req = QNetworkRequest(url)
        req.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        reply = self._nam.get(req)
        reply.finished.connect(lambda: callback(reply))

    def _post(self, endpoint: str, payload: dict, callback):
        """Realiza un POST JSON a la API."""
        url = QUrl(self._api_base + endpoint)
        req = QNetworkRequest(url)
        req.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        data = QByteArray(json.dumps(payload).encode("utf-8"))
        reply = self._nam.post(req, data)
        reply.finished.connect(lambda: callback(reply))

    def _delete(self, endpoint: str, callback):
        """Realiza un DELETE a la API."""
        url = QUrl(self._api_base + endpoint)
        req = QNetworkRequest(url)
        req.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        reply = self._nam.deleteResource(req)
        reply.finished.connect(lambda: callback(reply))

    def _parse_reply(self, reply: QNetworkReply):
        """
        Devuelve (data, error_str).
        data puede ser list o dict; error_str es '' si todo fue bien.
        """
        err = reply.error()
        if err != QNetworkReply.NoError:
            return None, reply.errorString()
        raw = bytes(reply.readAll())
        try:
            return json.loads(raw.decode("utf-8")), ""
        except Exception as e:
            return None, f"JSON inválido: {e}"

    def _set_status(self, msg: str, color: str = "#4a5568"):
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet(
            f"color: {color}; font-size: 11px; padding: 2px;"
        )

   
    def _cargar_oficinas(self):
        self.combo_oficina.setEnabled(False)
        self.combo_oficina.clear()
        self.combo_oficina.addItem("— Cargando… —")
        self._set_status("Consultando lista de oficinas…")
        self._get(EP_OFICINAS, self._on_oficinas_received)

    def _on_oficinas_received(self, reply: QNetworkReply):
        data, err = self._parse_reply(reply)
        reply.deleteLater()

      
        self.combo_oficina.clear()

        if err:
            self._set_status(f"Error al cargar oficinas: {err}", "red")
            self.combo_oficina.addItem("— Error al cargar —")
            self.combo_oficina.setEnabled(False)
            return

        try:
            result = data.get("ObtenerOficinasResult", {})

            if result.get("Exitoso") is True:
                respuesta = result.get("Respuesta", [])

                self.combo_oficina.addItem("— Seleccione una oficina —")

                for item in respuesta:
                    nombre = item.get("Nombre", "")
                    oficina_id = item.get("Id", "")

                    self.combo_oficina.addItem(nombre, oficina_id)

                self.combo_oficina.setEnabled(True)
                self._set_status(
                    f"{len(respuesta)} oficina(s) cargadas.",
                    "green"
                )

        except Exception as e:
            self._set_status(f"Error procesando oficinas: {e}", "red")

    def _on_oficina_changed(self, index: int):
        text = self.combo_oficina.currentText()

        if index <= 0 or text.startswith("—"):
            self._limpiar_tabla()
            self.btn_crear.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            return

        self._oficina_actual    = text
        self._oficina_actual_id = self.combo_oficina.currentData()

        id_oficina = self._oficina_actual_id


        self._cargar_terminales(id_oficina)

    def _limpiar_tabla(self):
        self.table_terminales.setRowCount(0)
        self.table_terminales.hide()
        self.lbl_no_oficina.show()
        self._terminales = []

   
    def _cargar_terminales(self, oficina: str):
        self._limpiar_tabla()
        self._set_status(f"Cargando terminales de «{oficina}»…")
        endpoint = EP_TERMINALES.format(oficina=oficina)
        self._get(endpoint, self._on_terminales_received)

    def _on_oficinas_received(self, reply: QNetworkReply):
        data, err = self._parse_reply(reply)
        reply.deleteLater()
      
        self.combo_oficina.clear()

        if err:
            self._set_status(f"Error al cargar oficinas: {err}", "red")
            self.combo_oficina.addItem("— Error al cargar —")
            self.combo_oficina.setEnabled(False)
            return

        try:
            result = data.get("ObtenerOficinasResult", {})

            if result.get("Exitoso") is True:
                respuesta = result.get("Respuesta", [])

                self.combo_oficina.addItem("— Seleccione una oficina —")

                for item in respuesta:
                    nombre = item.get("Nombre", "")
                    oficina_id = item.get("Id", "")

                    self.combo_oficina.addItem(nombre, oficina_id)

                self.combo_oficina.setEnabled(True)
                self._set_status(
                    f"{len(respuesta)} oficina(s) cargadas.",
                    "green"
                )

        except Exception as e:
            self._set_status(f"Error procesando oficinas: {e}", "red")


    def _on_terminales_received(self, reply: QNetworkReply):
        data, err = self._parse_reply(reply)
        reply.deleteLater()

        if err:
            self._set_status(f"Error al cargar terminales: {err}", "red")
            return

        terminales = []

        try:
            result = data.get("ObtenerTerminalesXOficinaResult", {})

            if result.get("Exitoso") is True:

                respuesta = result.get("Respuesta", [])

                for t in respuesta:

                    if t.get("Tipo") == 0:

                        terminales.append({
                            "Direccion": t.get("Id"),
                            "Servicio": t.get("Nombre"),
                            "Prioridad": "1",
                            "Id": t.get("Id")
                        })

        except Exception as e:
            self._set_status(f"Error procesando terminales: {e}", "red")
            return

     


        self._terminales = terminales

        self._poblar_tabla(terminales)

        self.btn_crear.setEnabled(True)

        self._set_status(
            f"{len(terminales)} terminal(es) para «{self._oficina_actual}».",
            "green"
        )



    def _poblar_tabla(self, terminales: list):
        self.table_terminales.setRowCount(0)

        if not terminales:
            self.lbl_no_oficina.setText(
                f"No hay terminales configuradas para «{self._oficina_actual}»."
            )
            self.lbl_no_oficina.show()
            self.table_terminales.hide()
            self.btn_eliminar.setEnabled(False)
            self.btn_crear.setEnabled(False)
            return

        self.lbl_no_oficina.hide()
        self.table_terminales.show()

        # Asignaciones guardadas localmente 
        asignaciones = self._leer_asignaciones()

        for t in terminales:
            row = self.table_terminales.rowCount()
            self.table_terminales.insertRow(row)

            terminal_id = str(t.get("Id", ""))
            nombre      = str(t.get("Nombre", t.get("Servicio", "")))
            asignado    = asignaciones.get(terminal_id, "")

            # col 0: nombre terminal  |  col 1: id  |  col 2: N° asignado
            for col, texto in enumerate([nombre, terminal_id, asignado]):
                item = QTableWidgetItem(texto)
                item.setForeground(Qt.black)
                item.setBackground(Qt.white)
                self.table_terminales.setItem(row, col, item)

            # Id en UserRole de col 0 para operaciones posteriores
            self.table_terminales.item(row, 0).setData(Qt.UserRole, terminal_id)

        self.btn_eliminar.setEnabled(True)
        self.btn_crear.setEnabled(True)

    def _base_cfg_path(self) -> str:
        return os.path.expanduser("~") + "/.config/Ciel/C-Media_Player/configs/config.json"

    def _leer_asignaciones(self) -> dict:
        """Devuelve {id_terminal_d5: num_fisico} desde config.json."""
        try:
            with open(self._base_cfg_path(), "r") as f:
                cfg = json.load(f)
            return cfg.get("SelectorPNP", {}).get("DireccionTerminal", {})
        except Exception:
            return {}

    def _guardar_asignaciones(self, asignaciones: dict):
        """Persiste {id_d5: num_fisico} y la oficina activa en config.json."""
        try:
            with open(self._base_cfg_path(), "r") as f:
                cfg = json.load(f)
            cfg.setdefault("SelectorPNP", {})
            cfg["SelectorPNP"]["DireccionTerminal"]  = asignaciones
            cfg["SelectorPNP"]["OficinaConfigurada"] = self._oficina_actual
            with open(self._base_cfg_path(), "w") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))

    def _crear_asignacion(self):
        """
        Asigna el N° físico (spin 1-24) a la terminal seleccionada en la tabla
        y lo guarda localmente en config.json. Sin llamada al servidor.
        """
        row = self.table_terminales.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Sin selección",
                "Seleccione una terminal de la tabla antes de crear la asignación.")
            return

        num_asignado = self.spin_terminal_dir.value()
        terminal_id  = self.table_terminales.item(row, 0).data(Qt.UserRole)
        nombre       = self.table_terminales.item(row, 0).text()

        # Validar unicidad del número en la tabla
        for r in range(self.table_terminales.rowCount()):
            if r == row:
                continue
            celda = self.table_terminales.item(r, 2)
            if celda and celda.text() == str(num_asignado):
                otra = self.table_terminales.item(r, 0).text()
                QMessageBox.warning(self, "Número duplicado",
                    f"El N° {num_asignado} ya está asignado a «{otra}».\n"
                    "Cada terminal debe tener un número único.")
                return

        if QMessageBox.question(self, "Confirmar",
                f"¿Asignar N° {num_asignado} a «{nombre}»?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) != QMessageBox.Yes:
            return

        # Quitar ese número si ya estaba en otro ID, luego asignar
        asignaciones = self._leer_asignaciones()
        asignaciones = {k: v for k, v in asignaciones.items() if v != str(num_asignado)}
        asignaciones[str(terminal_id)] = str(num_asignado)
        self._guardar_asignaciones(asignaciones)

        # Actualizar solo la celda col 2 sin recargar la tabla
        item = QTableWidgetItem(str(num_asignado))
        item.setForeground(Qt.black)
        item.setBackground(Qt.white)
        self.table_terminales.setItem(row, 2, item)

        self._set_status(f"N° {num_asignado} asignado a «{nombre}» y guardado.", "green")

    def _eliminar_terminal(self):
        row = self.table_terminales.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selección vacía", "Seleccione una terminal para eliminar.")
            return

        item = self.table_terminales.item(row, 0)
        direccion = item.text()
        terminal_id = item.data(Qt.UserRole)

        resp = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Desea eliminar la terminal «{direccion}»?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
            
        )
        if resp != QMessageBox.Yes:
            return

        self._set_status(f"Eliminando terminal {direccion}…")
        endpoint = EP_ELIMINAR.format(id=terminal_id)
        self._delete(endpoint, self._on_terminal_eliminada)

    def _on_terminal_eliminada(self, reply: QNetworkReply):
        data, err = self._parse_reply(reply)
        reply.deleteLater()

        if err:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar la terminal:\n{err}")
            self._set_status("Error al eliminar terminal.", "red")
            return

        QMessageBox.information(self, "Éxito", "Terminal eliminada correctamente.")
        self._cargar_terminales(self._oficina_actual_id)