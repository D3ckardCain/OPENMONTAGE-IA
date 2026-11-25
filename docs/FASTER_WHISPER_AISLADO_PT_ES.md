# Faster-Whisper aislado y muestra portuguesa — #107

25-11-2026 UTC. Instalación autorizada en entorno nuevo; `.venv` y ComfyUI no se
modifican. No se descargan pesos ni se traduce o genera voz. La prueba utiliza
el adaptador nativo existente, no otro AutoClip/ASR. **Validación española pendiente**.

## Entorno y configuración

- Python3.11.9, `.runtime/faster-whisper/venv/Scripts/python.exe`.
- Faster-Whisper1.2.1, CTranslate2 4.9.1, PyAV18.1.1, tokenizers0.23.3,
  ONNXRuntime1.32.0, huggingface-hub2.4.0, NumPy2.4.6. pip24.0/setuptools65.5.0.
- [Lock completo](../requirements-faster-whisper-windows-py311.txt) de paquetes
  instalados; `pip check` sin dependencias rotas y módulos importados correctamente.
- Configuración exclusiva `adapter_settings.faster-whisper`: Python del entorno
  anterior y `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Systran--faster-whisper-large-v3`.
  Se guarda mediante API Studio; demás settings y adaptadores permanecen iguales.
  Respaldo local de settings anterior, no publicado.
- El otro conjunto faster-whisper-large-v3 y sus originales se conservan.
  Presencia/tamaño de archivos no se presentan como revisión oficial/hash nuevo.
  Model.bin local3087284237bytes; no rehash/descarga/copia del modelo.

