# rembg — evaluación #94

25-11-2026 UTC. Código [61fca30e68a34082da41bbe6197f07bee0a7d36b](https://github.com/danielgatis/rembg/tree/61fca30e68a34082da41bbe6197f07bee0a7d36b).
Se reutiliza la inspección de `session_factory.py`, `bg.py` y `sessions/u2net.py`
del comentario 7146306499. Evaluación concluida; ningún modelo habilitado por ella.

## Valor diferencial y existente

OPENMONTAGE **ya tiene** `tools/enhancement/bg_remove.py`: llama explícitamente
`new_session(model_name)` con valor inicial `u2net`. Por tanto no está heredando
automáticamente el nuevo default BRIA del upstream. También existe el worker
`birefnet` en `lib/model_adapter_worker.py`, con salida cutout y carga local.
Presencia de adaptador no prueba disponibilidad/licencia de todos los pesos.
No crear otro removedor, servidor HTTP o editor para resolver esta necesidad.

Sí falta cerrar el contrato común de máscara/cutout/candidato: identidad y licencia
del modelo, entrada y salida con hashes, parámetros, espacio de color/alpha,
errores y cancelación. El resultado actual de BgRemove nombra modelo/parámetros,
pero no constituye por sí solo esa procedencia completa ni un bloqueo de descarga.
El nombre de salida debe ser explícito bajo el proyecto, separado del original.
`only_mask`, matting, posprocesado y descontaminación son operaciones distintas;
no prometerlas todas por exponer una casilla «quitar fondo».

## Licencias y elegibilidad

[Código MIT](https://github.com/danielgatis/rembg/blob/61fca30e68a34082da41bbe6197f07bee0a7d36b/LICENSE.txt).
El [README](https://github.com/danielgatis/rembg/blob/61fca30e68a34082da41bbe6197f07bee0a7d36b/README.md)
fija `bria-rmbg` como default y exige acuerdo pagado para RMBG-2.0 comercial:
**esa ruta no satisface nuestro perfil comercial $0**. WithoutBG/AtlasCloud y
créditos de alta tampoco son una dependencia offline/$0 aceptable.

U-2-Net declara Apache-2.0 en su origen; no equivale a una cadena de licencia
cerrada del ONNX convertido alojado por rembg. BiRefNet/ISNet/SAM/ViTMatte y cada
conversión necesitan archivo, revisión y términos propios. No se aprueban todos
los modelos porque el wrapper sea MIT. El inventario previo es la primera fuente;
no se repite una búsqueda física ni se propone descargar para esta evaluación.

## Requisitos y límites

[Manifiesto](https://github.com/danielgatis/rembg/blob/61fca30e68a34082da41bbe6197f07bee0a7d36b/pyproject.toml):
versión de desarrollo dinámica `0.0.0` — no una release identificada —,
Python `^3.11`; README limita soporte anunciado a 3.11–3.13. ONNX Runtime 1.23.2
CPU/GPU opcional; CUDA/cuDNN y provider Windows deben verificarse por artefacto,
en entorno aislado. NumPy/Pillow nuevos no justifican actualizar .venv/ComfyUI.

Primer uso puede descargar. Rutas actuales `REMBG_HOME`/XDG y `~/.rembg/models`,
con migración legacy desde `.u2net`: no mover caches por defecto. Mantener checksum;
MD5 publicado no se presenta como SHA256 oficial. GPU/CPU, memoria y calidad no
medidos; el perfil estimado del wrapper tampoco es un benchmark. Imágenes por
frame no aportan consistencia temporal de vídeo.

| Prioridad / ID | Aceptación futura, sin duplicados |
|---|---|
| P0 E01 | Modelo/artefacto explícito, licencia elegible y cache existente; unknown/NC/ausente falla antes de inferencia o descarga; integridad no desactivable como fallback |
| P1 E05/E06 | Salida candidata confinada al proyecto, original intacto, máscara/alpha identificados y recibo con hashes/parámetros; error/cancel no promociona parcial |
| P1 E02/#92 | Ajedrezado, fondos alternativos y comparación sincronizada con zoom; acción manual y agente llaman al mismo contrato |
| B04/B06 | Cerrar derechos del peso/conversión y luego revisar pelo, transparencia y bordes con medios autorizados; vídeo requiere evaluación temporal independiente |

No instalación, descarga, inferencia ni procesamiento de imágenes. La decisión
es mejorar el contrato de los adaptadores existentes, no añadir otro runtime.

Seguimiento posterior [#110](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/110):
[contrato local de BgRemove0.2.0](BG_REMOVE_LOCAL_ES.md), sin default/fallback de
modelos, con preflight/huella/revisión por artefacto y pruebas sintéticas. Este
añadido no repite la evaluación ni aprueba pesos reales/licencias/calidad visual.
