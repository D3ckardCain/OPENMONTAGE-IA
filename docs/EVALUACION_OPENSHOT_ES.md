# OpenShot-Qt — evaluación #93

25-11-2026 UTC. Evaluación documental concluida; adopción e integración no ejecutadas.
Se reutilizan #93/7146322830 y #93/7147399702, sin repetir pruebas aprobadas de #92.

## Fuentes fijadas y decisión

[OpenShot 4.1.1](https://github.com/OpenShot/openshot-qt/tree/eead0c71dcb323f6befa7d5935daeb1bedf95cd2),
[README](https://github.com/OpenShot/openshot-qt/blob/eead0c71dcb323f6befa7d5935daeb1bedf95cd2/README.md).
Conservar además la revisión documental `37682676d836a513d6d08e763033daaddc0b1157`
de `doc/timeline.rst` y `doc/clips.rst`; no confundirla con el release.
Usarlo como referencia de interacción junto a Kdenlive y [Concat #67](EVALUACION_CONCAT_ES.md),
sin incorporar otro motor ni cambiar la estructura aprobada de #92: multimedia,
pistas inmediatamente debajo, herramientas debajo de las pistas y GitHub Dark.

## Comparación con OPENMONTAGE

`backlot/ui/editor-layout.js`, `editor.js` y `editor-time.js` ya tienen tamaños
persistentes, arrastre/teclado de trim, split, snapping, reordenar, zoom/ajustar,
Escape y undo/redo. `studio_editor_layers.py`, `studio_editor_effects.py` y
`studio_timeline_ops.py` ya contienen capas, títulos, transformaciones, transiciones
y ripple; audio/cues y el agente comparten el proyecto revisionado. No volver a
crear esas funciones como tareas nuevas. La evidencia ripple y persistencia de
#92 se reutiliza; no certifica toda la interacción o calidad audiovisual.

Carencias demostradas: `editPoints` no incorpora límites de capas/títulos;
no hay un contrato general de curvas animadas editables que conserve sus relojes
al cortar/retimar. Identificar claramente preview Fuente/Montaje y el borde activo
es una revisión de interacción pendiente, no un resultado visual acreditado aquí.
Título o cue disponible no equivale a editor lingüístico por palabra ni alineación.

## Licencias, Windows y operación local

Aplicación GPL-3.0-or-later según README y [COPYING](https://github.com/OpenShot/openshot-qt/blob/eead0c71dcb323f6befa7d5935daeb1bedf95cd2/COPYING).
El release usa libopenshot 1.1.1, [LGPLv3](https://github.com/OpenShot/libopenshot/blob/v1.1.1/COPYING).
`libopenshot-audio` tiene [GPLv3](https://github.com/OpenShot/libopenshot-audio/blob/7504624e07ea958ba5dcff2b7c1f261b47289b2b/COPYING)
en la revisión inspeccionada, no identificada como el binario exacto del instalador.
Qt/PyQt/PySide, JUCE, codecs/build FFmpeg, fuentes e imágenes requieren su revisión
de distribución propia. No se copia código, recursos ni binarios en esta fase.

Existe distribución Windows x64; compilar implica Python, Qt y sus bindings,
bibliotecas nativas y GCC/MinGW, no solo un ZIP Python. Editar/renderizar localmente
no requiere API pagada; offline depende de preparar codecs, fuentes y medios.
Aceleración experimental y rendimiento de la laptop no medidos. No instalación.

## Entregas al backlog existente

| Prioridad / ID | Aceptación concreta futura |
|---|---|
| P0 E01/E02 | Versión/capacidades frontend-backend coherentes y aviso de actualización pendiente; reutiliza diagnóstico de #99 y activación #92 |
| P1 E04/E06 | Snapping toma límites de capa/título; mismo cálculo al arrastrar y usar teclado; split/ripple conserva fuente y reloj del resto de elementos |
| P1 E06 | Antes de exponer keyframes, definir reloj fuente/montaje, interpolación y continuidad al dividir/retimar; undo/redo/reabrir conserva curvas |
| P1 E02/#92 | Verificar Fuente/Montaje, indicador de borde y tamaños en 1920×1080 y 3440×1440 con medios autorizados; no repetir regresiones ya aprobadas sin cambios |

El diagnóstico HTTP queda documentado en #92; no añade otra tarea de captura aquí.
Licencias de una eventual distribución y QA visual/sonora son condiciones de
adopción futura, no motivo para instalar OpenShot para terminar esta evaluación.
