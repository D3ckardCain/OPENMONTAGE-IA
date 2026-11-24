# ComfyUI-ReaVideoBreakdown: evaluación #75

24-11-2026 UTC. `benjiyaya/ComfyUI-ReaVideoBreakdown`
`bd4ba2ede3f0e7ab088ca5593af780c4afe2a65f`, pyproject0.2.0/Python>=3.10.
Solo lectura. No instalar nodos, actualizar/parchear ComfyUI o ejecutar tests upstream.

## Decisión y comparación

Reutilizar un contrato de planos que distinga tiempo/fuente, medición e inferencia;
no otro director ni detector duplicado. `lib/reference_analysis.py` ya da shots por
FFmpeg y ASR; #73 evalúa detector clásico. `scene_plan`/edit_decisions y E03/E04/E06/
E11 cubren límites y semántica. Aporte faltante justificable: cámara estimada con
método/unidad/confianza, descripción VLM separada y trazable a frames muestreados.
No clasificador confiable de origen IA/real/3D por made_of o porcentajes del modelo.

## Fuentes y arquitectura

[README](https://github.com/benjiyaya/ComfyUI-ReaVideoBreakdown/blob/bd4ba2ede3f0e7ab088ca5593af780c4afe2a65f/README.md),
[nodes.py](https://github.com/benjiyaya/ComfyUI-ReaVideoBreakdown/blob/bd4ba2ede3f0e7ab088ca5593af780c4afe2a65f/nodes.py),
[shots.py](https://github.com/benjiyaya/ComfyUI-ReaVideoBreakdown/blob/bd4ba2ede3f0e7ab088ca5593af780c4afe2a65f/rea_clip/shots.py),
[vlm.py](https://github.com/benjiyaya/ComfyUI-ReaVideoBreakdown/blob/bd4ba2ede3f0e7ab088ca5593af780c4afe2a65f/rea_clip/vlm.py):
Node1 detecta planos CPU/OpenCV y estima movimiento con Lucas–Kanade/RANSAC, luego
muestrea para VLM nativo clip.tokenize/generate/decode, fallback videos→images.
Pan px/s/zoom%/s son estimaciones bajo modelo de ajuste, no ground truth de cámara:
movimiento de objetos, parallax, cortes y blur pueden confundirlas.

VIDEO.md/JSON/prompts no son revisión factual. Idiomas en/zh, español no acreditado;
sin audio/BPM/OCR o subtítulos temporizados. No inventar observación auditiva desde
un frame. max_side limita imágenes de entrada al VLM, no el lote original completo,
RAM de decodificación, copias CPU/NumPy ni todo el contexto/VRAM. Métricas necesitan
coordenadas/resolución/fps/frames/tiempos exactos para comparación reproducible.

[Node2](https://github.com/benjiyaya/ComfyUI-ReaVideoBreakdown/blob/bd4ba2ede3f0e7ab088ca5593af780c4afe2a65f/nodes_v3.py)
usa ComfyAPI V3 y prompt Ref2VA MiniMaxH3 con slots de referencias. Requiere ComfyUI
reciente compatible, no existe mínimo exacto certificado por esta lectura. Reescribir
timeline a target_seconds no prueba sincronía ni preservación de intención.
H3 mantiene B01 de #47/#56: prompts no hacen compatibles pesos WAN/LTX ni resuelven
licencias. No modificar ComfyUI actual para ensayar ese nodo.

## Licencias, Windows/$0/offline

[MIT](https://github.com/benjiyaya/ComfyUI-ReaVideoBreakdown/blob/bd4ba2ede3f0e7ab088ca5593af780c4afe2a65f/LICENSE),
[requirements](https://github.com/benjiyaya/ComfyUI-ReaVideoBreakdown/blob/bd4ba2ede3f0e7ab088ca5593af780c4afe2a65f/requirements.txt)
NumPy/OpenCV-headless sin pin, torch del host. MIT del nodo no licencia VLM/H3/
medios ni asegura coinstalar OpenCV sin conflicto. Windows wheels/backend y encoder
con soporte visual requieren perfil aislado/revisiones/huellas antes de ejecutar.
CLIP SD1.5/SDXL no sustituye VLM de vídeo. Tener Qwen en Ollama no garantiza loader
CLIP ComfyUI equivalente. Sin API externa obligatoria; offline$0 condicionado a
todo recurso compatible local y egreso bloqueado, no probado en ejecución aquí.

## Tareas con aceptación

| Prioridad | Carencia / grupo | Aceptación |
|---|---|---|
| P1 | Plano neutral E03/E06 | Hash de vídeo, intervalo/frame/PTS/resolución y muestras; measured/estimated/inferred separados, made_of no hecho ni veredicto |
| P1 | Movimiento E11 | Método/parámetros/unidades/residual/inliers/confianza y unknown; mocks de objeto móvil/cámara quieta, parallax y RANSAC fallido |
| P1 | Descripción E04/E06 | JSON validado, español explícito como pendiente, truncamiento/parse_error/ausencia imagen visibles; cita frames/versión del VLM/seed sin alucinar audio |
| P2 | Doctor E01 | Node1 separado de Node2/H3, API/encoder/recursos y presupuesto RAM/VRAM; no auto-install/updates ni llamada de generación |

Bloqueos: VLM/API/recursos no validados y H3 condicionado. No bloquean contratos
neutrales sobre herramientas ya conectadas; sin inferencia ni contenido nuevo.
