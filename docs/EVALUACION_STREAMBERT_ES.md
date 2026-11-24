# Evaluación Streambert — #77

Evaluación estática del 24-11-2026, vinculada a #3. Sin instalación, descargas audiovisuales ni ejecución del candidato.

## Fuentes y versión

Repositorio oficial: [truelockmc/streambert, revisión 270d5fa9fec9a846195b2e08df45c2d939863b64](https://github.com/truelockmc/streambert/tree/270d5fa9fec9a846195b2e08df45c2d939863b64). Se revisaron README, LICENSE, package.json, src/utils/backup.js, src/utils/storage.js y src/ipc/storage.js en esa revisión. package.json declara **2.7.0**; no se descargó un instalador ni se verificó su correspondencia binaria.

## Licencias, Windows y operación local

| Aspecto | Resultado |
|---|---|
| Código | GPL-3.0 declarada y texto GPL v3 incluido. La distribución de derivados/binarios requiere evaluar código correspondiente, avisos y dependencias; no copiar componentes a un producto con licencia incompatible. Uso interno y distribución son escenarios distintos. |
| Windows | Electron; README ofrece instaladores vía Codeberg. Compilación requiere Node >=22.12; package.json usa Electron ^45.2.1 y electron-builder ^26.18. El instalador no exige instalar Node al usuario. Compatibilidad práctica no probada en esta evaluación. |
| Función | Biblioteca, historial, progreso de reproducción y reproducción/descarga orientada a películas y anime. No aporta selección editorial, transcripción, montaje ni director multietapa. |
| Offline | Archivos locales y estado persistido pueden funcionar sin red; búsqueda, carteles, metadatos, proveedores y actualizaciones requieren red. No equivale a aplicación completamente offline. |
| Costo | El código es gratuito; eso no concede derechos sobre obras, fuentes ni datos externos. TMDB exige clave, atribución y licencia comercial separada para uso comercial. No se garantiza costo $0 para ese escenario. |
| Descargas | Usa descargador externo vid-dl-cli-only y FFmpeg. No adoptar otro descargador ni proveedores de streaming: OpenMontage ya tiene herramientas de adquisición y procedencia. |

[FAQ oficial de TMDB](https://developer.themoviedb.org/docs/faq): API gratuita con atribución para fines no comerciales; uso comercial requiere contactar al titular. Los términos de AniList no pudieron recuperarse (HTTP 403 en la fuente oficial); su elegibilidad queda **sin resolver**, no autorizada por la GPL de Streambert. No se consultaron catálogos ni se solicitó una clave.

## Comparación con OpenMontage

Ya existen biblioteca Backlot (`backlot/ui/library.js`), revisión de fuentes (`lib/source_media_review.py`), artefactos/procedencia y adquisición local. `backlot/ui/board.js` conserva posición y reproducción durante un refresco SSE cuando la fuente coincide. Esto no demuestra persistencia del progreso entre sesiones.

La única carencia potencial útil es **reanudar la revisión de archivos propios entre sesiones**, con historial opcional y exportación de estado. Prioridad baja dentro de E06, condicionada a necesidad de revisión prolongada; no crear biblioteca ni aplicación Electron paralela. No confundir progreso del reproductor con reanudación de trabajos E05.

El candidato permite respaldo por lista explícita de claves y excluye claves API de esa lista. Sin embargo, los respaldos contienen rutas e historial; no son datos publicables automáticamente. Su almacenamiento omite errores en algunas escrituras; su almacén de secretos dispone de fallback base64 y migración temporal en texto. No trasladar esos comportamientos como contrato de seguridad de Studio.

## Tareas y aceptación

| Backlog | Propuesta acotada | Aceptación futura |
|---|---|---|
| E06, baja | Marcador local por proyecto, identidad del archivo y usuario; posición de revisión, sin URL de proveedor | Con metadatos sintéticos: restaurar tras nueva sesión; invalidar al cambiar hash/duración; posición finita dentro del intervalo; distinguir borrado del historial de borrado del original. |
| E06 | Exportación opcional con versión de esquema y lista de campos | Importación rechaza versión/tipos inválidos; no incluye secretos ni rutas personales por defecto; falla explícitamente si no puede persistir; no sobrescribe configuración. |
| B07 | Metadatos o proveedores externos | Permanecen fuera del alcance hasta resolver licencias, términos, derechos y necesidad; ningún fallback de red implícito. |

No se recomienda integrar Streambert como aplicación ni reutilizar sus proveedores. Estas propuestas se incorporan al backlog existente sin duplicar E05/E06. Evaluación completada; implementación y prueba funcional del candidato no realizadas.
