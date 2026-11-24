# PixelFX — evaluación #90

24-11-2026, #3. [patch-gg/pixelfx fijado](https://github.com/patch-gg/pixelfx/tree/5294518ce7c72e48b6100a744596e0acf57f2826), package **0.3.1**. README, LICENSE, NOTICE.md, gallery/fonts/NOTICE.md, tools/render.mjs y src/core/sim.js revisados.244 efectos es catálogo declarado, no244 exportaciones comprobadas.

## Licencia y excepción de recursos

Código/efectos MIT, comercial permitido con avisos. NOTICE identifica adaptaciones de Hugo Duprez/Sprite Fusion y Hollow Crown/rehan-remade MIT: mantener atribuciones aplicables. **Patch Pixel de gallery/fonts queda expresamente fuera de MIT**; no copiar/distribuir fuente por la licencia del repositorio. Galería demostrativa no es paquete íntegramente elegible. Usar fuente local con licencia aprobada y registrar sustitución; no descargar assets. No instalar skill/plugin ni herramientas globales Patch.

## Windows, recursos y offline

Core JS/browser sin dependencias runtime declarado; herramientas **Node>=18**, esbuild^0.25.10 dev, exportadores tienen utilidades/formatos propios que deben inventariarse. PNG/sheets/JSON y GIF/MP4 no son el mismo camino; video/codecs/FFmpeg requieren comprobación aparte. Node localizado no acredita todos los exportadores. No ejecutar render/check: pueden producir imágenes. Sin modelo/GPU obligatoria para core; RAM/buffers/disco crecen con resolución, frames, capas y export. Rendimiento Windows no medido.

Biblioteca/efectos preparados pueden trabajar localmente sin API pagada. Publicación Patch/pch requiere componentes/cuenta/red y no es necesaria ni activada. Offline de una composición exige imports, runtime, fuente elegible y codecs locales; no prometerlo por core sin dependencias.

## Comparación y carencia

OpenMontage ya tiene composición, animación procedural, rigs/poses/eventos y QA; E06/E11 cubren integración y E04 timing. No otro renderer/UI ni catálogo creativo obligatorio. Útil: describir asset de efecto con **buffers color/luz y capas/pivote**, separado de biblioteca o export concreto.

Pure draw(t) y simulación120Hz son contratos diferentes. Poses12fps y fps final tampoco son intercambiables. Semilla fija no garantiza el mismo estado al saltar directamente al frame40 de una simulación sin reiniciar/avanzar pasos correctos; no afirmar determinismo visual sin comparar artefactos.

| Grupo | Aceptación futura con números/JSON/mocks |
|---|---|
| E06 | Asset con fuente/revisión/hash/licencia/NOTICE/seed/paleta/pivote/origen/alpha/color-light/front-back, bounds y unidades; fuente excluida rechazada. JSON Aseprite-style conserva rects/duraciones/loop/fps, campos desconocidos explícitos. |
| E04/E11 | Tiempo de simulación120Hz, poses12fps y salida racional separados; fixtures de freeze/windup/hit/recovery, dt irregular, seek/restart/loop y orden de capas. No reordenar causalidad del evento por estética. |
| E05 | Cambiar semilla/paleta/escala invalida derivados pertinentes; cache exige parámetros/revisión. Color/luz sin soporte queda unsupported, no se aplana silenciosamente. |
| B06 | Export/alpha visual, seams, escalado pixelado y rendimiento pendientes de fase autorizada; catálogo no prueba calidad final ni realismo. |

Evaluación completa, sin render/instalación/modelos/contenido/configuración modificada. Solo ampliar E04/E05/E06/E11, sin duplicados.
