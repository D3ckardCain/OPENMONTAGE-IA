# Evaluaciones #71–#78

24-11-2026. Evaluaciones documentales completadas una por una; seguimiento #3. Sin instalación, descarga de modelos, ejecución de candidatos ni contenido generado. Cerrar estos issues significa completar la evaluación, no acreditar integración ni calidad del candidato.

| Issue | Informe | Decisión útil |
|---|---|---|
| #71 | [Raea](EVALUACION_RAEA_ES.md) | QA final con alcance y evidencia; separar uso interno de distribución bajo FSL. |
| #72 | [WhisperX](EVALUACION_WHISPERX_ES.md) | Alineación independiente de diarización, errores explícitos y un reloj coherente; reutilizar ASR. |
| #73 | [PySceneDetect](EVALUACION_PYSCENEDETECT_ES.md) | Comparar detectores con FFmpeg antes de incorporar dependencia; cortes no son saliencia. |
| #74 | [Auto-Editor](EVALUACION_AUTO_EDITOR_ES.md) | Señales candidatas y mapas temporales de ediciones; cortes ya existentes. |
| #75 | [ReaVideoBreakdown](EVALUACION_REAVIDEO_BREAKDOWN_ES.md) | Shot record con medición/estimación/inferencia separadas; no modificar ComfyUI. |
| #76 | [Cinematic Skill](EVALUACION_CINEMATIC_SKILL_ES.md) | Anclajes por palabra con procedencia; reparto de letras es heurística. |
| #77 | [Streambert](EVALUACION_STREAMBERT_ES.md) | Solo progreso de revisión de archivos propios, prioridad baja; no proveedores ni descargador. |
| #78 | [Reverb-TTS](EVALUACION_REVERB_TTS_ES.md) | Normalización española trazable; uso comercial de pesos NC bloqueado, codec/presets independientes. |

[Backlog consolidado](IMPLEMENTACIONES_PRIORIZADAS_44_60_ES.md):34 evaluaciones,16 entregas E01–E16 y8 grupos de bloqueo B01–B08. Se conservan IDs; solo se amplían carencias con aceptación, sin duplicar funciones. Primero E01/E03/E04/E05 con datos/mocks existentes, después formatos y perfil E06/E16; nuevas aplicaciones/modelos no son requisito para comenzar. E02 conserva GitHub Dark. #70 corresponde a CI y queda excluido del recuento de evaluaciones.

Fuentes y revisiones, licencia de cada componente, requisitos Windows y límites offline/costo constan en cada informe. Las versiones anunciadas, manifiestos y revisiones de código se distinguen de binarios probados. No hay benchmark local ni certificación funcional de esos candidatos. Bloqueos de adopción no impidieron terminar las evaluaciones.

Validación de esta entrega: UTF-8, enlaces locales, cobertura y unicidad de IDs; CI completa del commit final se registra en #3 y PR #2. Se preservan originales, configuraciones, entornos, ComfyUI y PR #2 en borrador; sin fusiones ni cargos.
