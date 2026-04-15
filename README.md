
# C-Media Player Linux

### Descripción:

El Propósito del desarrollo en el presente repositorio ofrecer un reproductor de C-Media que pueda ser instalado en Ubuntu/Linux.
El reproductor utiliza el control navegador de C-Media a traves del cual se accede al despliegue de un Player/Windows, a demas, se ofrece la posibilidad de usar impresoras seriales, y lectores.

**Versión actual:** 
2.0


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
  
### Arquitectura
ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter



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


## Crear copia del repositorio con nuevo nombre

### Copia local

```bash
./scripts/crear_copia_engine.sh
```

### Publicar en GitHub

```bash
GITHUB_TOKEN=tu_token ./scripts/crear_copia_engine.sh --github TU_USUARIO_O_ORG
```

Esto crea (si no existe) y publica el repositorio privado `C-Media_Player_Engine` en GitHub con todo el historial.
