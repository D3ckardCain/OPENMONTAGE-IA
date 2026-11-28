# EvaluaciÃ³n de Line-Art Animation #178

Fecha: 2026-11-27. Fuente original fijada a [`JDhruv14/line-art-animation@c43d698913cf0ad44f984c7ae14c5348010594d3`](https://github.com/JDhruv14/line-art-animation/tree/c43d698913cf0ad44f984c7ae14c5348010594d3); no se usaron mirrors ni se ejecutÃ³ SKILL.md.

## DecisiÃ³n

No instalar una nueva app ni incorporar un segundo timeline/capturador. La biblioteca es corta (SVG/TypeScript) y ofrece un estilo line art opcional: dibujo ink-on-paper, gait walk/run, springs/pendulums/wind y paleta dÃ­a/noche. No necesita pesos ni API, pero cada escena/personaje se programa; no convierte arbitrariamente un vÃ­deo o avatar en line art.

Reutilizar las capacidades Three.js/Remotion/HyperFrames y las guÃ­as line art/motion existentes en #132/#135/#136/#137, integrando una forma SVG editable solo si funciona con el mismo reloj, proyecto, undo y export de #174. No copiar automÃ¡ticamente Walker/Village, medios ni instrucciones externas. #178 se completa como evaluaciÃ³n; una implementaciÃ³n local es una entrega distinta.

## Fuente, licencia y dependencias

- `LICENSE` raÃ­z es MIT, copyright JDhruv14. No hace falta comprar API o modelo para ejecutar el cÃ³digo ya escrito; se mantienen el copyright y aviso MIT si se reutilizan partes.
- La biblioteca `lib/` declara cuatro mÃ³dulos TypeScript sin dependencias de runtime. El `package-lock.json` registra Ãºnicamente herramientas dev `vite`, `typescript` y `@types/node`; Node indicado por README/SKILL/scripts es **>=22.18** y FFmpeg. No hay garantÃ­a de compatibilidad de esa revisiÃ³n con el Node del proyecto sin probar.
- Hallazgo reproducible en el Ã¡rbol fijado: hay `package-lock.json`, pero no `package.json`; README instruye `npm install`, `npm run dev`, `npm run typecheck` y `npm run build`. El manifiesto que definirÃ­a esos scripts no aparece en esa revisiÃ³n, asÃ­ que esos comandos quedan inconsistentes y no se ejecutaron.
- README dice que Chrome local se encuentra automÃ¡ticamente o se selecciona con `CHROME`. `scripts/capture.ts` solo enumera rutas macOS/Linux y env `HOME` mÃ¡s `CHROME`; no busca rutas estÃ¡ndar de Chrome/Chromium de Windows. En esta plataforma necesitarÃ­a ruta explÃ­cita/validaciÃ³n de proceso, no se declara Windows listo.
- `scripts/frames.sh` usa `mkdir -p`, expansiÃ³n aritmÃ©tica y sintaxis POSIX; no es un script de PowerShell. Puede sustituirse por FFmpeg y utilidades Windows ya existentes, si una tarea posterior lo necesita.
- `scripts/capture.ts` crea PNG y abre el endpoint CDP de Chrome por loopback (`127.0.0.1`); no se detectaron llamadas remotas en ese fragmento inspeccionado. `clip.ts` ejecuta FFmpeg localmente con argumentos separados. El anÃ¡lisis estÃ¡tico no cubre mÃ³dulos, dependencias transitivas o HTML arbitrario.
- Los GIF/PNG de preview no tienen un aviso de licencia de media separado visible en el README. No usarlos en entregables. Confirmar derechos de cualquier sample/asset antes de copiarlo; no confundir MIT del cÃ³digo con autorizaciÃ³n de medios externos.

## Reproducibilidad temporal y Windows

El API de ejemplo `run((t, dt) => â€¦)` acumula fase/posiciÃ³n con `dt`. Eso funciona en avance secuencial fijo, pero una seek/lectura de fotogramas fuera de orden puede depender del historial. Para integraciÃ³n con el playhead compartido, la animaciÃ³n deberÃ¡ derivarse de tiempo absoluto o poder resetear/replay determinista; no estÃ¡ acreditado por el ejemplo una sola secuencia monotÃ³nica.

La captura usa headless Chrome y CDP local, resuelve frames con exactitud nominal desde su script y FFmpeg codifica la secuencia. No se probÃ³ si Chrome instalado, permisos de puerto, fuentes, path, salida de Vite o codecs funcionan en Windows. `frames.sh` refuerza que esa ruta auxiliar requiere adaptaciÃ³n. El README â€œbuilds/renders on your own PCâ€ no es evidencia de validaciÃ³n en esta instalaciÃ³n.

## ComparaciÃ³n con OPENMONTAGE

| Ya hay / issue | AplicaciÃ³n sin duplicar |
|---|---|
| Skills Three.js, Remotion, GSAP y HyperFrames locales | Mantener el runtime/perfil actual escogido; no agregar otro proyecto Vite ni una segunda app.
| #174: timeline y capas compartidas | Poder colocar una animaciÃ³n/SVG como capa editable con ID, versiÃ³n, tiempo absoluto, transform y undo; sincronizar preview/export.
| #158: personajes por cuenta | Dibujos propios con origen y versiÃ³n; perfil visual no significa rig, lipsync o identidad generativa.
| #159/#164: director y guion | Usar estilo como opciÃ³n tras presentar propuestas, no regla fija de todo short; mantener hechos y fuentes.
| #177: sonidos autorizados | No reutilizar audio/FX del ejemplo sin origen/licencia; usar biblioteca local con recibo #177.

No se crea backlog duplicado. Nombres `walking`, `wind`, `daynight` describen cÃ³digo reusable, no automatizaciÃ³n editorial terminada.

## AceptaciÃ³n de una futura implementaciÃ³n pequeÃ±a

1. Inventariar primero la forma de importar SVG/capas y export local; no cambiar `.venv`, ComfyUI ni Node global.
2. Una escena SVG original mÃ­nima en copia; misma salida al buscar frame t=2, t=1, t=2 y al abrir proyecto/export. Hash de frame exacto para detectar deriva.
3. Probar loop de marcha con contacto de pie sin deslizamiento, inicio/fin sin salto, zoom/escala de capa y guardar/reabrir; escena en 9:16 y 16:9 sin stretch ni recortes ocultos.
4. Si `dt` acumulativo no pasa seek fuera de orden, cambiar integraciÃ³n a funciÃ³n `poseAt(absoluteTime)` o replay desde estado inicial; un avance determinista 0â€¦N por sÃ­ solo no satisface seeking.
5. Probar Windows con rutas/Chrome resueltas y `FFmpeg` existente solo al llegar a integraciÃ³n; usar el capturador de Studio ya instalado o capturar HTML directamente segÃºn compatibilidad. Sin descarga ni render antes de aprobaciÃ³n de la implementaciÃ³n.

## VerificaciÃ³n y lÃ­mites de esta evaluaciÃ³n

- Revisados commit/tree/README/LICENSE, los mÃ³dulos `ink.ts`, `gait.ts`, `motion.ts`, `daynight.ts`, package-lock, ejemplos, `capture.ts`, `clip.ts`, `frames.sh` y guÃ­a SKILL como datos.
- ComprobaciÃ³n documental focalizada: SHA, licencia/cÃ³digo frente a assets, Node/dependencias, ausencia del manifest, compatibilidad Windows no acreditada, necesidad de reloj absoluto y solapamiento con backlog existente.
- Sin instalaciÃ³n, `npm install`, ejecuciÃ³n de scripts, acceso a Chrome, captura, referencia de vÃ­deo, exportaciÃ³n, voz, inferencia o contenido nuevo.

## AceptaciÃ³n de evaluaciÃ³n

- [x] SHA oficial, MIT y dependencias fijadas.
- [x] Windows, commands/manifiesto, captura local, `dt` y lÃ­mites de assets revisados.
- [x] Solapamiento consolidado en issues existentes.
- [x] Sin instalar o renderizar.
- [ ] Prueba de escena/export local: no realizada; requiere una entrega distinta y validar primero la inconsistencia de manifiesto/Windows.

