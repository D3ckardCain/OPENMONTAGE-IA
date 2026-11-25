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

## Bloqueo físico de exportación — historial previo a reconectar D:

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

## Exportación retomada tras reconectar D:/E: — resultado actual

Las rutas guardadas existen y ambos `-version` devuelven exit0:

- `D:\OPENMONTAJE-IA\HERRAMIENTAS\FFmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe`
- `D:\OPENMONTAJE-IA\HERRAMIENTAS\FFmpeg\ffmpeg-9.0.2-essentials_build\bin\ffprobe.exe`

Ambos9.0.2 essentials_build-www.gyan.dev. No hizo falta buscar alternativas,
descargar o duplicar ejecutables, cambiar rutas ni reiniciar Studio. MismoPID89172,
protocolo1/clip_candidates y revisión32 de la copia. No se repiten candidatos,
undo o pruebas previamente aprobados. El bloqueo físico anterior queda resuelto.

Nuevo intento `18311b3980ac412b9518d64ef5adc1bc` **completed/current**:
[MP4 local](http://127.0.0.1:4750/media/edit-qa107-6281c8a744/assets/editor-renders/18311b3980ac412b9518d64ef5adc1bc/montage.mp4).
4566153bytes, SHA256
`a53526f1870e43d3b02ca0b03c9d29a8c9176ed7e9ee9caf6325d0a84f4bd466`.

| Comprobación nueva | Resultado |
|---|---|
| Vídeo real | H.2641080×1920,82frames/24fps,3.416667s; duración redondeada al fotograma de salida |
| Audio real | AAC estéreo48kHz,3.416667s, inicio0; PCM mono RMS0.12019548/pico0.65862429, no silencioso |
| Subtítulos exportados | mov_text seleccionable; extracción SRT exacta0.500–2.500s, `QA107: No cambies el encuadre.` |
| Decodificación | Vídeo y audio completos con FFmpeg `-xerror` sin fallo |
| Encuadre exportado | Frame24 comparado con fuente10.5–13.9s y transform real zoom1.2/foco0.8: MAE RGB0.63554/255 a180×320; alternativa centrada22.13635/255, claramente distinta |
| Entrega HTTP | Range0–1023 devuelve206/1024bytes, Content-Range con tamaño total4566153 |
| Conservación | Original manual_edit y settings/applications con SHA256 idénticos; sin nuevos modelos/inferencia |

Revisión del fotograma real decodificado: encuadre vertical del fondo marino sin
bandas, no frame vacío. La comparación prueba aplicación del foco elegido,
**no selección inteligente del sujeto ni identificación de hablante**. El texto
QA es manual/sintético, no transcripción del vídeo. Los subtítulos seleccionables
no están quemados en ese fotograma; su pista y tiempos se verifican por extracción.
RMS/pico y decodificación no acreditan escucha, inteligibilidad, calidad subjetiva
o sincronía de habla. No se declara interacción/preview dentro de la ventana local.

Registro y frame permanecen en la copia/local QA; medios no se publican en GitHub.
**#107 sigue abierto por comprobación visual/interactiva y escucha pendientes**.
Este resultado levanta el bloqueo de exportación, no esas comprobaciones. Sin
repetir suites/CI aprobadas ni hacer capturas extensas o cambios de red.