Fuentes de provisión: [Faster-Whisper1.2.1 en PyPI](https://pypi.org/project/faster-whisper/1.2.1/),
[CTranslate2 4.9.1](https://pypi.org/project/ctranslate2/4.9.1/),
[documentación oficial](https://github.com/SYSTRAN/faster-whisper).
Dependencias de CPU/int8 comprobadas, sin instalar Torch/CUDA o modificar drivers.
No extrapolar esta prueba a GPU ni prometer tiempo real.

Reproducción del entorno, solo si no está ya preparado:

```powershell
.\.venv\Scripts\python.exe -B -m venv .runtime/faster-whisper/venv
.\.runtime\faster-whisper\venv\Scripts\python.exe -B -m pip --use-feature=truststore install --only-binary=:all: --retries 1 --timeout 20 -r requirements-faster-whisper-windows-py311.txt
.\.runtime\faster-whisper\venv\Scripts\python.exe -B -m pip check
```

La primera instalación falló por cadena TLS del almacén usado por pip; se resolvió
con `--use-feature=truststore` y certificados nativos Windows, manteniendo TLS
verificado. No usar trusted-host, desactivar verificación ni cambiar certificados
globales. Los paquetes sí requieren red durante provisión; **la inferencia no**.
El lock no incluye pesos ni acepta licencias de recursos adicionales.

## Inferencia real, acotada y offline

Fuente original del proyecto `edit-794de088270c`:55.472472s,1080×1920 con audio,
20002714bytes. SHA256 original
`8c91014b94ee773afb32260534eff3113fd27ef3f11f9af7d27dab9f8cb31670`.
Nueva copia `edit-qa107-pt-5f4e1409`; original y manual_edit conservan hashes.

FFmpeg extrae0–25s del audio existente a PCM16/mono16kHz, sin síntesis de voz.
Una llamada real a `model_faster_whisper` utiliza ese WAV, `language:pt`,
`device:cpu`,int8,timeout600s y output_dir dentro de la copia. Worker existente
usa `local_files_only=True`, variables HF offline y bloqueo de sockets externos.
No se ejecuta Whisper por nombre remoto ni se permite fallback de pesos.

Resultado **success**,100.859s,12segmentos y116palabras con tiempos/probabilidades.
Es transcripción ASR, no simulación ni traducción. Idioma pt fue solicitado,
no una certificación independiente de detección; nombres propios y exactitud
requieren revisión. No se ejecuta una segunda inferencia ni se fabrican tiempos.
Se aplanan las palabras de segmentos sin interpolar y se conservan ambos JSON,
modelo/idioma, SHA de audio extraído y vínculo al vídeo de origen.

## Candidatos y montaje compartido

Operaciones reales por agent-command/HTTP en el mismo EDL que Studio:

1. Importar3 propuestas sobre las116palabras con cobertura ASR declarada0–25s
   (45.0674% de55.472472s), no toda la fuente ni revisión editorial completa.
2. Aceptar el tramo completo0–22.70s, que cierra una frase. La propuesta interior
   de negación conserva **não** al ampliarse a frase; queda pendiente de revisión.
3. Rechazar el fragmento final truncado22.78–24.98s; no usarlo como conclusión.
4. Insertar el aceptado; dividir11.52s y aplicar al segundo clip zoom1.15,
   foco0.65/0.5. Primer clip conserva plano completo. Output9:16/25fps.
5. Crear24cues desde las palabras reales en portugués, hasta6palabras por cue,
   conservando acentos/negaciones, y guardar/reabrir revisión11.

Subtítulos **incrustados** para revisión visual. No se usa el camino mov_text que
actualmente etiqueta spa: ese metadato multilingüe continúa pendiente de mejora,
sin alterar el servidor activo para esta muestra. No es traducción a español.
La separación por6palabras no certifica velocidad de lectura ni puntuación óptima;
las24cues siguen editables en el EDL y deben revisarse por reproducción.

## Exportación y comprobaciones

[Abrir proyecto](http://127.0.0.1:4750/studio?edit=edit-qa107-pt-5f4e1409#subtitles) ·
[MP4 local](http://127.0.0.1:4750/media/edit-qa107-pt-5f4e1409/assets/editor-renders/373ee0f363264abdab7ff2f613b684f7/montage.mp4).

Intento373ee0f363264abdab7ff2f613b684f7 completed/current. **22.72s**,568frames,
H.2641080×1920/25fps, AACestéreo48kHz,10255210bytes. SHA256
`042e514fc024407ca08a3a5715e9385529fe6ff325bfad59071d712fbea6e644`.

- Decodificación completa vídeo/audio sin fallos. Audio RMS mono0.19020, no silencio.
- Frame3s sin zoom y frame16s con zoom comparados contra transform esperado:
  MAE RGB0.57125/255 y0.56073/255 en región superior sin subtítulo.
- Revisión real de ambos frames: comentarista y fútbol visibles, texto portugués
  inferior legible, sin corte del texto en esos frames; cambio de escala aplicado.
  No son capturas de la ventana ni certifican todos los fotogramas/cues.
- Primera comparación directa PCM contra WAV extraído falló:correlación−0.02212;
  búsqueda limitada de desplazamiento tampoco la validó. Ese fallo se conserva.
  Contraste posterior con **el grafo exacto** del editor, que incluye atempo1,
  resampling y limitador, da0.9998818 en363520muestras. Prueba correspondencia de
  exportación con el plan, **no transparencia frente al audio original**, ni
  identifica por sí sola la causa de la diferencia. No se rebaja el umbral para
  llamar aprobada la primera comparación.
- No se ha verificado escucha humana, sincronía labial, corrección ASR por
  referencia independiente o interacción completa del panel local. Mantener
  esos límites visibles; no inferirlos de RMS, frames o duración coincidente.

Se añaden esta integración real/pip check/validaciones nuevas; no repetir suites
aprobadas. No cambios de código del editor, reinicio de Studio, servicios de pago
o configuraciones de Blender/FreeCAD/Krita/ComfyUI. Solo adaptador ASR autorizado.
Archivos de entorno, logs, settings, audio, transcripción y vídeo permanecen
locales; GitHub recibe lock/manual/resultados, no medios ni pesos.

**Confirmación posterior del usuario:** la muestra portuguesa queda validada.
Se registra como aceptación humana de esta muestra, sin repetir ASR/exportación
ni las comprobaciones anteriores. Las observaciones técnicas conservan su alcance.
**#107 permanece abierto por la prueba española pendiente**, que no hereda la
aceptación portuguesa. No se afirma validación general de otras muestras/idiomas.
