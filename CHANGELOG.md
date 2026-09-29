# Versión 2.2 

**Versión actual X86_64:** ![version](https://img.shields.io/badge/C--Media_Player_Linux-2.2-orange?style=flat-square)

---

## Hitos

* **27-Abr-2026:**

  * Mejoras en el puente JS y `WebView`.
  * Ajustes en la lógica de impresión.
  * Nueva conexión de eventos.
  * Correcciones en la comunicación del `JSBridge`.

* **28-Abr-2026:**

  * Adaptación y conexión del controlador Honeywell 3320g.
  * Pruebas de comunicación con lector.

* **30-Abr-2026:**

  * Adaptación y depuración del Lector Universal.
  * Configuración y pruebas del lector Newland para lectura de cédulas nuevas.
  * Cambios de visualización gráfica para ARM64.

* **14-May-2026:**

  * Correcciones del Lector Universal.
  * Incorporación de lectura de cédulas nuevas.
  * Mejoras en la interfaz de configuración.

* **15-May-2026:**

  * Correcciones relacionadas con `Ticket Null`.

* **25-May-2026:**

  * Correcciones en Universal Printer y Universal Reader.
  * Ajustes en el tamaño del papel de impresión.

* **26-May-2026:**

  * Correcciones para lectura de cédulas nuevas.
  * Correcciones para lectura de documentos de extranjería.
  * Pruebas de impresión.

* **29-May-2026:**

  * Corrección de impresión de códigos QR en tickets.

* **01-Jun-2026:**

  * Mejoras en la estructura del ticket.
  * Correcciones de cortes de texto y saltos de línea.

* **17-Jun-2026:**

  * Actualización de dependencias del proyecto.
  * Incorporación de `PyInstaller` a los requerimientos.

* **23-Jun-2026:**

  * Limpieza y reorganización de la arquitectura.
  * Ajustes para preparación de producción.

* **10-Jul-2026:**

  * Cambios en iconos y elementos visuales.
  * Ajustes relacionados con controladores y aceptación de certificados.

* **14-Jul-2026:**

  * Correcciones del ticket en Universal Printer.
  * Correcciones de posiciones de bytes y logo en impresión.
  * Corrección del corte de impresión.

* **17-Jul-2026:**

  * Actualización del puente para comunicación con servidores.
  * Correcciones en tamaños de impresión.
  * Eliminación de alertas de prueba en `JSBridge`.

* **22-Jul-2026:**

  * Correcciones de importaciones relativas.
  * Correcciones en generación de logs.
  * Ajustes de tamaño del ticket y corte.
  * Correcciones de impresión en líneas específicas.

* **31-Jul-2026:**

  * Correcciones de comunicación del Bridge con servidores.
  * Eliminación de redundancias.
  * Implementación de nueva `TitleBar`.
  * Actualización visual de `MainFrame`, `WebTabFrame`, `GeneralTabFrame`, `PrinterTabFrame` y `CodeReaderTabFrame`.

* **10-Ago-2026:**

  * Actualización de interfaces.
  * Mejoras de interacción y navegación.
  * Implementación de detección de pantalla.

* **12-Ago-2026:**

  * Correcciones en lectores de códigos.
  * Correcciones en `Event.py` y Universal CodeReader.
  * Implementación de acciones `closeApp`.

* **19-Ago-2026:**

  * Refactorización de `WebTabFrame`.
  * Correcciones en `MainFrame`.
  * Corrección del archivo `.spec` utilizado para generar el instalador.

* **20-21-Ago-2026:**

  * Correcciones relacionadas con pantallas.
  * Correcciones de gestión y rotación de pantalla.

* **01-Sep-2026:**

  * Correcciones de audio.
  * Correcciones relacionadas con audio y pantalla táctil.

* **04-Sep-2026:**

  * Correcciones en `SpeechSynthesis`.
  * Mejoras en la comunicación y manejo del audio.
  * Refactorización de la gestión de la cola de síntesis de voz.

---

## ✨ Features

* Comunicación entre `JSBridge`, `WebView` y servidores.
* Universal Printer.
* Universal Reader.
* Lectura de cédulas nuevas y documentos de extranjería.
* Detección y gestión de pantallas.
* Nueva barra de título (`TitleBar`).
* Acciones `closeApp`.
* Generación de instaladores mediante `PyInstaller`.
* Sistema de síntesis de voz (`SpeechSynthesis`).
* Gestión de cola de síntesis de voz.
* Reproducción y manejo de audio.
* Mejoras en la interfaz gráfica.
* Optimización de la estructura interna del proyecto.

---

## 🔧 Fix

| Tipo         | Descripción                                                              |
| ------------ | ------------------------------------------------------------------------ |
| 🔴 Crítico   | Correcciones en la comunicación entre `JSBridge`, `WebView` y servidores |
| 🔴 Crítico   | Correcciones de lectura de cédulas y documentos de extranjería           |
| 🔴 Crítico   | Correcciones de impresión y corte de tickets                             |
| 🟠 Tolerante | Correcciones de Universal Printer                                        |
| 🟠 Tolerante | Correcciones del Universal Reader                                        |
| 🟠 Tolerante | Correcciones de generación de logs                                       |
| 🟠 Tolerante | Correcciones de gestión de pantallas                                     |
| 🟠 Tolerante | Correcciones relacionadas con audio                                      |
| 🟢 Mejora    | Refactorización de `WebTabFrame`                                         |
| 🟢 Mejora    | Nueva `TitleBar`                                                         |
| 🟢 Mejora    | Detección de pantallas                                                   |
| 🟢 Mejora    | Acciones `closeApp`                                                      |
| 🟢 Mejora    | Refactorización de `SpeechSynthesis`                                     |
| 🟢 Mejora    | Gestión de la cola de síntesis de voz                                    |
| 🟢 Mejora    | Mejoras en manejo y reproducción de audio                                |
| 🟢 Mejora    | Incorporación de `PyInstaller`                                           |

[ 🟢 Mejora ] [ 🟠 Tolerante ] [ 🔴 Crítico ]

---

## 📄 Documentación

* Manual Actualizado de Instalación y Configuración de C-Media Player (Versión 2.2).

---

## Autores 🚀

* @n.luque (Desarrollo, integración, análisis, codificación y debug)




 
