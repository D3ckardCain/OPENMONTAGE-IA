# Revisión transversal: deportes, animación y noticias
Fecha: 2026-11-13. Investigación de candidatos; no instalación, inferencia ni producción.
Selección dirigida, no censo exhaustivo de Hugging Face. Los enlaces a repositorios
no constituyen listas de archivos ni aprobación completa de dependencias.
No tratar una descarga comunicada como archivo local íntegro.

## Novedades con prioridad
| Área | Candidato | Aporte | Licencia/estado |
|---|---|---|---|
| Animación | Wan-AI/Wan2.2-Animate-2-14B | Imagen de personaje y vídeo conductor; movimiento y control de vista | Apache-2.0 declarada en proyecto; revisar componentes y variantes antes de lista |
| Animación | 3DAIGC/LAM_audio2exp | Audio a controles de expresión facial | HF y código upstream Apache-2.0; revisar archivos internos, encoder y mapeo al rig |
| Noticias/verificación | Qwen/Qwen3-Reranker-0.6B | Reordenar pasajes por relevancia a una afirmación | Apache-2.0; candidato nuevo; no verifica verdad |
| Noticias/archivo | Qwen/Qwen3-Embedding-0.6B | Recuperación multilingüe y similitud | Apache-2.0; alternativa a MiniLM, comparar antes de reemplazar |
| Deportes/tenis | nvidia/NVIDIA-NemotronLabs-AI-for-Media-Sports-Tennis | Preguntas y análisis sobre clips de puntos | Ficha admite comercial, OpenMDW-1.1; cerrar lectura del acuerdo antes de aprobar |
| Deportes/tenis | vishnushenoy09/tracknet-v1-tennis | Localizar pelota pequeña en secuencias | MIT declarada por redistribuidor; verificar upstream/procedencia de pesos |

Wan-Animate-2 tiene un repositorio de aproximadamente 82,5 GB que puede contener
variantes o componentes compartidos: NO descargarlo completo sin desglosar.
Es distinto de Wan-Animate original y de Wan T2V/I2V, pero falta comparar sus
componentes por hash con el inventario existente.
LAM: árbol público muestra LAM_audio2exp_assets.tar (~32,8 MB) y
LAM_audio2exp_streaming.tar (~373 MB). El README HF es casi vacío; no asumir que
eso certifica cadena completa. El código original es aigc3d/LAM_Audio2Expression.
Wav2ARKit CPU y adolon-ai/lam-a2e son conversiones alternativas: no descargar todas
sin contrastar pesos externos, precisión y procedencia. Un grafo ONNX pequeño
no demuestra que incluya todos los pesos.
NVIDIA Tennis publica referencia BF16 de A100/H100 80 GB y ~62 GB de pesos;
candidato para equipo de producción, no validado en laptop. Sus respuestas no
son mediciones certificadas ni sustituyen seguimiento geométrico.
Embedding y reranker cumplen funciones distintas; similitud no equivale a veracidad,
independencia de fuentes ni detección infalible de una noticia repetida.

## Reutilizar, sin repetir descargas
- Deportes: RT-DETR v2, RFDETR-Soccernet, ViTPose+, DWPose, SAM2.1 y TAPNext++.
  Calibración: MOVA HRNet candidato; TVCalib y Soccer Tactical Vision solo código
  comunicado, componentes/pesos pendientes. Gráficos: MPLSoccer; datos: Kloppy;
  métricas: Socceraction.
- Animación: Qwen-Image/Edit, ControlNet Union, modelos de vídeo ya catalogados,
  voces, ACE-Step y MOSS; Blender, Rigify incluido, Krita y Rhubarb.
- Noticias: Qwen local, Qwen VL, OCR, Whisper/Qwen ASR, MiniLM, voces y montaje;
  Feedparser y Trafilatura para entrada. Fuente, hora, selección y derechos aún
  sin elegir. Feeds no garantizan el orden de portada.
No comprar servicios ni activar endpoints alojados como sustitutos de ejecución local.

## Licencias que impiden aprobación automática
- InstantCharacter: licencia original limita a investigación/educación; excluir comercial.
- InstantID: dependencia de modelos faciales InsightFace no comercial; excluir esa cadena.
- Kicky AI RF-DETR: ficha actual CC BY-NC 4.0; índice antiguo Apache no prevalece.
- MOVA RF-DETR: MIT en metadatos pero texto limita socios autorizados; pendiente.
- SAM3: licencia propia y gated; no tratarlo como Apache ni reemplazar SAM2.1 sin auditoría.
- YOLO: AGPL no implica necesariamente pago ni prohíbe uso comercial. Revisar
  obligaciones y procedencia del modelo concreto; etiqueta Apache de un fork no basta.
- LTX y Hunyuan: conservar condiciones previamente registradas; no declarar permiso
  comercial irrestricto para toda variante.
Revisar licencias en versiones fijadas y mantener copia de condiciones y avisos.

## Huecos reales
### Deportes
No se ha validado una solución completa para béisbol, boxeo o MMA/UFC.
Detectar personas y articulaciones no mide fuerza del golpe ni decide impacto válido.
Offside requiere instante de pase, balón, penúltimo adversario, partes válidas del cuerpo,
calibración y tratamiento de altura/oclusión. Homografía de suelo no resuelve cuerpo 3D.
Clasificadores de tipos de pelota no sustituyen localización o seguimiento.
### Animación
Faltan rigs, biblioteca de acciones, adaptadores faciales y QA de continuidad.
Ningún modelo se ha probado con nuestros personajes ni certificado para español.
Conservar opción 2D/3D/mixta sin decidir estilo por descarga de un motor.
### Noticias
Faltan conectores por fuente, derechos de recursos, trazabilidad, correcciones,
selección diaria, programación y publicación por plataforma. El reranker no hace
esas tareas ni determina automáticamente si una afirmación es falsa.

## Próximo trabajo de descarga
Preparar una lista por candidato, fijar revisión, tamaños, SHA de pesos y Git blob
para auxiliares; comparar con manifiestos e inventarios antes de repetir archivos.
Primero LAM original y Qwen Reranker por funciones nuevas; después desglosar
Wan-Animate-2. TrackNet, SAM3 y NVIDIA Tennis quedan sin lista aprobada hasta
resolver las comprobaciones descritas. No instalar ni ejecutar por este documento.

## Fuentes primarias consultadas
- https://huggingface.co/Wan-AI/Wan2.2-Animate-2-14B
- https://huggingface.co/Wan-AI/Wan2.2-Animate-2-14B/tree/main
- https://huggingface.co/3DAIGC/LAM_audio2exp
- https://github.com/aigc3d/LAM_Audio2Expression/blob/main/LICENSE
- https://huggingface.co/Qwen/Qwen3-Reranker-0.6B
- https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- https://huggingface.co/nvidia/NVIDIA-NemotronLabs-AI-for-Media-Sports-Tennis
- https://huggingface.co/vishnushenoy09/tracknet-v1-tennis
- https://huggingface.co/myned-ai/wav2arkit_cpu
- https://huggingface.co/adolon-ai/lam-a2e
- https://huggingface.co/facebook/sam3
- https://github.com/Tencent-Hunyuan/InstantCharacter/blob/main/License.txt
- https://github.com/instantX-research/InstantID
- https://huggingface.co/dcrey7/kicky-ai-rfdetr-seg
