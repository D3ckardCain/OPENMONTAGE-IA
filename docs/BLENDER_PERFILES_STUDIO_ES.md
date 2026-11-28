# Blender 4.5 LTS y5.3 portable: perfiles compartidos (#117)

Actualización: [selector activado en4750](ACTIVACION_117_129_ES.md), PID130700,
API contrato1 y control habilitado.4.5 sigue predeterminado; opción5.3 comprobada
sin guardar cambio global ni lanzar Blender. Los párrafos siguientes conservan
la evidencia histórica de provisión/pruebas aisladas, no el estado actual del panel.

Implementación y pruebas locales25–26-11-2026 UTC. La selección cambia una ruta
compartida por Studio y el agente; nunca abre otra versión como sustitución
silenciosa. **El servidor4750 no se reinició**: su selector permanece bloqueado
con aviso de activación pendiente. La selección funcional se comprobó contra
API real en servidor aislado4778, con copia de configuración y proyectos vacíos.

## Instalación realizada y conservación

ZIP oficial previamente publicado en#117: [Blender5.3.0 Windows x64](https://download.blender.org/release/Blender5.3/blender-5.3.0-windows-x64.zip),
425299259bytes, SHA256
`3ac567a63d59d9934f7b9213bfb27ba05760e1fb366f8f55c381573ec3eabfa8`.
Descarga única verificada antes de extraer7623entradas/992912801bytes en
directorio nuevo. Entradas del ZIP comprobadas para rechazar rutas absolutas,
traversal y symlinks. No instalador/MSI ni asociaciones de archivos.

| Perfil registrado | Ejecutable | Preferencias/complementos |
|---|---|---|
|`blender-4.5` · seleccionado|`D:\OPENMONTAJE-IA\HERRAMIENTAS\Blender\4.5.15\blender-4.5.15-windows-x64\blender.exe`|Preferencias4.5 existentes, Archimesh1.2.5 y MN4.5.11 conservados|
|`blender-5.3` · disponible|`D:\OPENMONTAJE-IA\HERRAMIENTAS\Blender\5.3.0\blender-5.3.0-windows-x64\blender.exe`|`D:\OPENMONTAJE-IA\HERRAMIENTAS\Blender\5.3.0\profile`, sin importar4.5|

ZIP retenido en `D:\OPENMONTAJE-IA\DESCARGAS_SOFTWARE\Blender\blender-5.3.0-windows-x64.zip`.
Registro local: `.backlot/studio/blender_profiles.json`; contiene rutas personales
y no se publica. La ruta activa original en applications.json conserva4.5.15.
SHA256 de settings/applications, preferencias4.5, archivos previos de Archimesh
y manifiesto MN4.5.11 comprobados sin cambios. Se respaldaron preferencias4.5
antes de arrancar5.3 en `.backlot/setup/blender-5.3.0/userpref-4.5-before.blend`.

Solo los procesos5.3 reciben `BLENDER_USER_RESOURCES`, `PYTHONNOUSERSITE=1`,
TEMP/TMP propios bajo profile/temp y eliminación de overrides heredados de
Python/Blender. No variables globales ni cambios de .venv/ComfyUI. Las dependencias
cp313 del perfil5.3 se mantienen separadas de cp311 de4.5; no se duplican pesos,
medios ni bibliotecas creativas.

## Uso en Studio después de una futura activación autorizada

Aplicaciones → Blender → **Versión de Blender** → elegir4.5/5.3 → **Usar esta
versión**. Guardar cambia únicamente la vinculación Blender compartida; no
ejecuta el programa ni afirma que un render esté validado. Abrir desde el
proyecto usa la vinculación seleccionada y su entorno. Archivos .blend originales
no se migran por seleccionar un perfil. No seleccionar versiones cambiando la
ruta manual de un backend anterior para eludir su aislamiento.

El catálogo puede cargarse de forma diferida en un servidor anterior y mostrar
ambos perfiles aunque sus rutas HTTP todavía sean antiguas. Por eso la interfaz
comprueba además un GET específico antes de habilitar la selección.404 muestra
activación pendiente; conexión incierta y contrato incompatible tienen mensajes
distintos. No reintento automático ni reinicio.4750/PID123920 siguió activo y el
selector nuevo quedó deshabilitado; cero POST en esa comprobación de solo lectura.

API:

```text
GET /api/studio/applications
GET /api/studio/applications/blender/profiles
POST /api/studio/applications/blender/profile {"profile_id":"blender-5.3"}
POST /api/studio/applications/blender/launch {"project_id":"ID","file":"assets/escena.blend","profile_id":"blender-5.3"}
```

Selección rechazada mientras producción/análisis estén activos. Rutas/perfiles
ausentes o inválidos no se sustituyen por PATH, BLENDER_PATH u otra versión.
El lanzamiento explícito por perfil no altera por sí solo la selección global.
Otras aplicaciones y llamadas sin profile_id conservan su contrato anterior.

