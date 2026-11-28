# HyperFrames: diagnóstico local, staging y audio — #132

Actualización26-11-2026 UTC: [preparación y piloto real](HYPERFRAMES_OFFLINE_PILOTO_ES.md).
Las afirmaciones de ausencia de preparación/render siguientes describen la
entrega anterior, no el estado actual.

## Cambio implementado

Disponibilidad de `hyperframes_compose`/`video_compose` ya no ejecuta `npm view`,
`npx`, el CLI, instaladores ni comprobaciones de updates. Lee manifests locales
y, si Node está en PATH, ejecuta únicamente `node --version` con límite5s.
No hay caché negativa permanente que obligue a reiniciar tras preparar recursos.
No modifica configuración, paquetes, preferencias del navegador ni archivos.

Se conserva el adaptador existente, sin runtime alternativo ni fallback.
Resolución única para diagnóstico/doctor/render en `lib/hyperframes_runtime.py`:

- Paquete preparado explícitamente mediante `HYPERFRAMES_PACKAGE_DIR`, o
  `node_modules/hyperframes`/`node_modules/@hyperframes/cli` del proyecto.
  No busca automáticamente versiones en cachés npx ni instala globalmente.
- `package.json` debe identificar HyperFrames, versión revisada **0.9.96** y
  `bin.hyperframes` existente dentro del paquete. Otra versión/incompleto falla
  de forma explícita; la versión observada es la del manifest local, no npm latest.
- Node>=22, FFmpeg **y FFprobe** por resolvedor multimedia existente.
  Navegador preparado declarado en `HYPERFRAMES_BROWSER_PATH`, sin auto-download.
- El comando usa `[node, entrada_local, ...argumentos]` en todas las operaciones.
  No ejecuta shims npm/npx. Variables de telemetría se desactivan solo en el hijo,
  rutas de medios guardadas se exponen en el entorno del hijo; configuración intacta.

Preparación significa reutilizar instalación/navegador existentes antes de
descargar otro. Esta entrega **no instala nada** ni declara ausentes recursos
fuera de las rutas revisadas. Las variables se indican como contrato del adaptador,
no como invitación a modificar globalmente el equipo.

## Instalado, disponible y render validado

`installed` acredita manifest/entry locales reconocidos. `local_requirements_met`
añade los requisitos anteriores; no acredita lanzamiento del navegador ni DLLs.
`runtime_available`/AVAILABLE requieren además un **doctor explícito** con resultado
vigente para esas identidades, durante60s y solo en ese proceso. Consultar estado
no lo ejecuta ni renueva. Cambios de archivos/rutas invalidan el resultado; fallo
explícito elimina un estado sano previo. Doctor se vuelve a solicitar expresamente.
`render_validated=false` no cambia por doctor.

Doctor interpreta JSON, no exit0 ni el `ok` global. Se exigen checks inequívocos
`Node.js`, `FFmpeg`, `FFprobe`, `Chrome`, `Memory`, `Disk`, `Frames cache`,
`Settings lock` y `/dev/shm` en Linux. Whisper, TTS, MusicGen, Docker, actualización
y paquetes opcionales se reportan separados, sin bloquear composición básica.
JSON ausente/desconocido, duplicados o fallos requeridos son errores claros.

El formato se contrastó con doctor/preflight upstream fijados en
[1e7d00496692d4c264ffeb59e85175752f39ea2d](https://github.com/heygen-com/hyperframes/tree/1e7d00496692d4c264ffeb59e85175752f39ea2d),
manifest0.9.96/Node>=22/Apache2.0. No se confirmó versión publicada o instalada
desde ese número. Las dependencias/GSAP/recursos mantienen licencias separadas.

## Medios y audio

`lib/hyperframes_staging.py` comparte copias entre vídeo, imágenes, narración y
música. Nombres `om-hf-<SHA256>.<ext>` evitan colisiones por basename/tamaño.
La misma fuente inalterada reutiliza la copia y hash sin nuevas lecturas:
se verifica ruta resuelta, dispositivo/inodo/tamaño/mtime/ctime y la identidad
del destino. Cambio invalida caché. Destino de contenido distinto se conserva y
produce error; archivos anteriores/ajenos no se sobrescriben ni limpian.
Una fuente nueva se hashea y copia; usa disco y lecturas, no se presenta como
deduplicación física o prueba contra manipulación deliberada de metadatos.

Volumen musical0 se conserva hasta `data-volume="0"` en el HTML, sin sustituirlo
por0.15. Valores inválidos se rechazan. El scaffold mínimo **no implementa fades**:
si se solicitan, devuelve error explícito antes de producir un HTML que los omita.
Preparar una mezcla local explícita con motores existentes es una tarea separada,
sin sustitución silenciosa de decisiones de audio.

## Pruebas y consulta real

23casos nuevos y5regresiones adaptadas al contrato (4disponibilidad y1scaffold),
aprobados por subconjuntos focalizados. Tras cada delta se repitió únicamente
el subconjunto afectado; no sumar ejecuciones repetidas como casos distintos.
Paquetes, salidas doctor y bytes de medios son sintéticos/offline. Prueban ausencia
de invocación CLI en catálogo, manifest/pin/entry/Node/FFprobe/browser, invalidación,
JSON requerido vs opcional, mismo resolvedor, colisiones/copia/caché, cero y fades.
Sin suite completa ni CI nueva afirmadas; sintaxis de los seis Python tocados válida.

Consulta real nueva: FFmpeg/FFprobe disponibles; paquete no configurado en las
rutas revisadas, Node no comprobable en este PATH y browser no declarado.
Cero subprocesses, npm/npx/CLI o descargas durante esa consulta. No confundir
alcance de entorno con ausencia global: Node/navegador existentes no se reinstalan.
[Evidencia](HYPERFRAMES_132_RESULTADOS.json).

## Límites y siguientes pasos

La reproducción/render real, seek/cancelación y escucha siguen pendientes de
preparación local explícita. No se ejecutó doctor upstream real por faltar esa
preparación. Los opt-outs no prueban ausencia total de tráfico de un CLI futuro.
El scaffold todavía referencia GSAP por CDN y registro upstream main; no se afirma
offline reproducible completo hasta fijar/localizar recursos y verificar egreso.
No se ejecutaron add_block, browser ensure, descargas, ASR, síntesis ni pilotos.
La carga de módulos nuevos en el servidor residente no se validó: agruparla con
próximas entregas si requiere activación, sin reiniciar por rutina.

Configuraciones/ComfyUI intactos;4.5 predeterminado y PR#2 en borrador, costo$0.
#132 conserva pendientes de recursos offline y validación AV; diagnóstico y
regresiones de staging/audio no equivalen a integración completamente validada.
