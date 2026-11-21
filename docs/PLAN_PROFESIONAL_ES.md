# Plan de OPENMONTAGE‑IA

## Auditoría y punto de partida

En el commit 320bba9 pasaron 57 pruebas de comparativas, exportación y estudio. Una consulta real Messi–Mbappé en Qatar 2022 devolvió 7 y 8 goles y 29 y 21 disparos. La selección produjo un SVG y un segmento H.264 vertical de 720 × 1280 que FFmpeg decodificó completo. El segmento duró dos segundos y se probó sin audio. Chromium quedó bloqueado al arrancar en el entorno de auditoría. Quedan pendientes la validación visual y las pruebas de ComfyUI en la RTX 4060 de 8 GB.

El panel actual de fútbol expone consultas UEFA. El agente ya puede consultar varias fuentes, reunir lotes y validar una selección antes de exportar.

## Orden de implementación

1. **Métricas y fases.** Conservar las 54 métricas comunes en todas las competiciones y los campos adicionales que publique cada fuente. Mantener los datos sin evidencia como ausentes. Identificar edición, selección o club, fase, unidad y procedencia de cada cifra. Validar el calendario por edición. Los grupos, eliminatorias directas, semifinales, final y tercer puesto oficial cuentan en el total del torneo cuando se disputan. La clasificación previa corresponde a un bloque separado del historial individual. Un total de edición no habilita filtros por ronda.
2. **Mesa de comparativas.** Buscar dos jugadores, elegir competición y edición, revisar el informe con enlaces y seleccionar las métricas disponibles. Mostrar una vista previa antes de la aprobación. Guardar informe, selección y resultado de la revisión juntos. Exportar postal y clip desde el mismo expediente. Los filtros por ronda se habilitan cuando la fuente acredita ese alcance.
3. **Producción bilingüe.** Reusar el expediente, la plantilla y las escenas entre español e inglés. Generar y revisar audio y subtítulos por idioma. Marcar las piezas que requieren nueva revisión al cambiar datos o selección. Recuperar la entrega a otro disco desde el render verificado.
4. **Escala local.** Producir un piloto de diez piezas completas. Medir duración por etapa, uso máximo de RAM y VRAM, aprobación al primer intento y causas de reintento. Mantener la cola secuencial hasta tener medidas. Después separar tareas de CPU y GPU y asignar trabajadores según capacidad probada. Medir el rendimiento antes de comprometer el objetivo de 48 videos semanales. La publicación se opera por separado.

### Desglose por ronda de Qatar 2022

El agente puede consultar partidos jugados, goles y tiros en grupos, octavos, cuartos, semifinal, tercer puesto y final. Verifica el calendario de 64 partidos y contrasta los eventos de los encuentros consultados con el marcador. Incluye prórroga y deja fuera las tandas de penaltis al contar goles y tiros. El informe conserva las URLs por partido y el nombre StatsBomb. Esta consulta está disponible para investigación. La exportación visual del desglose sigue pendiente de integrar la atribución visible y la selección de métricas.

## Modelos candidatos

| Candidato | Prueba de aceptación |
|---|---|
| [Qwen3‑TTS 12Hz 0.6B CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice) | Comparar contra Qwen3‑TTS 1.7B y Kokoro con el mismo guion en español e inglés. Revisar pronunciación de nombres y cifras y medir memoria y tiempo. |
| [Qwen3‑VL‑4B‑Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct), variante cuantizada compatible | Revisar pocos fotogramas por consulta. Medir memoria y legibilidad detectada en rótulos y subtítulos. |
| [RF‑DETR Nano](https://github.com/roboflow/rf-detr) | Medir detección de jugadores. Probar el balón pequeño, las oclusiones y los cambios de cámara de forma independiente. |

Cotejar los inventarios antes de descargar. Faster‑Whisper y PaddleOCR latino ya están catalogados. Usar los pesos disponibles de WAN, LTX, FLUX y Qwen3‑TTS 1.7B para la primera ronda. Los candidatos requieren validación local. El objetivo operativo sigue siendo cero dólares, sin tarjetas ni APIs de pago.

## Formatos iniciales

- **Duelo en 30 segundos.** Dos jugadores y tres métricas aprobadas. Una pieza vertical animada y una postal desde el mismo informe.
- **La jugada explicada.** Diagramas tácticos propios. Añadir velocidad, balón y fuera de juego después de validar la medición con referencias conocidas.
- **Ficha de leyenda.** Fútbol, béisbol y boxeo con corte y fuente visibles. Distinguir bateo y pitcheo, y ranking, récord y resultado de combate.
- **Biblia ilustrada.** Historias con continuidad de personajes, pronunciación revisada y versiones en español e inglés. Usar generadores de movimiento en planos donde aporten al relato.
