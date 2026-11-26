# Soundsible — #131, biblioteca y transiciones musicales

Evaluación estática26-11-2026 UTC, vinculada a #3/#92. Fuente oficial fijada:
[Arzuparreta/soundsible](https://github.com/Arzuparreta/soundsible/tree/3a6197073c3fc77c7aede995179f5cf79f8cdbef),
revisión `3a6197073c3fc77c7aede995179f5cf79f8cdbef`.
[shared/version.py](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/shared/version.py)
declara0.40.0; no equivale a versión instalada ni último binario de releases.

Decisión: referencia selectiva para biblioteca, análisis rítmico y transiciones
revisables, sin instalar otro servidor/reproductor ni proveedor musical.
No se ejecutó código, importó biblioteca, reprodujo audio o descargó canciones/modelos.

## Licencias, costo y funcionamiento local

[LICENSE](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/LICENSE)
MIT, copyright2026Arzuparreta, exige conservar avisos al reutilizar software.
No licencia las canciones. [LEGAL.md](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/docs/LEGAL.md)
separa derechos sobre medios y términos de plataformas; una canción accesible,
descargada o reproducible no queda autorizada para sincronizar con vídeo o monetizar.
Usar únicamente música propia o con licencia/atribución comprobada por recurso.

[README](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/README.md)
describe servidor propio sin suscripción, archivos locales y fuentes YouTube/Music.
El navegador y Windows necesitan ese servidor; no son caché autónoma offline.
Android anuncia copias offline en alpha, no prueba Windows. Búsquedas, sugerencias,
catálogos, letras, feeds, Live/relay y updates pueden usar red según función.
No cuentas/cookies/relay ni búsquedas musicales en esta evaluación. El perfil
adaptado deberá cerrar toda ruta externa y fallar sin fallback/descarga.

## Requisitos y efectos de arranque

[Instalación](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/docs/INSTALL.md):
Python3.10+, git, FFmpeg y Node recomendado24LTS. El manifiesto
[ui_web/package.json](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/ui_web/package.json)
exige `^22.22.2 || ^24.15.0 || >=26.0.0`; no sustituirlo por «cualquier Node22».
Incluye Solid/Vite/TypeScript. run.py prepara su entorno, instala cambios de
requirements y construye UI: **no es un doctor de lectura**. No ejecutarlo aquí.
[requirements.txt](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/requirements.txt)
incluye NumPy, ONNX Runtime, Flask/gevent, mutagen y yt-dlp; varias versiones son
rangos, no un entorno reproducido por esta lectura.

[Desktop beta](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/docs/DESKTOP_BETA.md):
Windows11x64/ARM64, empaqueta engine/FFmpeg/FFprobe, sin firma. La CI upstream
documentada no acredita escucha, tray físico, SmartScreen o upgrades del usuario.
No instalar binario para obtener funciones ya disponibles en nuestros motores.

## DJ beta, peso concreto y límites

[AUTO_MODE.md](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/docs/AUTO_MODE.md)
describe beat grid/tonalidad/estructura, dos decks, blends/fades/echo, tempo
limitado y corrección de ruta. Puede desplazar downbeats; confianza no garantiza
compás correcto. Tempo variable requiere tratamiento conservador. Una parrilla
estimada no certifica sincronía perceptiva ni mezcla final.

[weights.py](https://github.com/Arzuparreta/soundsible/blob/3a6197073c3fc77c7aede995179f5cf79f8cdbef/shared/dj/weights.py)
fija Beat This! final0 ONNX,84249656bytes, SHA256
`c31e46719845b8111259289885996629735ba0d2815bfcef2da4f7dc6224aa31`,
asset `dj-model-beat-this-final0-1/beat_this-final0.onnx` del mismo repositorio.
Declara MIT del origen y conversión; antes de incorporarlo, contrastar licencia
original/pesos/conversión y artefacto exactos. No se bajó ni calculó hash local.
`session()` puede descargarlo en primer análisis desde fuente; distribuciones
lo incluyen. El modo explícito sin descarga existe en model_path, pero no vuelve
inocuo ejecutar la aplicación entera. No iniciar sesiones/analizador por diagnóstico.
La caché verificada del candidato se guarda por Path en memoria: para nuestra
reutilización exigir identidad/metadatos vigentes, no confiar solo en ruta.

## Comparación y tareas sin duplicados

| Ya existe localmente en código | Diferencia útil / aceptación futura |
|---|---|
| `tools/audio/music_library.py`: descubre música local; no concede derechos por nombre de carpeta | Ficha de recurso fuente/hash/licencia/atribución/derechos de sincronización, faltante/desconectado explícitos. No otro catálogo/red |
| `tools/analysis/audio_energy.py`: loudness momentánea con FFmpeg; `audio_mixer.py`: mezcla, ducking y normalización | Loudness no es beat/downbeat. Separar medida, estimación y corrección manual; no duplicar mezcla ni convertir nivel en BPM |
| `tools/video/bmts_lite.py`: adaptador de montaje por beats, dependencias librosa/NumPy y entorno externo explícitos | No se confirmó instalación ni runtime aquí. Comparar primero su análisis existente; disponer de adaptador no acredita ejecución ni beats corregibles en Studio |
| Audio del EDL, curvas/fades, revisión, undo/reopen y agente compartido | **E04/E06/E09 P1:** beats/compás/entrada/salida editables en mismo reloj; vista y preescucha A/B, corrección manual y export consistente. Sin reimportar una app DJ |
| Recibos y hashes existentes | **E01/E05:** análisis por fuente/hash/versión/parámetros/cobertura, invalidación mínima y cancelación sin repetir resultados válidos; original intacto |

Primero contratos numéricos con tempo variable/medio-doble tempo/downbeat errado,
silencio y voz superpuesta; unknown cuando no hay evidencia. Toda transición
conserva dos fuentes y mapa temporal, ganancia/curva/tempo y permiso, es reversible
y rechaza base obsoleta. No afirmar licencia/calidad desde un BPM o una búsqueda.
Después, únicamente en fase autorizada, muestra AV propia breve con escucha y
medición/visuales del cambio; hasta entonces no automatización musical validada.
ACE-Step ya existe como motor diferente de generación: no generarlo ni bajar pesos
para evaluar una biblioteca/DJ. Se amplían E01/E04/E05/E06/E09 sin nuevas familias.

Se reutilizaron revisiones/documentos fijados, no se instaló nada ni se tocó
ComfyUI/.venv/configuraciones. Costo$0,4.5 predeterminado y PR#2 borrador.
