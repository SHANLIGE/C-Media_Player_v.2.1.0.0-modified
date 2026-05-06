
# C-Media Player Linux

### Descripción:

El Propósito del desarrollo en el presente repositorio ofrecer un reproductor de C-Media que pueda ser instalado en Ubuntu/Linux.
El reproductor utiliza el control navegador de C-Media a traves del cual se accede al despliegue de un Player/Windows, a demas, se ofrece la posibilidad de usar impresoras seriales, y lectores.

**Versión actual:** 
2.2


## Archivos de configuración

La app espera estos archivos en `~/.config/Ciel/C-Media_Player/`:

```
~/.config/Ciel/C-Media_Player/
├── configs/
│   └── config.json          -- Configuración general de la app
├── Media/
│   ├── SplashScreen.png     -- Pantalla de carga
│   └── Logo-CMedia_lx.png  -- Ícono de la ventana
└── logs/
    └── log.log              -- Archivo de logs
```
Estos archivos son indispensables para que corra el programa.

Si "Ruta" empieza con $, se trata como variable de entorno. Ejemplo: "$HOME/pantallas.json"





Resumen de dependencias Python:

- PySide6 6.8.x -- framework gráfico
- pyserial -- comunicación con lectores y impresoras por puerto serial
- cryptography -- manejo de credenciales (Fernet)
- gtts -- síntesis de voz (Google Text-to-Speech)
- psutil -- información del sistema
- netifaces -- información de interfaces de red
- opencv-python-headless -- procesamiento de imagen para lector de códigos

---

## Diferencias entre la versión x86_64 y ARM64

En ARM64/Linaro hay que agregar las variables de entorno para el driver de video:

```bash
LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=xcb python3 App.py --debug
```

```

En ARM64/Linaro también hace falta la librería del sistema libwebp. Si la versión disponible es libwebp7 y la app pide libwebp.so.6, se crea un symlink:

```bash
sudo apt-get install libwebp7
sudo ln -s /usr/lib/aarch64-linux-gnu/libwebp.so.7 /usr/lib/aarch64-linux-gnu/libwebp.so.6
```

La versión ARM64 (rama arm64-version) tiene estos cambios respecto a main:

En App.py:
- Detección automática de arquitectura con platform.machine()
- Se agrega sys.path.insert(0, APP_DIR) al inicio para que los imports funcionen correctamente. En ARM64/Linaro el resolver de módulos relativos falla cuando se corre el script directamente.
- Se agregan flags de Chromium adicionales cuando se detecta ARM: --disable-gpu --no-sandbox --disable-dev-shm-usage. Sin esto QtWebEngine mata el proceso de render al arrancar.
- Se fuerzan las variables QT_QUICK_BACKEND=software y LIBGL_ALWAYS_SOFTWARE=1 en ARM para evitar pantalla negra con drivers Mesa/Rockchip incompletos.
- El directorio de logs se crea automáticamente con os.makedirs(..., exist_ok=True) porque en Linaro fresh install no existe y la app crasheaba silenciosamente antes de mostrar nada.
- QApplication recibe argv correctamente en vez de llamarse sin argumentos.

En Player.py:
- El atributo self.close fue renombrado a self._closing. En versiones recientes de PySide6 el nombre close colisiona con el método heredado de QWidget y rompe el evento de cierre.
- Se agrega time.sleep(0.2) en el hilo print_screens para evitar busy-wait. En CPUs ARM de baja potencia (Cortex-A53/A72) el hilo sin sleep agota un núcleo completo e impacta la UI.
- El hilo se marca como daemon=True para que muera con el proceso principal y no deje la app colgada.
- qApp fue reemplazado por QApplication.instance() porque qApp es un alias obsoleto que no siempre está disponible en builds de PySide6 para Linux ARM.

---

## Empaquetar con PyInstaller

Se usa un archivo .spec para controlar el empaquetado. El comando es:

```bash
pyinstaller CMediaPlayer.spec
```

El .spec incluye estos hidden imports que PyInstaller no detecta automáticamente:

```
serial, serial.serialposix, serial.serialutil, serial.tools.list_ports,
serial.tools.list_ports_posix, PySide6.QtWebEngineCore,
PySide6.QtWebEngineWidgets, cryptography.fernet, cv2, netifaces, psutil, gtts
```

Las librerías de Qt están excluidas sobre UPX porque en ARM64 UPX las corrompe:

```
upx_exclude=["libQt6*.so*", "libPySide6*.so*", "Qt6*.so*"]
```


## Hardware probado en ARM64

- Placa: Rockchip RK3399 / RK3588 con Linux Linaro
- Display: HDMI, identificado como :0.0 en X11
- Lector de códigos: Honeywell 3320g y Magellan, conectados en /dev/ttyACM0 por serial
- Impresora: térmica por serial
- Python: 3.10
- PySide6: 6.8.0.2

El hilo print_screens en Player.py monitorea si la pantalla se desconecta y reconecta verificando el nombre del display. En Linaro la pantalla aparece como :0.0 cuando está conectada. Si cambia de nombre, el hilo detecta la desconexión y al volver llama showFullScreen() después de 0.5 segundos.

---

## Render QtWebEngine en Arm64

sudo --disable-gpu --no-sandbox --disable-dev-shm-usage a QTWEBENGINE_CHROMIUM_FLAGS.

sudo -- setear LIBGL_ALWAYS_SOFTWARE=1 y QT_QUICK_BACKEND=software.

### Documentos complementarios 📄

| Documento  | ![LogoGitLab](https://img.shields.io/badge/GitLab-FC6D26?logo=gitlab&logoColor=white)   |
|:---|     :---     | :---   |

| `🖼️Manual Configuracion Certificado SSL` | (Docs/Configurar certificado autofirmado - Player Linux.docx) | **N/A** | **N/A**


## Pre-requisitos 📋

* ![ci](https://img.shields.io/badge/ubuntu-20.04-red)
* Qt WebEngine 6
	https://doc.qt.io/qt-6/qtwebengine-index.html
	* Requerimientos:
	 `sudo apt install libxcb-cursor0`
	 `sudo apt-get install libxcb-xinerama0`
* 

## Información técnica 🔬
### Lenguajes 🧙

![ci](https://img.shields.io/badge/Phyton-3.10-3670A0?logo=python&logoColor=ffdd54)

### Otros conceptos
- SOLID
- POO
- Abstracción (Interfaces)



## Instrucciones para ejecutar en Debug 🚩

- `cd cmediaplayerlinux/cod/C-Media_Linux_player-master
`: Ubicarse en la carpeta correspondiente
- `python3 -m venv entornoVirutal`: Crear entorno virtual
- `source entornoVirutal/bin/activate`: Activar entorno virtual 
- `pip install -r requerimientos.txt`: Instalar requerimientos
- `cd App
`: Ubicarse en la carpeta para ejecutar la aplicación
- Ejecutar configuración `App.py -- debug --config`
- Ejecutar Player  `App.py -- debug`

