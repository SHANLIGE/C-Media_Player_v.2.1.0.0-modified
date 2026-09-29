# Versión 2.2 (Actualizada) (29-Sep-2026)

**Versión actual X86_64:** ![version](https://img.shields.io/badge/C--Media_Player_Linux-2.2-orange?style=flat-square)
**Versión actual ARM64:** ![version](https://img.shields.io/badge/C--Media_Player_Linux-1.0-orange?style=flat-square)

---

## Hitos

* **27-Abr-2026:**

  * Mejoras en el puente JS y WebView.
  * Ajustes en la lógica de impresión.
  * Nueva conexión de eventos.
  * Actualización de la conexión JSBridge.

* **28-Abr-2026:**

  * Adaptación y conexión del controlador Honeywell 3320g.
  * Pruebas de comunicación con lector.

* **30-Abr-2026:**

  * Creación y depuración del Driver de Impresora Universal.
  * Creación y depuración del Driver de Lector Universal.
  * Compilación gráfica para arquitectura ARM64.
  * Configuración del lector Newland para lectura de cédulas nuevas.

* **11-May-2026:**

  * Implementación de configuración de terminales.
  * Configuración de lectores.
  * Integración de cambios de arquitectura ARM64.

* **14-May-2026:**

  * Correcciones y estabilización del Lector Universal.
  * Correcciones y estabilización de la Impresora Universal.
  * Configuración y conexión de terminales.
  * Implementación de configuración de la barra de navegación.
  * Persistencia de configuraciones de terminales.

* **15-May-2026:**

  * Correcciones relacionadas con `Ticket Null`.

* **25-May-2026:**

  * Correcciones en Universal Printer y Universal Reader.
  * Mejoras en tamaño de papel.
  * Correcciones para lectura de cédulas nuevas y documentos de extranjería.

* **29-May-2026:**

  * Corrección de impresión de códigos QR en tickets.

* **01-Jun-2026:**

  * Mejoras en estructura del ticket.
  * Correcciones de cortes de texto y saltos de línea.

* **17-Jun-2026:**

  * Actualización de dependencias del proyecto.
  * Incorporación de PyInstaller a los requerimientos.

* **23-Jun-2026:**

  * Limpieza y reorganización de la arquitectura.
  * Ajustes para preparación de producción.

* **25-Jun-2026:**

  * Actualización de requerimientos y configuración de `.gitignore`.

* **01-Jul-2026:**

  * Actualizaciones visuales de la interfaz.

* **08-Jul-2026:**

  * Mejoras visuales de la interfaz.
  * Actualización de botones y elementos de UI.

* **10-Jul-2026:**

  * Actualización de iconos.
  * Correcciones relacionadas con controladores.
  * Ajustes para aceptación de certificados.

* **14-Jul-2026:**

  * Correcciones del sistema de impresión universal.
  * Ajustes de posiciones y logos en impresión.
  * Corrección del corte de impresión.

* **17-Jul-2026:**

  * Actualización del puente de comunicación con servidores.
  * Eliminación de alertas de prueba en JSBridge.
  * Mejoras en tamaños de impresión.

* **22-Jul-2026:**

  * Correcciones de importaciones relativas.
  * Corrección de generación de logs.
  * Correcciones en tamaño del ticket y corte.
  * Ajustes de variaciones horizontales y líneas de impresión.

* **24-Jul-2026:**

  * Corrección de impresión en arquitectura ARM64.

* **31-Jul-2026:**

  * Correcciones en comunicación del Bridge con los servidores.
  * Eliminación de redundancias.
  * Nueva barra de título (`TitleBar`).
  * Actualización visual de `MainFrame`.
  * Actualización visual de `TerminalTabFrame`.
  * Actualización visual de `CodeReaderTabFrame`.
  * Actualización visual de `PrinterTabFrame`.
  * Actualización visual de `GeneralTabFrame`.
  * Actualización visual de `WebTabFrame`.

* **10-Ago-2026:**

  * Cambios en interfaces.
  * Incorporación de botón para agregar URLs.
  * Implementación de scroll.
  * Detección de pantallas.

* **12-Ago-2026:**

  * Correcciones en lectores de códigos.
  * Correcciones relacionadas con terminales.
  * Correcciones en `Event.py` y `UniversalCodeReader`.
  * Eliminación de labels innecesarios.
  * Incorporación de acciones `closeApp`.

* **19-Ago-2026:**

  * Refactorización de `WebTabFrame` para mejorar distribución y funcionalidad.
  * Correcciones en `MainFrame`.
  * Correcciones del archivo `.spec` para generación del instalador.
  * Eliminación de labels de ayuda innecesarios.

* **20-Ago-2026:**

  * Correcciones relacionadas con múltiples pantallas.

* **21-Ago-2026:**

  * Correcciones de pantallas y rotación.

* **01-Sep-2026:**

  * Correcciones relacionadas con audio.
  * Correcciones de interacción entre audio y pantalla táctil.

* **04-Sep-2026:**

  * Correcciones en comunicación con el sistema de Speech.
  * Correcciones adicionales relacionadas con Speech.

---

## ✨ Features

* Conexión universal con servidores adaptados a Linux.
* Driver Universal para impresoras.
* Driver Universal para lectores.
* Compatibilidad con arquitectura ARM64 para tablets.
* Configuración de terminales PNP para arquitectura ARM64.
* Configuración de URLs para terminales desde el contenedor Web.
* Configuración y persistencia de terminales.
* Sistema de drivers universales para dispositivos de entrada y salida.
* Detección de pantallas.
* Soporte para múltiples pantallas.
* Manejo de rotación de pantalla.
* Scroll en interfaces.
* Gestión de URLs desde la interfaz.
* Acciones `closeApp`.
* Nueva barra de título personalizada.
* Actualización visual de las principales interfaces del sistema.
* Mejoras en comunicación entre JSBridge, WebView y servidores.
* Mejoras en generación y manejo de logs.
* Generación de paquetes mediante PyInstaller.
* Optimización del sistema para entornos Linux de bajos recursos.
* Soporte y mejoras para impresión en arquitectura ARM64.

---

## 🔧 Fix

| Tipo         | Descripción                                                           |
| ------------ | --------------------------------------------------------------------- |
| 🔴 Crítico   | Correcciones de comunicación entre JSBridge, WebView y servidores     |
| 🔴 Crítico   | Correcciones de comunicación con Speech                               |
| 🔴 Crítico   | Correcciones de lectura de cédulas nuevas y documentos de extranjería |
| 🔴 Crítico   | Correcciones de controladores de lectores                             |
| 🔴 Crítico   | Correcciones de impresión en ARM64                                    |
| 🟠 Tolerante | Correcciones de Universal Printer y Universal Reader                  |
| 🟠 Tolerante | Correcciones de tamaño de papel y tickets                             |
| 🟠 Tolerante | Correcciones de corte y saltos de línea en impresión                  |
| 🟠 Tolerante | Corrección de impresión de códigos QR                                 |
| 🟠 Tolerante | Correcciones de comunicación con pantallas                            |
| 🟠 Tolerante | Correcciones de rotación de pantalla                                  |
| 🟠 Tolerante | Correcciones relacionadas con audio y pantalla táctil                 |
| 🟠 Tolerante | Correcciones en `MainFrame` y `WebTabFrame`                           |
| 🟠 Tolerante | Correcciones de importaciones y generación de logs                    |
| 🟢 Mejora    | Detección y gestión de pantallas                                      |
| 🟢 Mejora    | Nuevas acciones `closeApp`                                            |
| 🟢 Mejora    | Nueva barra de título                                                 |
| 🟢 Mejora    | Actualización visual de interfaces                                    |
| 🟢 Mejora    | Mejoras en configuración de terminales                                |
| 🟢 Mejora    | Mejoras en Bridge y comunicación con servidores                       |
| 🟢 Mejora    | Refactorización de `WebTabFrame`                                      |
| 🟢 Mejora    | Actualización de dependencias y PyInstaller                           |
| 🟢 Mejora    | Mejoras de compatibilidad ARM64                                       |

[ 🟢 Mejora ] [ 🟠 Tolerante ] [ 🔴 Crítico ]

---

## 📄 Documentación

* Manual Actualizado de Instalación y Configuración de C-Media Player ARM64 (Versión 1.0).

---

## Autores 🚀

* @n.luque (Análisis, codificación, debug)
* @v.hernandez (Análisis, pruebas de hardware)

 
