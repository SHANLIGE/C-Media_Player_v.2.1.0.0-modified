<img width="202" height="52" alt="SplashScreen" src="https://github.com/user-attachments/assets/d935eda8-a7c8-4838-be7e-5920157eb28f" />


![C-Media](https://img.shields.io/badge/C--Media-Software-orange?style=for-the-badge)
# C-Media Player
### Linux — X86_64 / ARM64

C-Media® Software permite desplegar contenidos dinámicos en pantallas instaladas en el mismo lugar o distribuidas en diferentes ubicaciones, sincronizando la reproducción de experiencias digitales para la audiencia.

## Descripción

El reproductor C-Media Linux es la herramienta desarrollada por Ciel Ingeniería que facilita la visualización de señalización digital en dispositivos con Ubuntu/Linux. Utiliza el control navegador de C-Media a través del cual se accede al despliegue de un Player/Windows, con soporte nativo para impresoras seriales y lectores de códigos de barras.



**Versión actual X86_64:** ![version](https://img.shields.io/badge/C--Media_Player_Linux-2.2-orange?style=flat-square)
**Versión actual ARM64:** ![version](https://img.shields.io/badge/C--Media_Player_Linux-1.0-orange?style=flat-square)

- [Changelog](#)
- [Información de arquitectura ARM64](#)
- [Estrategia de empaquetado con PyInstaller](#)



![ubuntu](https://img.shields.io/badge/Ubuntu-22.04-E95420?logo=ubuntu&logoColor=white)
![python](https://img.shields.io/badge/Python-3.10-3670A0?logo=python&logoColor=ffdd54)
![pyside6](https://img.shields.io/badge/PySide6-6.8.0.2-41CD52?logo=qt&logoColor=white)
![arch-x86](https://img.shields.io/badge/x86__64-supported-blue)
![arch-arm](https://img.shields.io/badge/ARM64-supported-blueviolet)



## Documentos complementarios 

| Documento | |
|:---|:---|
| Manual de Configuración Certificado SSL | `Docs/Configurar certificado autofirmado - Player Linux.docx` |
| Requerimientos del sistema | `Docs/Requerimientos.pdf` |



### Pre-requisitos ​📋​


- Ubuntu 20.04 o superior
- Python 3.10
- PySide6 con soporte Qt WebEngine 6 — https://doc.qt.io/qt-6/qtwebengine-index.html
- Dependencias del sistema:
```bash
sudo apt install libxcb-cursor0
sudo apt-get install libxcb-xinerama0
sudo apt-get install libwebp7
sudo ln -s /usr/lib/aarch64-linux-gnu/libwebp.so.7 /usr/lib/aarch64-linux-gnu/libwebp.so.6
```

## Información técnica ​

### Lenguajes

- Python 3.10
- JavaScript (Qt WebEngine / C-Media Web)
- Bash (scripts de entorno)

### Arquitectura

- Aplicación de escritorio Qt (PySide6)
- Navegador embebido con Qt WebEngine
- Módulo de periféricos (impresora tèrmica, lector de códigos)

### Patrones usados

- POO
- SOLID
- Abstracción (Interfaces)
- Arquitectura por capas

## Otros conceptos

- Hilos de fondo (daemon threads)
- Detección automática de arquitectura (`platform.machine()`)
- Monitoreo de display en tiempo real
- Variables de entorno condicionales por plataforma
- Empaquetado con PyInstaller (`.spec` personalizado)

## Diferencias ARM64 vs X86_64

En ARM64/Linaro se requieren variables de entorno adicionales para el driver de video:

```bash
LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=xcb python3 App.py
```

**App.py (rama arm64-version):**
- Detección automática de arquitectura con `platform.machine()`
- `sys.path.insert(0, APP_DIR)` para resolver imports correctamente en ARM
- Flags de Chromium adicionales: `--disable-gpu`, `--no-sandbox`, `--disable-dev-shm-usage`
- Forzado de `QT_QUICK_BACKEND=software` y `LIBGL_ALWAYS_SOFTWARE=1`
- Creación automática del directorio de logs con `os.makedirs(..., exist_ok=True)`

**Player.py (rama arm64-version):**
- `self.close` renombrado a `self._closing` para evitar colisión con `QWidget.close()`
- `time.sleep(0.2)` en hilo `print_screens` para evitar busy-wait en CPUs ARM
- Hilo marcado como `daemon=True`
- `qApp` reemplazado por `QApplication.instance()`


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

> Si el campo "Ruta" en `config.json` empieza con `$`, se interpreta como variable de entorno. Ejemplo: `$HOME/pantallas.json`



## Instalación

### Modo debug 

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

### Empaquetar con PyInstaller 

```bash
pyinstaller CMediaPlayer.spec
```

**Hidden imports requeridos (no detectados automáticamente):**

```
serial, serial.serialposix, serial.serialutil, serial.tools.list_ports,
serial.tools.list_ports_posix, PySide6.QtWebEngineCore,
PySide6.QtWebEngineWidgets, cryptography.fernet, cv2, netifaces, psutil, gtts
```

**Librerías excluidas de UPX (ARM64 las corrompe):**

```
upx_exclude=["libQt6*.so*", "libPySide6*.so*", "Qt6*.so*"]
```

### Recomendaiones | Aclaraciones ​📢​

- En ARM64 verificar que las variables de entorno estén configuradas antes de lanzar el ejecutable
- En modo debug, si no aparece la ventana en Linaro, revisar que el display `:0.0` esté disponible
- El directorio de logs debe existir antes de ejecutar (en ARM64 se crea automáticamente)



## Visuals 

<img width="299" height="133" alt="Captura desde 2026-05-06 11-08-34" src="https://github.com/user-attachments/assets/8b453d86-555a-4345-906a-a9c966c0fdf5" />
<img width="299" height="133" alt="Captura desde 2026-05-06 11-08-44" src="https://github.com/user-attachments/assets/10f89907-b3bb-4917-b08b-56e2a88dd5b3" />
<img width="299" height="133" alt="Captura desde 2026-05-06 11-08-50" src="https://github.com/user-attachments/assets/e65c64c8-b1e1-4c50-9b2e-587a58720aa0" />
<img width="199" height="225" alt="Captura desde 2026-04-22 12-17-03" src="https://github.com/user-attachments/assets/2827b60e-d597-4d2a-87c2-a8f0ffaed932" />
<img width="199" height="225" alt="Captura desde 2026-04-22 12-17-11" src="https://github.com/user-attachments/assets/26462504-fe7b-482e-93f3-ab5cd35e30cc" />


## Autores 🖌️

- **Andrés Mauricio Gómez** (Actualización)
- **@n.luque** (Desarrollo, codificaciòn, Bugs)


