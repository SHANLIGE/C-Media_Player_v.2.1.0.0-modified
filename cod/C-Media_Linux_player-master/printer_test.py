#http://192.168.1.138:8823/Player.aspx?Recurso=Tablero1%20OfficeMax&idoficina=1&idtablero=1&fullscreen=1

from App.AppFrames.Controllers.Printers import NCR7197
from App.AppFrames.Controllers.Printers import TM_T88V





def main():
    #printer_1 = NCR7197.Printer({"NombrePuerto": "USB"})
    printer_2 = TM_T88V.Printer({"NombrePuerto": "/dev/ttyUSB0",
    "Baudios": 9600,
    "Paridad": "N",
    "BitsParada": 1,
    "BitsDatos": 8})
    
    a = (b"\x1Dd\x05")

    a_1 = (b"\x1bL\x1bW\x00\x00\x00\x00\x00\x02>\x03\x1bT\x02"+ #inicializar
        b"\x1D\x5C\x40\x02"+ #Impresión vertical relativa
        b"\x1d/3"+ #Imprimir Logo 
        b""+
        b"\x1bW\x00\x00\x00\x00\x00\x02>\x03"+
        b"\x1bt\x02"+  #Caracteres multilengua
        b"\x1bT\x02"+ #Impresión vertical relativa
        b"\x1b2\x1b!\x00"+ #Caracteres y fuente
        b"\x1bD\x13\x00"+ #Posiciones de Tab
        b"\x1d\x5c\00\x00\x1b!0"+ #Posicicion y fuente
        b"Linea1\nLinea2\nLinea3"+
        b""+
        b"\xFF")
    a_2 = (b"\x1bL\x1bW\x00\x00\x00\x00\x00\x02>\x03\x1bT\x03"+ #inicializar
        b"\x1D\x5C\x40\x02"+ #Impresión vertical relativa
        b"\x1d/3"+ #Imprimir Logo 
        b"\x1bW\x00\x00\x00\x00\x00\x02>\x03"+
        b"\x1bt\x02"+  #Caracteres multilengua
        b"\x1bT\x02"+ #Impresión vertical relativa
        b"\x1b2\x1b!\x00"+ #Caracteres y fuente
        b"\x1bD\x13\x00"+ #Posiciones de Tab
        b"\x1d\\(\x00\x1b!0"+ #Posicicion y fuente
        b"Linea1\n\nLinea2\n"+
        b""+
        b"\x1b\x0c\x1dV\x01")
    #printer_2.imprimir("Linea1\nLinea2\nLinea3\nLinea4\nlinea5\nlinea6") #,"/home/luis/Descargas/logo_ciel.bmp"
    
    printer_2.imprimir("PruebaTurno\nLinea1\nLinea2")
    printer_2.printer.write(a_2)


if __name__ == "__main__":
    main()