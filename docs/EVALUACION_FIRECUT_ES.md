# FireCut — #130, comparación documental para #3/#92

Consulta oficial:26-11-2026 UTC. Revisión de páginas públicas y código local;
sin instalación, cuenta, trial, licencia aceptada, ejecución o medios procesados.
No se fijó un binario/revisión de código del proveedor: sus páginas son mutables
y esta evaluación no acredita una versión instalada ni acceso a su código.

## Decisión y condiciones

Usar como referencia de interacción; no como dependencia central de OPENMONTAGE.
La [oferta oficial](https://firecut.ai/pricing/all/) diferencia productos:
Resolve anuncia tres utilidades gratuitas (silencios, separación multicanal y
Markers+); esto no convierte toda la suite en gratuita. Shorts web gratuito
limita720p, marca de agua,25vídeos/mes y5minutos/clip. Captions/Pro tienen cuotas
y requieren conexión. No utilizar planes, trials ni servicios de pago. El español
experimental anunciado no equivale a validación española local.

Los [términos](https://firecut.ai/terms) reservan propiedad del código/recursos y
ofrecen derechos limitados de uso; no son MIT/AGPL ni autorización de copia.
No trasladar código, imágenes, presets o marca del proveedor. Solo diseño de
un flujo propio con nuestros contratos. Licencias de motores/recursos existentes
siguen siendo independientes.

[Resolve](https://learn.firecut.ai/overview-davinci-resolve/installing-firecut.md):
Windows10/11x64, Resolve20+, clave y conexión durante uso; algunas vías necesitan
edición/versión adicional. La documentación describe envío de stills con permiso
automático por defecto en planes elegibles. No adoptar esa conducta ni tocar
permisos/ajustes del host. [Premiere](https://learn.firecut.ai/overview-premiere-pro/faq.md)
requiere Premiere2022+ y su propia licencia; no instalar otro editor para este fin.
Una utilidad gratuita o ejecutable de escritorio no acredita funcionamiento offline.

## Reutilización y diferencia demostrada

| Referencia útil | Ya existe en OPENMONTAGE | Carencia / aceptación futura |
|---|---|---|
| [Silencios](https://learn.firecut.ai/features/remove-silences.md): analizar, revisar y aplicar por separado; pistas guía, rango y padding | `tools/video/silence_cutter.py`: FFmpeg silencedetect, modos mark/remove/speed_up; mark escribe intervalos. Waveform y edición/ripple global existentes | Enlazar intervalos a propuesta sobre waveform, selección manual y reloj del EDL; hoy el cutter trabaja sobre un archivo, no acredita que todas las pistas/capas/cues sigan sincronizadas en Studio |
| [Repeticiones](https://learn.firecut.ai/features/remove-repetition.md): comparar tomas y conservar una | ASR local preparado, palabras/candidatos #107, reloj #115 y subtítulos #129 | Grupos revisables con contexto/negaciones/cifras protegidos. Coincidencia textual no prueba toma mala ni justifica aceptar siempre la última o más larga |
| Marcadores y cambios reversibles | markers, batch, undo/redo/reopen, revisión y recibos existentes | Reutilizarlos; no otro motor o proyecto paralelo para el agente |
| Multicanal/multicámara | Mezcla y fuentes de audio/vídeo independientes | Separar canales, diarizar y escoger cámara son tareas distintas; volumen no identifica hablante ni cámara correcta |

Lectura local contrastada: `lib/studio_timeline_ops.py`,
`lib/studio_editor.py`, `lib/studio_word_clock.py`,
`lib/studio_word_subtitles.py`, `tools/video/silence_cutter.py` y controles
de waveform del editor. No se ejecutaron para esta evaluación. Antes de considerar
Auto-Editor, revisar su adaptador/inventario y demostrar qué falta en el cutter;
no instalarlo como consecuencia automática de esta comparación.

## Tareas concretas, sin nuevas familias del backlog

1. **E03/E04, prioridad P0 acotada:** contrato de propuesta de silencios, pista/rango
   guía, unión de intervalos, umbral/mínimo/padding y tiempo fuente→montaje.
   Aceptación inicial offline con números: orden/solapes/NaN, intervalos vacíos,
   límites de palabras, cambios de velocidad, varias guías y hash/revisión obsoletos.
   Ausencia de palabras no se interpreta como silencio acústico. No generar
   nuevos intervalos medidos desde un mock ni llamar VAD a silencedetect.
2. **E04/E05, implementación visual posterior:** propuesta separada en waveform,
   escuchar límites y excluir cortes; aplicar únicamente revisados con batch/ripple
   existente y undo/redo/reopen. Conservar capas, títulos, audio, cues y marcadores.
   Cancelación/recibo evita repetir análisis confirmado; resultado incierto no retry.
   Prueba AV española propia en copia, autorizada por separado; no acreditada aquí.
3. **E03/E07, P1:** agrupar repeticiones sin reescribir ni eliminar por score.
   Probar acentos, negaciones, citas, énfasis deliberado y tomas no contiguas;
   selección del usuario y mapa de cambios obligatorio. Reusar palabras guardadas
   y modelo Ollama preparado solo si la fase requiere y autoriza inferencia.
4. **E04/E09, posterior:** multicámara requiere contrato de reloj/calibración y
   validación independiente de cada paso; no una ampliación implícita del cutter.

Se amplían criterios E03/E04/E05/E07/E09 existentes, no otro descargador/ASR/editor.
Operación propia puede ser local y$0 con motores preparados; la evaluación del
producto no acredita ninguna nueva integración ni benchmark. Configuraciones,
ComfyUI,4.5 predeterminado y PR#2 borrador conservados. No necesita reinicio.
