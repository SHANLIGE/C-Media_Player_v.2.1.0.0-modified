from App.AppFrames.Controllers.Printers.Printers import get_impresoras

printers = get_impresoras()

printer = printers["SAT"]["import"]({"NombrePuerto": "USB"})
text = "Bienvenido\nPrueba Linux 2022\n"
for i in range(2, 14):
    if i == 10:
        text += "A020\n"
    else:
        text+="Lin"+str(1+i)+"\n"
printer.imprimir(text+"https://www.muylinux.com/2021/11/09/microsoft-dotnet-6/","/home/luis/Descargas/logo_ciel.bmp")