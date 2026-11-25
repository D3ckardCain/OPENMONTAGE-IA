# #107 — activación y validación HTTP en copia

25-11-2026 UTC. Servidor4750 reiniciado manualmente por el usuario, sin reinicio
adicional. identity/capabilities200, protocolo1, clip_candidates presente,
restart_required:false; PID89172. Resident/disk SHA256
`a68d1acb6b9aea6288bc57aa38beb20399647f53139b001b0d5ebff157df58a4`.
Se contrastan36 archivos del alcance declarado (17backend/19UI) con el árbol
de `f3a1e2853f1c391abdc7174c32ddb3489ebe95a0`: todos coinciden como blobs de
texto normalizados. Es evidencia de fuentes/snapshot, no atestación de bytecode
ni de todo archivo ajeno a ese alcance. No se atribuye un commit solo por PID.

## Copia y operaciones realizadas

Original `edit-173e7bc16d1e` conservado. Copia independiente
`edit-qa107-6281c8a744`, con assets copiados y sin heredar renders antiguos:
[abrir copia](http://127.0.0.1:4750/studio?edit=edit-qa107-6281c8a744#library).
No se ejecutan suites ya aprobadas. Operaciones por HTTP real, sin TestClient,
mock del backend o nueva inferencia:

- Limpiar solo el montaje de la copia por batch reversible; conservar fuentes.
- Importar8 palabras **sintéticas declaradas**, no transcripción del vídeo NOAA.
  Cobertura declarada10–14s de76.743333s (5.2122%); no se presenta como ASR real
  o revisión completa del medio. Selección desde «cambies» conserva «No» al
  ampliarse a frase. Motivo y texto previo conservados.
- Aceptar por agent-command; corregir a palabras1–7 vuelve a pendiente y pierde
  confirmación anterior; aceptar e insertar10.5–13.9s. Resultado:
  «No cambies el encuadre. Conserva el contexto.»
- Undo devuelve exactamente el EDL anterior; redo restaura el mismo clip y
  procedencia. Guardar/reabrir conserva resultado y revisión32.
- Encuadre9:16,zoom1.2,focus_x0.8/focus_y0.5, fuente sin silenciar. SRT manual
  QA0.5–2.5s preparado en modo seleccionable. Son parámetros persistidos,
  **todavía no evidencia de encuadre exportado o escucha**.

La huella del manual_edit original no cambió. Assets/copias y registro completo
de operaciones permanecen locales en `.runtime/qa/107-live-validation.json`;
no se publican medios, configuraciones ni archivos personales.

## Bloqueo físico de exportación

D: no aparece entre unidades conectadas (C:/E: disponibles). Las rutas guardadas
FFmpeg/FFprobe apuntan a D:, y el ejecutable configurado no está disponible.
No equivale a archivo borrado/corrupto. No se cambian rutas ni se instala otra
copia. Se solicita reconectar la unidad manteniendo D:.

POST render fue aceptado200 para la copia; intento
`7120accc06fb4c54afd52e960edd7154` termina **failed**, antes de arrancar encoder,
con «Configura la ruta de ffmpeg en el Estudio». No se ha producido un MP4
aprobado. #108 corrige ese diagnóstico genérico por separado, con fixtures.

Pendientes #107: exportación real, decodificación/encuadre comparado con fuente,
audio/subtítulos y revisión visual/interactiva/escucha. **#107 permanece abierto**.
Conectar D: permite continuar sin recrear copia ni repetir operaciones anteriores;
primero confirmar archivos accesibles y estado de la copia, luego un nuevo render.
No se reinicia el servidor ni se retoma el diagnóstico de red.
