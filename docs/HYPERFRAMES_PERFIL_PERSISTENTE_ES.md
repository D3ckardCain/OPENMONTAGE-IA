# HyperFrames: selección offline persistente — #132

26-11-2026. Continúa f1dddfa sin repetir el piloto, doctor completo, hashes de
GSAP ni renders. Adaptador0.3.2. Paquete0.9.96, Node22.23.5, Chrome y GSAP3.14.2
existentes reutilizados; sin npm/npx, descargas ni instalaciones.

## Contrato compartido

Studio guarda un perfil explícito en `.backlot/studio/hyperframes_profile.json`:
node, browser, package_dir, gsap_package_dir y scratch, todos absolutos y existentes.
No se publica ese archivo privado. La selección real apunta a los recursos
preparados bajo HERRAMIENTAS/.runtime/hyperframes-0.9.96, **no a carpetas QA**.
No hay ruta QA codificada en la solución ni dependencia de variables heredadas.
Los demás settings y perfiles se conservan.

- GET `/api/studio/hyperframes/profile`: selección/revisión/disponibilidad.
- POST misma ruta con `{profile,revision}`: selecciona con control de revisión;
  selección idéntica es idempotente. No descarga ni ejecuta CLI.
- POST `/api/studio/hyperframes/profile/probe` con `{}`: comprueba únicamente
  `node <entry-local> --version`, hasta15s, guarda recibo ligado a identidades
  de recursos y revisión. Sin doctor/render; tareas activas bloquean cambios.

Aplicaciones → «HyperFrames · perfil offline explícito» permite consultar,
guardar y comprobar. Errores conservan campos. Ante respuesta incierta consultar
el perfil antes de reenviar; no hay retry automático. La disponibilidad por
perfil declara `selected_profile_cli_execution`, `cli_probe_status=not_run` y
`render_validated=false`: **ejecución comprobada no equivale a doctor o render nuevo**.
Un cambio en recursos invalida el recibo, sin rehacer hashes automáticamente.

El adaptador nativo HyperFramesCompose consume la misma selección en el puente
del agente. Forma un entorno hijo; no modifica os.environ de Studio. Node,
paquete, navegador y GSAP se seleccionan explícitamente y el guard offline se
carga en el hijo. El scaffold usa GSAP local seleccionado, sin fallback CDN.
El modo normal anterior sin selección conserva su contrato de doctor explícito.

## Puente existente, sin argumento de archivo QA

```powershell
& .\.venv\Scripts\python.exe -B scripts/run_hyperframes_offline.py --inspect-profile
```

Es lectura de disponibilidad, sin pipeline/generación. Para una tarea de pipeline
ya autorizada, el mismo launcher acepta project/stage/tool/inputs como antes y
usa por defecto la selección de Studio. `--profile` sigue admitiéndose como
override explícito **solo del hijo**, sin sustituir la selección persistida.
Los eventos de red del hijo de producción conservan log dentro de artifacts.
No ejecutar otra vez la fase render del piloto completado.

## Evidencia y alcance

- Once pruebas nuevas focalizadas: persistencia, revisión, idempotencia,
  entorno padre intacto, recursos inválidos/cambiados, recibo de ejecución,
  guard Windows y override de hijo sin heredar prueba ajena. Una regresión
  existente ajustada al parámetro opcional de resolve y ejecutada focalmente.
- El primer intento real identificó un fallo Windows: Node interpretaba las
  barras invertidas de NODE_OPTIONS como escapes y no encontraba el guard.
  Se corrigió con ruta portable, conservando el bloqueo de red del hijo.
- CLI0.9.96 ejecutado correctamente mediante perfil seleccionado; disponibilidad
  nativa available. Entorno padre comparado, sin cambios. Sin repetir doctor.
- Chrome/API reales en instancia aislada4766: selección guardada recuperada,
  save idempotente, ruta inválida400 conserva formulario, consulta recupera la
  selección original; catálogo available. No otro probe ni render desde navegador.
- Launcher normal `--inspect-profile`, sin variables HF ni `--profile`, confirma
  selección Studio y available. No usa una ruta de configuración QA permanente.

**Activación4750 pendiente de agrupar:** el proceso del usuario no se reinició.
Las rutas/UI nuevas requieren cargar esta entrega; no se atribuye a4750 la
validación de4766. El perfil ya queda preparado para el arranque normal, sin
exportar variables ni reinstalar. Comprobar salud/identidad y catálogo tras esa
activación; no repetir piloto/render/síntesis/doctor/hashes aprobados. PR2 borrador.
HTTP10054 conserva su seguimiento; no se hicieron diagnósticos de red extensos.
