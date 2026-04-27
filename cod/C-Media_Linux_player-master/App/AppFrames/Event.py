from PySide6.QtCore import QMetaObject, Qt, Q_ARG
import logging

log = logging.getLogger("Event")
log.debug("Clase Event cargada.")


class Event():
    """
    Clase que permite el manejo de eventos de la aplicación.
    Encola llamadas JavaScript hasta que la página web esté lista.
    :param nombre_js: str. Nombre del controlador JS al que pertenece el evento.
    """

    def __init__(self, nombre_js):
        self.isLoaded = False
        self.queue    = []
        self.value    = False
        self.nombre_js = nombre_js
        self.function  = ""
        self.params    = ""
        self.page      = None

    # ------------------------------------------------------------------
    # awake_js — ejecuta JavaScript arbitrario
    # ------------------------------------------------------------------

    def awake_js(self, js):
        """
        Ejecuta un fragmento JavaScript arbitrario.
        Si la página no está lista, lo encola.
        """
        log.debug(f"[{self.nombre_js}] awake_js — loaded={self.isLoaded}, page={self.page is not None}")

        if self.isLoaded and self.page:
            self._invoke(js)
        else:
            log.debug(f"[{self.nombre_js}] awake_js encolado.")
            self.queue.append(js)

    # ------------------------------------------------------------------
    # awake — construye y ejecuta la llamada al controlador JS
    # ------------------------------------------------------------------

    def awake(self, function, params):
        """
        Ejecuta Ciel.MPC.WebPlayer.Controles.<nombre_js>.<function>(<params>)
        Si la página no está lista, encola la llamada.

        :param function: str. Nombre de la función JS a llamar.
        :param params:   list. Lista de strings con los argumentos.
        """
        self.value    = True
        self.function = function
        self.params   = params

        js = (
            "Ciel.MPC.WebPlayer.Controles."
            + self.nombre_js + "."
            + function
            + "(" + ",".join(params) + ")"
        )

        log.debug(f"[{self.nombre_js}] awake → {js[:120]}")

        if self.isLoaded and self.page:
            self._invoke(js)
        else:
            log.debug(f"[{self.nombre_js}] awake encolado (loaded={self.isLoaded})")
            self.queue.append(js)

        self.clear()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _invoke(self, js):
        if not self.page:
            log.warning(f"[{self.nombre_js}] page es None")
            return

        try:
            # 🔥 EJECUCIÓN REAL DIRECTA (thread-safe usando signal implícito de Qt)
            self.page.runJavaScript(js)

            log.debug(f"[{self.nombre_js}] JS ejecutado")

        except Exception as e:
            log.error(f"[{self.nombre_js}] JS error: {e}")  

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def clear(self):
        """Limpia el estado del evento."""
        self.value    = False
        self.function = ""
        self.params   = ""

    def get(self):
        """Retorna si el evento está activo."""
        return self.value

    def set_page(self, page):
        """
        Asigna la página web donde se ejecutará el JavaScript.
        Debe llamarse antes de loaded().
        """
        self.page = page
        log.debug(f"[{self.nombre_js}] Página asignada.")

    def loaded(self):
        """
        Marca el evento como listo y vacía la cola de JS pendiente.
        Debe llamarse después de set_page(), cuando la página terminó de cargar.
        """
        self.isLoaded = True

        if not self.page:
            log.warning(f"[{self.nombre_js}] loaded() llamado sin página asignada — cola retenida.")
            return

        log.debug(f"[{self.nombre_js}] loaded() — ejecutando {len(self.queue)} elemento(s) en cola.")
        for js in self.queue:
            self._invoke(js)
        self.queue.clear()