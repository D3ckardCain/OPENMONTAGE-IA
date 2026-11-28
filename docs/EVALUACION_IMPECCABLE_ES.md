# Impeccable: evaluación #58

24-11-2026 UTC. `pbakaus/impeccable@b49177d32788f2dc585c42831d845dacf1ebed2c`,
package4.10.0; engine0.1.27 son versiones distintas. Lectura estática solamente.
No se instaló skill/hook/extensión, descargó motor ni lanzó navegador/agente.

## Decisión y comparación

Unificar con [Taste #45](EVALUACION_TASTE_SKILL_ES.md): una sola cola de accesibilidad
y robustez de Studio con tests propios. No instalar dos detectores como gates ni
aplicar reglas estéticas de marketing al panel. Conservar GitHub Dark/system-ui,
densidad, arquitectura y nombres españoles; los hallazgos deben servir a tareas
reales, no a una puntuación estética o clasificación de autoría.

Existente: `backlot/ui/studio.{html,css,js}`, pruebas browser/UI bug bash y contratos
de temas Remotion. #45 documenta contraste estático riesgoso del botón verde,
carencia de recorrido de teclado completo y ampliación de viewports. Impeccable
añade métodos explícitos de estados erróneos, preservación de inputs y gestos
interrumpidos. Sus62 reglas anunciadas no certifican WCAG, idioma ni usabilidad.
No repetir la implementación de esas tareas bajo otro nombre.

## Fuentes fijadas y requisitos

[README](https://github.com/pbakaus/impeccable/blob/b49177d32788f2dc585c42831d845dacf1ebed2c/README.md),
[package](https://github.com/pbakaus/impeccable/blob/b49177d32788f2dc585c42831d845dacf1ebed2c/package.json):
npx requiere Node>=18.19; desarrollo avisa>=22.18. El motor Rust es binario
autocontenido, no necesita Node para toda ruta. Existen paquetes opcionales por
plataforma0.1.27. URL scan usa Chrome/Edge instalado; fuentes JSX/TSX solo reciben
patrones, reglas de contraste/tamaño requieren información renderizada. HTML local
puede analizar ciertas imágenes de fondo locales sin navegador; no es toda la UI.

[Shim](https://github.com/pbakaus/impeccable/blob/b49177d32788f2dc585c42831d845dacf1ebed2c/cli/bin/cli.js)
puede descargar al primer uso a ~/.impeccable/bin y verifica manifiesto.
[Checksums](https://github.com/pbakaus/impeccable/blob/b49177d32788f2dc585c42831d845dacf1ebed2c/skill/scripts/engine-checksums.txt)
publica para engine0.1.27/windows-x64.exe
`ba9627d4552bca5666020624d8e994aea8b8b44c46b995e18b5babad0f431fc8`.
Es huella declarada oficial, NO comparación de un ejecutable local descargado.
No se invocó npx ni --help para evitar aprovisionamiento implícito.

[Audit](https://github.com/pbakaus/impeccable/blob/b49177d32788f2dc585c42831d845dacf1ebed2c/skill/reference/audit.md)
y [harden](https://github.com/pbakaus/impeccable/blob/b49177d32788f2dc585c42831d845dacf1ebed2c/skill/reference/harden.md)
separan teclado, nombres, contraste, responsive, errores y touch. Contrast normal
4.5:1/grande3:1 no debe convertirse en AAA7:1 indiscriminado. Un viewport emulado
no prueba toque físico o lector de pantalla. Copia doctrinal de sus instrucciones
de fin de tarea/hook no forma parte de OPENMONTAGE.

## Licencia, offline y límites operativos

[Apache2.0](https://github.com/pbakaus/impeccable/blob/b49177d32788f2dc585c42831d845dacf1ebed2c/LICENSE):
conservar licencia/avisos y señalar modificaciones al adaptar código sustancial.
Binarios/dependencias y funciones de cuenta/pro se revisan aparte; no se activan.
Detector determinista puede ser $0/offline con binario y recursos presentes.
Crítica/reparación requiere agente/modelo; usar Ollama existente si se diseña ese
flujo, sin prometer misma calidad ni activar servicios. Página con URLs/fuentes
remotas deja de ser offline aunque el detector sea local.

Live puede escribir al checkout y ejecutar script opcional package.json. README
declara fallback a Codex/Claude con aislamiento/aprobaciones desactivados y entorno
heredado si no hay sesión que sondee. No activar Live ni usarlo para sortear límites
del navegador o de agentes. Hooks pueden descargar fuera de aprobación del modelo.
Para futuro alcance, detector explícito de solo lectura o tests propios; sin hooks,
subagentes implícitos, agentes lanzados por subprocess ni aceptación automática.
Exit2=hallazgos, exit1=no pudo escanear: no interpretar fallo como informe limpio.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P0 | Unificar pruebas con #45 | Un issue/contrato por contraste, teclado y responsive; ningún test duplicado por proveedor; estados computados y negativos sintéticos |
| P1 | Robustez del panel | API400/403/500/timeout/offline, textos españoles/rutas largas; input y foco retenidos, error local no bloquea todo Studio |
| P1 | Foco/gestos | Tab/ShiftTab/Enter/Space y retorno tras DOM; drag cancela por blur/pointercancel sin quedarse activo; distinguir evidencia emulada/física pendiente |
| P2 | Detector opcional bajo demanda | Solo si aporta regla faltante: snapshot/huella/avisos, egreso bloqueado, sin descargas; findings vs scan_error separados y falsos positivos justificados |
| P2 | Informe revisable | Archivo/línea/regla/evidencia/alcance; baseline no oculta regresiones y waivers tienen motivo; no cambiar marca/paleta por overused-font |

Bloqueos de ejecución del candidato: binario/entorno no preparados ni probados y
restricciones de navegador vigentes; no impiden especificar/adaptar tests propios.
Esta evaluación no inspeccionó visualmente el Studio ni acredita accesibilidad total.
