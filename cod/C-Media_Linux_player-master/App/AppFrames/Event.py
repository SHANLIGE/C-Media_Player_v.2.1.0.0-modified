from PySide6.QtCore import QMetaObject, Qt, Q_ARG
print("Importando clase Event...")
class Event():

    print("Cargando clase Event...")
    """
    Clase que permite el manejo de eventos de la aplicación
    :param nombre_js: str. nombre del controlador al que pertenece el evento
    """
    def __init__(self, nombre_js):
        """
        Clase que permite el manejo de eventos de la aplicación
        :param nombre_js: str. nombre del controlador al que pertenece el evento
        """
        self.isLoaded = False
        self.queue = []
        self.value = False
        self.nombre_js = nombre_js
        self.function = ""
        self.params = ""
        self.page = None
        print("Evento creado")
        
    def awake_js(self, js):
        print("EVENT awake_js llamado")
        print("PAGE:", self.page)
        print("LOADED:", self.isLoaded)

        if self.isLoaded and self.page:
            print("EJECUTANDO JS")
            QMetaObject.invokeMethod(
                self.page,
                "ejecutarJavaScript",
                Qt.QueuedConnection,
                Q_ARG(str, js)
            )
        else:
            print("NO SE EJECUTA, SE VA A COLA")
            self.queue.append(js)

    def awake(self, function, params):
        """
        Enciende el evento
        :param function: nombre de la funcion a llamar en js
        :param params: list. Lista de los parametros a la funcion js
        """
        print(f"Awake llamado para función: {function} con params: {params}")
        self.value = True
        self.function = function
        self.params = params
        if self.isLoaded and self.page:
            js = "Ciel.MPC.WebPlayer.Controles."+self.nombre_js+"."+self.function+"("+",".join(self.params)+")"

            QMetaObject.invokeMethod(self.page, "ejecutarJavaScript", 
                         Qt.QueuedConnection, 
                         Q_ARG(str, js))

            
            self.clear()
        else:
            self.queue.append("Ciel.MPC.WebPlayer.Controles."+self.nombre_js+"."+self.function+"("+",".join(self.params)+")")
            self.clear()

    def clear(self):
        """
        Limpia el evento
        """
        self.value = False
        self.function = ""
        self.params = ""

    def get(self):
        """
        Obtiene el evento
        """
        print("Obteniendo evento")

        return self.value

    def set_page(self, page):
        """
        Establece el navegador en el que se desplegara el evento
        """
        self.page = page
        

    def loaded(self):
        self.isLoaded = True

        if not self.page:
            print("No hay página web asignada (self.page es None)")
            return

        for event in self.queue:
            self.page.runJavaScript(event)

        self.queue.clear()
   