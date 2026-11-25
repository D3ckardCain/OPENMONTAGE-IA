# VCTK reentrenado: sustitución verificada (#111)

Revisión oficial: `5ec43b186ef915a195d3ddbcfd9916e76c503c3f`. Piper 1.8.0, Python 3.11.9, CPU y
red bloqueada durante síntesis; entorno aislado existente, sin tocar `.venv` ni
ComfyUI. No se reinició Studio y no se repitieron pruebas españolas.

## Integridad y atribución

| Archivo | Bytes | SHA256 verificado localmente |
|---|---:|---|
| MODEL_CARD | 581 | `ab7216e9aba1f493781c47fabab1078eeae2ea2b1ec29e41653249b007b959c0` |
| en_GB-vctk-medium.onnx.json | 8061 | `8cc5a7678bf893c35cb6fde5d0812fb7e2b63e1eef54db250afd525277471f2d` |
| en_GB-vctk-medium.onnx | 76972979 | `fc3d92d266b1a6c03af2a38215e0eee430ca7fb360f641d7c3dcb17c7670c0f3` |

ONNX coincide con SHA256 LFS oficial. JSON y tarjeta coinciden con los SHA256
registrados en la revisión fijada; no se confunde ETag Xet con SHA256.
Descargas exclusivamente de
[esa revisión](https://huggingface.co/rhasspy/piper-voices/tree/5ec43b186ef915a195d3ddbcfd9916e76c503c3f/en/en_GB/vctk/medium).
La transferencia HTTPS lenta se continuó en el mismo archivo temporal, con
rangos HTTP 206 comprobados y plazos acotados; el conjunto antiguo permaneció
intacto hasta terminar y verificar el SHA256 completo. No se llamó corrupto a
un archivo parcial. Sin copias adicionales de pesos en C: ni otros entornos.

Tarjeta: base `hifi_tts_92`, Cori Samuel, HiFiTTS lector92, MRD/SDP; VCTK0.92
mic1; Piper >=1.5; dataset CC BY4.0. Atribución conservada tanto en MODEL_CARD
como catálogo/recibos: **VCTK 0.92 CC BY 4.0; HiFiTTS CC BY 4.0, Cori Samuel reader 92**. Código Piper GPL3+, separado de
licencias de voces. No se redistribuyen pesos en GitHub.

## Comprobación real antes de sustituir

JSON: 109 hablantes, IDs únicos y exactamente 0–108, versión1.5.0,
22050Hz. Las muestras usan el mismo texto sintético inglés, sin contenido real:
«This is a short local voice test. No network connection is required.»

| Hablante | Etiqueta del JSON | Duración (s) | RMS PCM16 | Pico PCM16 |
|---|---|---:|---:|---:|
| 0 | p239 | 3.935782 | 5060.21 | 32767 |
| 54 | p267 | 4.388571 | 4576.83 | 32767 |
| 108 | p362 | 4.469841 | 5478.38 | 32767 |

Síntesis real con el worker existente, creación exclusiva y recibos con
procedencia. WAV mono PCM16,22050Hz, con señal no vacía/no silenciosa.
Esto comprueba tres IDs representativos; **no** acredita síntesis individual
de los109 ni escucha/inteligibilidad/identidad perceptual de hablantes.

## Sustitución y ausencia de duplicados en el destino administrado

Conjunto final: `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Piper/en_GB-vctk-medium`.
Antes de mover directorios se resolvieron sus rutas y se verificó que todos
pertenecieran a la carpeta Piper autorizada. Se comprobaron hashes del conjunto
antiguo y del nuevo, nombres exactos y ausencia de archivos ajenos. Intercambio
de directorios con rollback si la instalación/verificación fallaba. Hashes
finales nuevamente correctos antes de eliminar el antiguo.

Eliminados exclusivamente los tres archivos identificados del conjunto antiguo
y su directorio temporal vacío. El directorio de staging ya no existe. Una sola
copia VCTK en ese destino, con ONNX/JSON/MODEL_CARD nuevos; las otras tres
voces españolas y configuraciones anteriores se conservaron. No es un escaneo
ni garantía de ausencia de copias en discos ajenos/no comprobados.

El catálogo ahora permite únicamente el retrain fijado con JSON y tarjeta
coherentes; deriva109 hablantes reales. Una revisión/hash antiguo, Lessac,
versión antigua o IDs incorrectos conservan el bloqueo. El worker vuelve a
verificar la integridad antes de cargar. Nueve regresiones nuevas del bloqueo
aprobadas; no suite completa ni repetición de las pruebas españolas aprobadas.

## Activación y límites

Después de instalar el conjunto final se abrió un servidor aislado4751 con
el código actualizado y se cerró al acabar. Chrome instalado/Playwright
existente: selector real con109 hablantes, VCTK habilitado, hablante54, texto
«This is a short local voice test.»; POST real de preescucha, WAV22050Hz de
2.124626s reproducido hasta ended=true/readyState4, sin error multimedia ni JS.
Atribución visible VCTK/HiFiTTS/Cori Samuel. Captura1920×1080 inspeccionada.
Esto acredita interacción/decodificación del navegador aislado, no escucha humana
ni activación de4750. Evidencia local: `.runtime/piper/browser-vctk-results.json`
y `panel-vctk-retrained.png`. Script opt-in `validate_studio_piper_ui.cjs --vctk`
ejecuta solo VCTK, conservando las pruebas españolas ya aprobadas.

Preparado un único reinicio **manual posterior** para #108/#109/#110/#111 en
[el plan agrupado](ACTIVACION_AGRUPADA_STUDIO_ES.md). No ejecutado en esta tarea.
La API de identidad de4750 aún indicaba código anterior; salud no es activación.
Pendientes: activación/identidad/API/panel de4750 y escucha humana de Piper.
La validación real de BgRemove sigue pendiente por entorno/peso/licencia;
#107 mantiene español pendiente y portugués aceptado, sin repetirlo.
