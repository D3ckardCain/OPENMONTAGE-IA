# Activación pendiente #174 — bloqueo de política, 26 noviembre 2026

La política de ejecución rechazó el comando que detenía exclusivamente Studio PID153088 en4750 y lo arrancaba desde `C:\OPENMONTAGE-IA\.venv`. Mensaje disponible: `blocked by policy`, sin razón adicional. La acción no se ejecutó; no se intentó otra vía. El servidor QA4766 ya está cerrado. El inventario y la recuperación de hashes ya terminaron; no se deben relanzar. Conserva las descargas y otros trabajos activos.

Antes del rechazo: worker inactivo, tarea local inactiva, cola pausada sin elementos. Se guardaron224 JSON de proyectos/configuración en una copia privada. El paquete se amplió después y debe activarse **una sola vez completo**, no por cada commit: sourceSHA256 esperado `d9838282b1f73383452a866414d90ca3635f98c4c39256277b8af13a83d72942`,49archivos; capabilities `layer_position_keyframes`, `layer_transform_keyframes`, `audio_balance`, `crossfade`, `sfx_catalog`/`sfx_favorites` y `audio_processing`, `track_mixer`, `audio_ducking`, `mix_meter`. La identidad UI se informa por separado. Las comprobaciones de trabajos deben ser actuales antes de ejecutar el bloque manual.

## Paso manual exacto

En PowerShell normal, ejecuta este bloque. Hace comprobaciones actuales, rechaza un propietario inesperado y detiene únicamente el servidor confirmado de4750. El último comando deja Studio en esa consola. No detengas otras consolas ni el proceso de hashes.

```powershell
Set-Location C:\OPENMONTAGE-IA
$studioIdentity = Invoke-RestMethod http://127.0.0.1:4750/api/studio/identity -TimeoutSec 10
$studioWork = Invoke-RestMethod http://127.0.0.1:4750/api/studio/queue/inspect -TimeoutSec 10
$studioQueue = Invoke-RestMethod http://127.0.0.1:4750/api/studio/queue -TimeoutSec 10
if (-not $studioIdentity.restart_required) { throw 'La instancia ya está actualizada; no reiniciar.' }
if ($studioWork.worker_active -or $studioWork.local_task_active -or @($studioQueue.items | Where-Object { $_.status -in @('running','starting') }).Count) { throw 'Hay trabajo activo; conservar Studio.' }
$studioListener = Get-NetTCPConnection -LocalPort 4750 -State Listen
if ($studioListener.OwningProcess -ne $studioIdentity.pid) { throw 'La identidad no coincide con el propietario del puerto.' }
$studioOwner = Get-CimInstance Win32_Process -Filter "ProcessId=$($studioListener.OwningProcess)"
if ($studioOwner.CommandLine -notlike '*-m backlot serve --port 4750*') { throw 'Propietario inesperado; no detener.' }
Stop-Process -Id $studioListener.OwningProcess
& .\.venv\Scripts\python.exe -B -m backlot serve --port 4750
```

Después, en otra consola, comprobación de solo lectura:

Recarga también la pestaña de Studio una vez (Ctrl+F5) para cargar los módulos del panel actualizado. El inventario/hashes ya están terminados y no necesitan otro reinicio ni repetición.

```powershell
Invoke-RestMethod http://127.0.0.1:4750/api/health -TimeoutSec 10
Invoke-RestMethod http://127.0.0.1:4750/api/studio/identity -TimeoutSec 10
Invoke-RestMethod http://127.0.0.1:4750/api/studio/editor/capabilities -TimeoutSec 10
```

Debe aparecer saludOK, `restart_required:false`, el sourceSHA256 esperado y las capabilities agrupadas. Eso acredita activación de backend, no escucha humana ni nueva exportación. No repetir las pruebas, renders o ciclos QA ya aprobados; solo comprobar presencia y funcionamiento pendiente en el panel principal con una copia.

La confirmacion del reinicio manual sigue pendiente: no ejecutar este bloque automaticamente ni consultar4750 antes de esa confirmacion. Entregas nuevas y evidencia: [mezclador exportado](EDITOR_MEZCLADOR_EXPORT_ES.md), [ducking](EDITOR_DUCKING_ES.md). Identidad UI actual esperada: `14f71fa542ab9c3a9801cd23811f91de4a7275c3785a96fb8e0769d47bbc4340`,41archivos. Las ocho descargas requieren otra confirmacion independiente; conservar Wan VACE Low valido.

La medicion persistente tambien forma parte de esta activacion agrupada: [uso y evidencia](EDITOR_MEDICION_MEZCLA_FINAL_ES.md). Se preserva el medidor mono previo del reproductor. No repetir el ensayo MP4 de ducking ya aprobado.
