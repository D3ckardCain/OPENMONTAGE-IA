# Evaluaciones #93–#104 — índice y decisiones

25-11-2026 UTC. Doce evaluaciones documentales; fuentes/revisiones fijadas y
hallazgos anteriores reutilizados. No se instalan candidatos, descargan modelos,
ejecutan inferencias, generan medios ni repiten pruebas aprobadas. No se hacen
nuevas capturas HTTP ni cambios de red. El diagnóstico #92 sigue documentado,
sin atribuir causa raíz al punto de pérdida observado.

| Issue / informe | Decisión útil | Condición principal |
|---|---|---|
| [#93 OpenShot](EVALUACION_OPENSHOT_ES.md) | Mejorar interacción/tiempo del editor existente, E01/E02/E04/E06 | GPL/LGPL por componente; no introducir otro motor ni repetir controles ya implementados |
| [#94 rembg](EVALUACION_REMBG_ES.md) | Endurecer BgRemove existente y trazabilidad de máscaras, E01/E05/E06 | Código MIT no autoriza pesos BRIA comerciales; wrapper actual elige u2net explícito |
| [#95 H3 Workflow](EVALUACION_H3_WORKFLOW_ES.md) | Contratos de perfil/tiempo y UI compacta, E01/E02/E04/E06 | Workflow sin LICENSE; H3 Community territorial/comercial, recursos32B y hardware sin validar |
| [#96 Chatterbox](EVALUACION_CHATTERBOX_ES.md) | Perfil regional español y variantes explícitas del adaptador actual, E01/E16 | MIT no prueba compatibilidad V3 ni companions locales; Turbo/Nano inglés |
| [#97 Code2Video](EVALUACION_CODE2VIDEO_ES.md) | QA temporal/semántica y spec con fuentes, E05/E06/E08/E11 | Repo sin LICENSE; pesos27B Apache no licencian scripts; ninguna ejecución aquí |
| [#98 LongLive](EVALUACION_LONGLIVE_ES.md) | Perfil honesto y contratos por segmentos, E01/E05/E06/E11 | 1.3B NC;2.0 NVIDIA; FP8/NVFP4/Plug distintos, sin garantía8GB |
| [#99 Phosphene](EVALUACION_PHOSPHENE_ES.md) | Coherencia de revisión/capabilities y tomas, E01/E02/E05/E06 | Pin dice5.0.86; appMIT, MLX Apple no Windows; recursos/Pro separados |
| [#100 Shotcraft](EVALUACION_SHOTCRAFT_ES.md) | Metadatos de plano/audio y controles de motores existentes, E04/E06/E09/E11 | Apache2 no cubre Remotion/fuentes/sonidos;124 recetas localizadas,150 anunciadas |
| [#101 PhotoCraft](EVALUACION_PHOTOCRAFT_ES.md) | Contrato de capas y puente explícito, E05/E06/E10 | MIT o Apache2, marcas/recursos separados; alpha y formatos con pérdidas |
| [#102 OBS](EVALUACION_OBS_ES.md) | Doctor/control autenticado de escenas y captura propia, E10/E12/E05 | GPL y componentes; websocket ya incluido, sin capturar ni conectar en esta fase |
| [#103 AutoClip](EVALUACION_AUTOCLIP_ES.md) | Candidatos por palabras y crop corregible, E03/E04 | Dos repos MIT distintos; offline anunciado no es validación; modelos/datos aparte |
| [#104 Voicebox](EVALUACION_VOICEBOX_ES.md) | Tomas/versiones y audio compartido, E04/E05/E16/E10 | AppMIT, motores/pesos distintos; MCP4 herramientas no toda REST; TADA Llama3.2 |

## Orden de implementación sin duplicados

La [cola consolidada](IMPLEMENTACIONES_PRIORIZADAS_44_60_ES.md) conserva sus16
familias E01–E16 y8 grupos B01–B08. Esta tanda amplía sus aceptaciones:

1. P0 E01/E02: identidad de revisión/capabilities de Studio y diagnósticos que
   impidan fallback o descarga oculta. No reiniciar ni reabrir diagnóstico HTTP.
2. P0 E03/E04: spans españoles de palabras→candidatos y crop editable, junto a
   tiempos/snapping que incluyan títulos/capas. Ya existen selección/ASR/reframe.
3. P0 E05: tomas/versiones, parciales y reanudación, distinguiendo solicitud de
   cancelación de parada real; reutilizar cancelación/jobs existentes.
4. P1 E06/E16: mismo proyecto para agente/usuario, máscaras y voz por variante;
   no otro estudio de imagen/audio ni promesas de roundtrip sin pérdidas.
5. P1 E10/E12: OBS primero lectura autenticada; grabación explícita futura con
   propiedad/reconciliación y archivo importable, no captura durante evaluación.
6. P1/P2 E08/E09/E11: QA con evidencias, eventos/fuentes y audio medido; contacto
   visual/escucha siguen separados de chequeos de formato o pruebas sintéticas.

Cada informe contiene criterios verificables y bloqueos. Las partes contractuales
pueden implementarse posteriormente con entornos existentes/fixtures sintéticos;
adopción de modelos/código no licenciado, hardware, GUI y AV reales permanece
bloqueada hasta resolver sus requisitos. No convertir bloqueo en instalación.

## Verificación y límites

Se comprueban UTF-8, presencia de12 informes, referencias fijadas, enlaces locales
y correspondencia con IDs de la cola. Esto es validación documental, no prueba de
las aplicaciones. Se conserva la CI ya aprobada de0f60b18; no se vuelve a ejecutar
la suite ni se atribuye esa CI a este cambio documental. PR#2 sigue en borrador.
