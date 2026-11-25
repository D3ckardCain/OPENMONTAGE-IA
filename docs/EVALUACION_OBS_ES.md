# #102 — OBS Studio y obs-websocket

Evaluación documental, 25-11-2026 UTC; reutiliza comentarios 7146172581 y
7151141005. No se abre OBS, conecta un servicio ni captura audio/pantalla.

## Referencias fijadas

[OBS 33.0.3](https://github.com/obsproject/obs-studio/tree/f2aa9ce69caa7239ef26660b5889de4f53d9880e),
código GPL2-or-later; su submódulo
[obs-websocket](https://github.com/obsproject/obs-websocket/tree/e28f84975984340e84fc4879cfc05741cc0afde1),
licencia GPLv2. Se consulta protocolo generado Markdown/JSON y README en esa
revisión, no documentación móvil. Plugins, codecs y recursos tienen condiciones
separadas. Controlar un proceso externo no exige copiar código del motor; una
distribución conjunta debe revisar componentes y obligaciones.

Incluido desde OBS28: no instalar un segundo plugin. Protocolo5.x, RPC1,
puerto habitual4455 configurable. Hello/Identify autentican mediante desafío,
salt y SHA256/base64; negociar RPC y consultar `GetVersion.availableRequests`.
La versión sola no demuestra disponibilidad de cada operación. No publicar
contraseñas, exponer red o usar credenciales en argumentos visibles.

## Comparación y viabilidad

Ya existe `tools/capture/screen_recorder.py` y FFmpeg gdigrab/dshow: falta el
control **de escenas y propiedad de una grabación OBS**, no otro grabador genérico.
`GetStats`, `GetSceneList`, `GetRecordStatus`, `StartRecord`, `StopRecord` y
volumen tienen contratos documentados. Stop devuelve outputPath. La autorización
de una grabación futura será explícita; esta evaluación no la inicia.

[Requisitos generales oficiales](https://obsproject.com/kb/system-requirements):
Windows10/11 y GPU DX10.1; página general de 2021, no certificación específica
de33.0.3 ni rendimiento del encoder. Recursos GPU/disco y competencia con modelos
no medidos. Grabación/composición son locales sin API de pago una vez preparado
el entorno; emitir requiere red y derechos de plataforma, fuera de esta entrega.

## Tareas y aceptación

| ID / prioridad | Entrega futura |
|---|---|
| E10 P1 | Doctor OBS solo lectura, loopback, autenticación, RPC y métodos disponibles; secretos redactados y allowlist por operación |
| E12/E05 P1 para OBS | Start explícito con propiedad del job; timeout reconcilia estado sin ToggleRecord ni reintento ciego; nunca detener grabación ajena; Stop registra archivo nuevo dentro de roots y lo importa al proyecto compartido |
| E09 P1 | Medición posterior de duración/sincronía/dropframes distinta de escucha; no declarar calidad por respuesta del socket |
| B06 | Apertura/control/captura y resultado audiovisual pendientes; fixtures del protocolo no certifican OBS real |

No modificar escenas, preferencias, red, micrófono/cámara ni grabaciones actuales.
Evaluación concluida; el adaptador funcional sigue pendiente.
