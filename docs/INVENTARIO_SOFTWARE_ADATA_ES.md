# Inventario observado de software en ADATA

Seguimiento: [Issue #3](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/3).

Fuente: salida de PowerShell aportada por el usuario. Disco `D:` (`ADATA`, NTFS). Raíz del proyecto: `D:\OPENMONTAJE-IA`. No se han accedido ni ejecutado estos paquetes desde el entorno de desarrollo.

La consulta examinó archivos ZIP, 7z, RAR, EXE, MSI y MSIX hasta profundidad dos en `D:\OPENMONTAJE-IA\DESCARGAS_SOFTWARE`. Devuelve 22 archivos: 18 ZIP, un 7z y tres EXE. No es un inventario completo del disco ni acredita integridad, procedencia, instalación o compatibilidad. Las versiones indicadas pertenecen a los nombres de los archivos, sin validación interna. El tamaño mostrado como MB en PowerShell se calculó con `1MB` y corresponde a MiB aproximados, redondeados a una decimal.

| Carpeta | Archivo detectado | MiB aproximados |
|---|---|---:|
| Archimesh | `add-on-archimesh-v1.2.5.zip` | 0.3 |
| Avogadro | `Avogadro2-2.1.0-win64.exe` | 114.5 |
| Blender | `blender-4.5.15-windows-x64.zip` | 380.2 |
| Blender | `Rhubarb-Lip-Sync-1.14.0-Windows.zip` | 83.3 |
| cq_warehouse | `cq_warehouse-main.zip` | 2.9 |
| Feedparser | `feedparser-a22c5521cbb109871f1a2318948581901bd47e26.zip` | 1.3 |
| FreeCAD | `FreeCAD_1.1.4-Windows-x86_64-py311.7z` | 398.7 |
| FreeCAD-Fasteners | `FreeCAD_FastenersWB-master.zip` | 1.6 |
| FreeCAD-Gears | `freecad.gears-4164073946282ee6e88594b0f7d1774a60b04f76.zip` | 18 |
| Kinovea | `Kinovea-2025.2.0.zip` | 45.9 |
| Kloppy | `kloppy-master.zip` | 39.6 |
| Krita | `krita-x64-5.3.4.1.zip` | 217.2 |
| Molecular-Nodes | `add-on-molecularnodes-v520.2.0-windows-x64.zip` | 127 |
| MPLSoccer | `mplsoccer-main.zip` | 0.9 |
| MuseTalk | `MuseTalk-0a89dec45a0192b824e3cf4daf96c239440c5ed8.zip` | 15.2 |
| OpenModelica | `OpenModelica-v1.27.1-64bit.exe` | 1565.6 |
| OpenSCAD | `OpenSCAD-2021.01-x86-64.zip` | 20.9 |
| Soccer-Tactical-Vision | `soccer-tactical-vision-main.zip` | 2.4 |
| Socceraction | `socceraction-93a1242d46c104889205753accaabadb00c45c6d.zip` | 6.9 |
| SolveSpace | `solvespace_single_core_x64.exe` | 9.1 |
| Trafilatura | `trafilatura-9c27981f4b7034a3249c77c4c06aaaed719fae66.zip` | 30.4 |
| TVCalib | `tvcalib-main.zip` | 0.3 |

## Orden de preparación

1. Revisar `HERRAMIENTAS` para identificar ejecutables y aplicaciones ya extraídos, incluida una posible herramienta de extracción 7z. No duplicar ni reemplazar instalaciones existentes.
2. Revisar estructura interna y procedencia del paquete elegido antes de extraerlo o ejecutarlo; comprobar licencias y condiciones de uso.
3. Separar aplicaciones, complementos y librerías/código fuente. Un ZIP no demuestra por sí solo que sea portable; un EXE no se considera automáticamente instalador o portable.
4. Preparar cada integración por separado, conservando los paquetes originales y aislando dependencias. Antes de crear otra copia, comprobar el espacio necesario: el disco tenía 99 161 419 776 bytes libres al identificarse.
5. Validar comandos/API locales, progreso y resultados cuando corresponda; no equiparar ejecutable registrado con integración funcional.

## Otras carpetas observadas

El listado de `D:\OPENMONTAJE-IA` también muestra `BIBLIOTECAS_3D`, `BIBLIOTECAS_GEOGRAFIA`, `BIBLIOTECAS_TECNICAS`, `BIBLIOTECAS_VIDEO`, `ComfyUI_windows_portable`, `DESCARGAS_MODELOS`, `FUENTES_DOCUMENTALES` y `HERRAMIENTAS`. El inventario de paquetes aquí registrado solo cubre la consulta delimitada de `DESCARGAS_SOFTWARE`.
