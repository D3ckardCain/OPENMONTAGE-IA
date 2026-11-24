# Raea: evaluación #71

24-11-2026 UTC. Fuente `shinyobjectz/raea@66eb15448f69ab29a801fe1bde75d3889d34d04e`.
README presenta Review0.1.6; no equiparar ese anuncio a binario local/release probado.
Cargo de engine/CLI declara0.1.0; rust-toolchain fija1.99.1 y Bevy0.20. Son referencias distintas, no una versión instalada comprobada.
Solo lectura de código/documentación y licencias; no instalar CLI/app/skills/hooks.

## Decisión y comparación

Estudiar controles de calidad de texto/contraste/zonas seguras/freeze/loudness y
contrato de composición, sin adoptar otro runtime/UI. E01/E04/E05/E06 y E11 ya
agrupan doctor, timing, jobs, intercambio y animación; E02 es accesibilidad del
panel, distinta de QA del vídeo. `lib/render_verification.py` verifica metadata,
decodificación y hashes, separando visual_quality/content_accuracy=False. Contratos
de contraste Remotion no constituyen control del frame final. Carencia útil:
informe QA por hallazgo con región/tiempo/alcance y evidencia, no otra aprobación.

## Licencia: uso interno frente a distribución

[LICENSE completa](https://github.com/shinyobjectz/raea/blob/66eb15448f69ab29a801fe1bde75d3889d34d04e/LICENSE)
FSL1.1-ALv2 permite expresamente uso/acceso interno; no licencia Apache actual.
Competing Use incluye ponerlo a disposición de otros en producto/servicio comercial
que sustituye u ofrece funciones iguales/sustancialmente similares. No inferir
elegibilidad de incorporarlo/distribuirlo con OPENMONTAGE por permitir render interno.
Tampoco toda redistribución está prohibida: exige propósito permitido y mantener
términos/avisos. Cada versión obtiene Apache2 en su segundo aniversario; fijar
fecha/version aplicable, no tratar main nuevo como convertido automáticamente.

[NOTICE](https://github.com/shinyobjectz/raea/blob/66eb15448f69ab29a801fe1bde75d3889d34d04e/NOTICE)
separa partes de HyperFrames Apache2, mediabunny MPL2, Bevy MIT/Apache y Windows
FFmpeg LGPL/DXC/uv/Git GPL. Un componente originalmente Apache no elimina la FSL
del conjunto ni autoriza copiar derivados sin revisar procedencia. Modelos/assets
de demos y marcas no son licencia uniforme. No se copió código.

## Windows, $0 y offline

[README](https://github.com/shinyobjectz/raea/blob/66eb15448f69ab29a801fe1bde75d3889d34d04e/README.md)
declara Windows10/11x64 como plataforma más nueva/menos probada, DX12/Vulkan driver;
Rust/Bevy0.20, Bun y dependencias nativas para build. macOS usa JavaScriptCore,
otros QuickJS: React/Three.js familiar no acredita equivalencia de renderer/browser.
Instalador cambia PATH bajo ~/.raea y plugin añade hooks; no ejecutarlos.
Benchmarks Apple Silicon no acreditan RTX4060Laptop8GB/16GBRAM.

Motor/app sin cuenta de pago según README, Pro/Team cloud excluidos. RAEA_OFFLINE=1
es control útil pero no prueba: modelos de primera descarga, imports/assets/fuentes,
updates y `gen` con proveedor pueden necesitar red. Perfil cerrado/egreso denegado
y licencias de cada recurso antes de cualquier ensayo. No API, modelo ni render usado.

## Tareas propuestas

| Prioridad | Carencia / grupo | Aceptación |
|---|---|---|
| P1 | QA multimedia estructurado, E04/E05 | Hallazgo con archivo/hash, frames/segundos, región, regla/umbral/versión, evidencia y estado unknown/error separado; mocks de texto cortado, freeze intencional y audio ausente |
| P1 | Doctor/elegibilidad, E01 | Uso interno explícito vs incorporación/distribución pendiente; versión/avisos/hardware/recursos sin instalar ni descargar |
| P2 | Intercambio, E06 | Subconjunto de props/timing/scene con unidades y unsupported explícitos; no afirmar React/R3F compatible sin validar |
| P2 | Calidad futura | Evaluar frame/sonido y rendimiento con medios sintéticos en fase autorizada; no convertir score técnico en aprobación creativa |

Bloqueos: distribución/incorporación FSL sin alcance resuelto y GPU/runtime Windows
no validados. Uso interno no se confunde con esos bloqueos; contratos propios siguen
independientes. Sin cambios de configuraciones, ComfyUI o GitHub Dark.