## Uso por el agente y adaptador

`application_catalog` devuelve los mismos IDs, versiones, disponibilidad y
selección. `application_open_project_file` admite profile_id opcional para Blender;
se reutiliza el mismo lanzador/registro. `blender_world`0.4.0 admite:

```json
{"operation":"doctor","profile_id":"blender-5.3"}
```

Sin profile_id utiliza la ruta activa compartida; con ID desconocido falla.
Doctor acredita ejecutable, versión real/Python y directorio de usuario; rechaza
discrepancias con el perfil. No equivale a geometría/render aprobados.
Build/render transmiten versión esperada al runtime; este rechaza versiones
distintas/no admitidas antes de crear geometría. EEVEE4.5 y5.3 se seleccionan
explícitamente; curvas5.3 usan channelbags. Las muestras permanecen en
SceneEEVEE.taa_render_samples, cuya disponibilidad se comprobó realmente5.3.
El informe del runtime identifica versión y motor efectivos, no un nombre4.5
constante. Scripts automáticos de .blend deshabilitados y errores Python provocan
salida distinta de cero. No se ejecutaron build/render en esta entrega.

## Validación real y límites

- **Arranque headless/doctor5.3:** versión5.3.0, build02f0899d78e3, Python3.13.13,
  USER bajo profile aislado. CLI y salida0, sin .blend de proyecto ni render.
- **Blender-Skills** EL4CTEO@1a1cc6c49312f9f370aae86f52b7b907f29c94f6:
  seis APIs locales comprobadas (interfaz de nodos, channelbag, compositor,
  enum splat, export glTF comprimido y EEVEE). Prueba sintética de tres curvas
  sobre cámara inicial, eliminada/restaurada en memoria: mismos3objetos/1malla/
  2materiales/0acciones antes/después. No instalador global/MCP/scripts remotos
  ni suite de28skills ejecutados. Compatibilidad de este subconjunto, no de
  todos los flujos/exports/recursos externos.
- **Complementos5.3:** instalación offline desde ZIP existentes, sin repositorios
  remotos. Archimesh1.2.5:28clases registradas (`is_registered`); MN520.2.0
  habilitado, Scene.mn/Object.mn presentes. MN no expone lista classes en su
  módulo raíz: no se inventa conteo total. Imports biotite1.7.1, MDAnalysis2.10.0,
  NumPy2.3.4 y databpy correctos; rutas cp313 del perfil y Python incluido.
  No importación molecular, generación arquitectónica ni render.
- **Arranque con ventana:** background=false, una ventana con VIEW_3D,
  OUTLINER/PROPERTIES/DOPESHEET. Se cerró exclusivamente esa instancia nueva
  mediante temporizador del propio Blender. No revisión humana de aspecto ni
  interacción de paneles acreditada. En ese primer cierre Blender guardó su
  recuperación automática `quit.blend` en el temporal de Windows; no fue una
  exportación ni un proyecto del usuario. Después se aislaron TEMP/TMP de futuros
  procesos5.3 bajo profile/temp; no se borró el archivo global por rutina.
- **API/panel aislados4778:** dos POST reales de selección5.3→4.5 sobre copia
  de configuración; IDs confirmados, cero lanzamientos y errores JS. No usar
  ese resultado como activación4750. Su catálogo sí lista las dos versiones,
  pero el GET de contrato nuevo falta y su selector queda deshabilitado.
- **Pruebas nuevas:**14pytest de perfiles/errores/API/agente/entorno y ramas4.5/
  5.3/versión no admitida;3casos revalidados tras añadir contratoGET/aislamiento
  temporal/flags de lanzamiento. No suites antiguas repetidas. Sintaxis focalizada7Python/4JS aprobada.

Se corrigieron dos lectores de diagnóstico antes de obtener resultados válidos:
el runtime ejecutaba main al importarlo (ahora guardado por __name__) y la
comprobación inicial de Archimesh buscaba nombres Python en bpy.types en lugar
de is_registered. Esos fallos del diagnóstico no se presentan como fallos de
compatibilidad del complemento. El primer smoke de UI pulsó antes de estar
vinculado el handler; el smoke final espera su disponibilidad, sin ampliar timeout.

Evidencia detallada: [JSON](BLENDER_117_VALIDACION_20261126.json). El servidor
aislado se detiene al finalizar. Publicación solo código/pruebas/manual: sin
binarios, ZIP, perfiles personales, preferencias o .venv. PR#2 borrador, coste$0;
#112 y las acciones ocultas de#113 siguen pendientes. #117 conserva pendiente
activación4750, pruebas de uso de complementos/skills y QA sobre copias autorizadas.
