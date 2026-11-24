# PySceneDetect: evaluación #73

24-11-2026 UTC. `Breakthrough/PySceneDetect`
`a696070d1a30d81b35ba9aff89de50eb80696f04`, código main0.7.4-dev0.
No equiparar main a v0.7.3 anunciada al registrar el issue. Fuentes leídas como
datos; sin instalar, importar librería ni analizar/generar vídeo.

## Decisión y contraste

Mantener FFmpeg como base. `lib/reference_analysis.py::detect_shots` ya reduce
ancho320, select scene>0.3/showinfo, conserva intervalos/threshold y declara
verified_by_human=False. PySceneDetect aporta detectores adaptativo/fundidos,
estadísticas y API de frames, no selección editorial, ASR, significación narrativa
o viralidad. Elegir otra dependencia solo tras comparación de precisión útil.
E03 candidatos/E04 relojes/E06 metadata de planos cubren esa extensión; no crear
otro cortador ni duplicar escena por proveedor.

## Fuentes, licencias y requisitos

[README](https://github.com/Breakthrough/PySceneDetect/blob/a696070d1a30d81b35ba9aff89de50eb80696f04/README.md),
[pyproject](https://github.com/Breakthrough/PySceneDetect/blob/a696070d1a30d81b35ba9aff89de50eb80696f04/pyproject.toml)
y [versión](https://github.com/Breakthrough/PySceneDetect/blob/a696070d1a30d81b35ba9aff89de50eb80696f04/scenedetect/__init__.py):
Python>=3.10, NumPy/OpenCV y extras según backend; PyAV>=9.2 opcional. Variantes
headless/normal comparten namespace: no coinstalar indiscriminadamente OpenCV o
paquetes que sobrescriban archivos. Windows MSI/ZIP puede incluir Python/binarios:
no extraer ni duplicar lo preparado; librería aislada solo en fase posterior.
FFmpeg/mkvmerge necesarios para splitting, no convertirlos en requisito de todos
los análisis ni ejecutar split_video_ffmpeg durante diagnóstico.

[LICENSE BSD3](https://github.com/Breakthrough/PySceneDetect/blob/a696070d1a30d81b35ba9aff89de50eb80696f04/LICENSE)
exige avisos/no endorsement y
[THIRD-PARTY](https://github.com/Breakthrough/PySceneDetect/blob/a696070d1a30d81b35ba9aff89de50eb80696f04/THIRD-PARTY.md)
distingue OpenCV, NumPy, PyAV, FFmpeg, mkvmerge/GPL y Python incluido. Wrapper BSD
no licencia todos los codecs ni medios de entrada. No código copiado.

[AdaptiveDetector](https://github.com/Breakthrough/PySceneDetect/blob/a696070d1a30d81b35ba9aff89de50eb80696f04/scenedetect/detectors/adaptive_detector.py)
usa ventana/ratio y mínimo de escena; emite corte retrasado respecto del frame
procesado. [ThresholdDetector](https://github.com/Breakthrough/PySceneDetect/blob/a696070d1a30d81b35ba9aff89de50eb80696f04/scenedetect/detectors/threshold_detector.py)
usa intensidad para fundidos. Movimiento deportivo, flashes y disoluciones pueden
inducir falsos positivos; parámetros no son universales. FPS racional y PTS/VFR
requieren trazabilidad: no reconstruir reloj real siempre con frame/fps nominal.

## $0/offline y aceptación

Detección clásica local no necesita cuenta/modelos/API ni GPU por defecto; con
dependencias/codecs y archivos presentes puede operar offline. No se probó el
perfil Windows, consumo o precisión; Docker/instalador no se ejecutaron.

| Prioridad | Entrega / grupo | Aceptación |
|---|---|---|
| P1 | Shot boundaries E03/E04 | Fuente/hash, backend/versión/config, frame/PTS/timebase y rango válido; terminal/no-cut/clip corto/fps racional y VFR en fixtures, sin off-by-one |
| P1 | Integración ASR E03 | Proponer snap a límite visual sin cortar palabra/frase silenciosamente; conservar candidato original y motivo, conflicto/uncertainty explícitos |
| P2 | Comparación futura | FFmpeg vs Content/Adaptive/Threshold sobre corpus autorizado, precisión/recall/tolerancia y RAM/tiempo; flashes/deporte/fades separados, no métricas de interés |
| P2 | Export E06 | Datos de planos sin cortar medios; límites y pérdidas explícitos, usando FFmpeg actual si luego se autoriza corte |

Bloqueos de ejecución: paquete/backend/codecs Windows aún no validados. No impiden
esquemas/mocks; no instalar dependencia si el beneficio frente a FFmpeg no se mide.
