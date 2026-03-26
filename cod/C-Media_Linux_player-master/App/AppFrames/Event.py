from PySide6.QtCore import QMetaObject, Qt, Q_ARG

class Event():
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
        
    def awake_js(self, js):
        if self.isLoaded:
            QMetaObject.invokeMethod(self.page, "ejecutarJavaScript", 
                         Qt.QueuedConnection, 
                         Q_ARG(str, js))
                         
            self.clear()
        else:
            self.queue.append(js)
            self.clear()

    def awake(self, function, params):
        """
        Enciende el evento
        :param function: nombre de la funcion a llamar en js
        :param params: list. Lista de los parametros a la funcion js
        """
        self.value = True
        self.function = function
        self.params = params
        if self.isLoaded:
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
        return self.value

    def set_page(self, page):
        """
        Establece el navegador en el que se desplegara el evento
        """
        self.page = page
        

    def loaded(self):
        self.isLoaded = True
        for event in self.queue:
            self.page.runJavaScript(event)
            self.queue.remove(event)