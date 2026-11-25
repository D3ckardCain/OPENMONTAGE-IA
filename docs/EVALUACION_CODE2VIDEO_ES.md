# SenseNova 6.8 Code2Video — evaluación #97

25-11-2026 UTC. [Código y guías 776ae79824e338ba5d63fef66167455edc94ad26](https://github.com/OpenSenseNova/SenseNova-6.8-Code2Video/tree/776ae79824e338ba5d63fef66167455edc94ad26).
Modelo [0f99ab03e0e2616155b0395199acfdc322a741eb](https://huggingface.co/sensenova/SenseNova-6.8-Code2Video/tree/0f99ab03e0e2616155b0395199acfdc322a741eb),
metadata oficial Apache-2.0. Solo documentos/metadata, ningún peso descargado.

## Decisión y utilidad

Priorizar el método: especificación comprobable, render dependiente de tiempo,
revisión por muestras visuales y afirmaciones ligadas a fuentes. OPENMONTAGE
ya tiene HyperFrames/Remotion, reviewer, contratos de artefactos y probes;
no hace falta otro director ni el modelo27B para adoptar esas disciplinas.
Es vídeo creado mediante código, no un generador fotorealista intercambiable
con WAN/LTX. El 512K de contexto anunciado no garantiza calidad ni costo local.

Se reutiliza #97/7146376521. Rutas completas de los scripts revisados:
`skills/code-video/scripts/check_video.sh`, `sync_check.py` y
`skills/code-video/crafts/explainer-diagrams.md`. El frontend de la skill se leyó
como objeto de evaluación, no se instaló ni se adoptaron sus instrucciones.

## Evidencia que cambia la aceptación

El chequeo de archivo verifica dimensiones/fps/duración/codecs/audio; negro y
congelación solo producen avisos. Un OK no certifica calidad creativa, verdad
factual ni física. `sync_check` compara onsets de audio con eventos declarados,
no eventos visuales medidos: admite margen de un frame más5ms, hasta10% de
fallos y éxito sin eventos. No describirlo como sincronía audiovisual completa.
Decodificar audio entero y STFT tiene costo de memoria; adaptar ventanas/límites
al QA existente antes de proponer otro análisis obligatorio por exportación.

## Licencias, Windows y offline

El árbol fijado no contiene LICENSE identificable; tampoco declara licencia
el encabezado revisado de la skill. **Apache de los pesos no licencia por sí
solo scripts, guías, fuentes, capturas ni dependencias del repositorio.**
Adopción literal de esos archivos bloqueada hasta permiso explícito; se pueden
contrastar principios y escribir una implementación propia sobre contratos actuales.

Ejemplos de despliegue Docker/SGLang/vLLM y cuatro GPU, no receta Windows8GB.
No son un mínimo universal ni una medición de nuestra laptop. Sesiones largas
e iteraciones de horas tienen costo de cómputo aunque no haya factura API.
Offline requiere modelo, runtime, navegador, fuentes, FFmpeg y paquetes preparados;
helpers shell necesitan adaptación al runner Windows. No instalar el harness ni
usar mejora de prompts con servicios de pago. El agente/Ollama existente sigue
siendo la ruta a comparar, sin ejecutar inferencias durante evaluación.

| Prioridad / ID | Aceptación futura sobre lo existente |
|---|---|
| P1 E06/E11 | Especificación versionada vincula requisito, escena, texto exacto y tiempo; seek a t da el mismo estado por contrato, no por reloj de pared |
| P1 E05 | QA distingue error, aviso, omitido e intencional; un conjunto vacío no acredita sincronía; informe conserva método, umbral y evidencia |
| P1 E08 | Cada afirmación/número tiene fuente y revisión; compilar/codificar no certifica corrección factual |
| P2 E02/E14 | Revisión de legibilidad española a resolución final y contact sheet con cobertura temporal explícita; capturas futuras separadas de tests de datos |
| B03/B04/B06 | Licencia de guías/código, recursos/hardware y revisión visual pendientes; no descargar27B para resolver el checklist |

Evaluación concluida con límites de adopción. No instalación, render, audio,
modelos nuevos o cambios en configuraciones.
