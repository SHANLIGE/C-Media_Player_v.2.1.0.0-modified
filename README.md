
# C-Media Player Linux X86_64 / ARM64

## Descripción

El propósito del desarrollo en el presente repositorio es ofrecer un reproductor de C-Media que pueda ser instalado en Ubuntu/Linux. El reproductor utiliza el control navegador de C-Media a través del cual se accede al despliegue de un Player/Windows. Además, se ofrece la posibilidad de usar impresoras seriales y lectores.

Versión actual: 2.2

---

## Pre-requisitos

![ci](https://img.shields.io/badge/ubuntu-20.04-red)

Qt WebEngine 6 — https://doc.qt.io/qt-6/qtwebengine-index.html

```bash
sudo apt install libxcb-cursor0
sudo apt-get install libxcb-xinerama0
sudo apt-get install libwebp7
sudo ln -s /usr/lib/aarch64-linux-gnu/libwebp.so.7 /usr/lib/aarch64-linux-gnu/libwebp.so.6
```

![ci](https://img.shields.io/badge/Python-3.10-3670A0?logo=python&logoColor=ffdd54)

---

## Instrucciones para ejecutar en debug

```bash
cd cmediaplayerlinux/cod/C-Media_Linux_player-master
python3 -m venv entornoVirtual
source entornoVirtual/bin/activate
pip install -r requerimientos.txt
cd App
```

Ejecutar configuración:
```bash
python3 -m App.App.py --config
```

Ejecutar Player:
```bash
python3 -m App.App.py
```

---

## Archivos de configuración

La app espera estos archivos en `~/.config/Ciel/C-Media_Player/`. Son indispensables para que corra el programa.

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

Si "Ruta" en config.json empieza con $, se trata como variable de entorno. Ejemplo: `$HOME/pantallas.json`

---

## Diferencias entre la versión x86_64 y ARM64

En ARM64/Linaro hay que agregar las variables de entorno para el driver de video:

```bash
LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=xcb python3 App.py
```

La versión ARM64 (rama arm64-version) tiene estos cambios respecto a main:

**App.py:**
- Detección automática de arquitectura con platform.machine()
- Se agrega sys.path.insert(0, APP_DIR) al inicio para que los imports funcionen correctamente. En ARM64/Linaro el resolver de módulos relativos falla cuando se corre el script directamente.
- Se agregan flags de Chromium adicionales cuando se detecta ARM: --disable-gpu --no-sandbox --disable-dev-shm-usage. Sin esto QtWebEngine mata el proceso de render al arrancar.
- Se fuerzan las variables QT_QUICK_BACKEND=software y LIBGL_ALWAYS_SOFTWARE=1 en ARM para evitar pantalla negra con drivers Mesa/Rockchip incompletos.
- El directorio de logs se crea automáticamente con os.makedirs(..., exist_ok=True) porque en Linaro fresh install no existe y la app crasheaba silenciosamente antes de mostrar nada.
- QApplication recibe argv correctamente en vez de llamarse sin argumentos.

**Player.py:**
- El atributo self.close fue renombrado a self._closing. En versiones recientes de PySide6 el nombre close colisiona con el método heredado de QWidget y rompe el evento de cierre.
- Se agrega time.sleep(0.2) en el hilo print_screens para evitar busy-wait. En CPUs ARM de baja potencia (Cortex-A53/A72) el hilo sin sleep agota un núcleo completo e impacta la UI.
- El hilo se marca como daemon=True para que muera con el proceso principal y no deje la app colgada.
- qApp fue reemplazado por QApplication.instance() porque qApp es un alias obsoleto que no siempre está disponible en builds de PySide6 para Linux ARM.

---

## Render QtWebEngine en ARM64

Agregar a QTWEBENGINE_CHROMIUM_FLAGS:
```
--disable-gpu --no-sandbox --disable-dev-shm-usage
```

Setear variables de entorno:
```
LIBGL_ALWAYS_SOFTWARE=1
QT_QUICK_BACKEND=software
```

---

## Empaquetar con PyInstaller

Se usa un archivo .spec para controlar el empaquetado:

```bash
pyinstaller CMediaPlayer.spec
```

Las librerías de Qt están excluidas de UPX porque en ARM64 UPX las corrompe:

```
upx_exclude=["libQt6*.so*", "libPySide6*.so*", "Qt6*.so*"]
```

---

## Hardware probado en ARM64

- Placa: Rockchip RK3399 / RK3588 con Linux Linaro
- Display: HDMI, identificado como :0.0 en X11
- Lector de códigos: Comunicación por puerto /dev/ttyACM0 serial
- Impresora: Comunicación por puerto /dev/ttyUSB0 serial
- Python: 3.10
- PySide6: 6.8.0.2

El hilo print_screens en Player.py monitorea si la pantalla se desconecta y reconecta verificando el nombre del display. En Linaro la pantalla aparece como :0.0 cuando está conectada. Si cambia de nombre, el hilo detecta la desconexión y al volver llama showFullScreen() después de 0.5 segundos.
<img width="599" height="333" alt="Captura desde 2026-05-06 11-08-50" src="https://github.com/user-attachments/assets/e65c64c8-b1e1-4c50-9b2e-587a58720aa0" />
<img width="599" height="333" alt="Captura desde 2026-05-06 11-08-44-1" src="https://github.com/user-attachments/assets/e01f5780-792a-4116-bca7-d7277cb1262e" />
<img width="599" height="333" alt="Captura desde 2026-05-06 11-08-44" src="https://github.com/user-attachments/assets/10f89907-b3bb-4917-b08b-56e2a88dd5b3" />
<img width="599" height="333" alt="Captura desde 2026-05-06 11-08-34" src="https://github.com/user-attachments/assets/8b453d86-555a-4345-906a-a9c966c0fdf5" />
<img width="499" height="525" alt="Captura desde 2026-04-22 12-17-11" src="https://github.com/user-attachments/assets/26462504-fe7b-482e-93f3-ab5cd35e30cc" />
<img width="499" height="525" alt="Captura desde 2026-04-22 12-17-03" src="https://github.com/user-attachments/assets/2827b60e-d597-4d2a-87c2-a8f0ffaed932" />

---

## Información técnica

- SOLID
- POO
- Abstracción (Interfaces)

---

## Documentos complementarios

| Documento | |
|:---|:---|
| Manual de Configuración Certificado SSL | Docs/Configurar certificado autofirmado - Player Linux.docx |

