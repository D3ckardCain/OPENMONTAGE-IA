# EvaluaciÃ³n de Animated Shorts #179

Fecha: 2026-11-27. Se revisaron metadatos, README, licencia, skills y muestras de cÃ³digo en las revisiones fijadas. No se instalaron paquetes, no se descargaron assets/pesos y no se renderizÃ³.

## DecisiÃ³n

No instalar ambas skills ni copiar ninguna plantilla completa. Reutilizar el concepto opcional de cuento/cartoony 2D dentro de mundo 3D con cÃ¡maras y profundidad como vÃ­a creativa de #159/#164/#158/#174/#178; usar los motores y catÃ¡logo ya disponibles. La escena requiere diseÃ±ar/codificar un relato y sus tomas, no es un conversor ni un modelo de generaciÃ³n automÃ¡tica.

La fuente mÃ¡s completa es mromidev; Brinderr ofrece una versiÃ³n reescrita para Claude y plantilla Eiffel. Las dos son repositorios independientes (`fork=false`), no un fork Git directo. Brinderr README atribuye el concepto y formula look a mromidev; su LICENSE atribuye copyright tanto a Bruno DuhÃ¡r como a Mr omi. No describir ninguÌn repositorio como â€œfuente originalâ€ Ãºnica sin mÃ¡s procedencia.

## Revisiones y contenido

| Repo fijado | Contenido, estado y lÃ­mites |
|---|---|
| [`mromidev/claude-animated-shorts@e3b817b6afc6cd413466d43f11ba31209e034bbf`](https://github.com/mromidev/claude-animated-shorts/tree/e3b817b6afc6cd413466d43f11ba31209e034bbf), README fechado 2026-11-01 | CÃ³digo/docs MIT. Un proyecto ejemplo Remotion + Three.js, vertical 1080Ã—1920/30fps y 55â€“70 s; Bridge scene, controles de luz/mundo/cÃ¡mara, scripts QA/stills y audio procedural Python. README dice `public/` alrededor de 1.3 GB, y el skill advierte que Remotion copia ese Ã¡rbol a temporales y relata que generÃ³ 60+ GB/ENOSPC y otros 110 GB de temporales en sus propias iteraciones. Esas son advertencias/experiencias del upstream, no tamaÃ±os medidos en la mÃ¡quina actual. Incluye 38 fotogramas y 20 hojas de contacto (1,200 frames anunciados) de otras shorts para â€œstyle study onlyâ€. No copiar/publicar esos frames, shorts, voice, guion, personajes o referencias; el aviso de estilo no es una licencia de medios. |
| [`brinderr/animated-shorts@3569877f7352623a91f514237c5fb5945fa659b1`](https://github.com/brinderr/animated-shorts/tree/3569877f7352623a91f514237c5fb5945fa659b1), README fechado 2026-11-06 | README declara necesitar Claude Code/plan pagado, ofrece instalar herramientas automÃ¡ticamente si se aprueba y pide copiar estilo de shorts al estudiar frames. Declara HyperFrames + Three.js; contiene un solo ejemplo Eiffel 57 s a 1080Ã—1920/30fps. README recomienda free; licencia raÃ­z contiene MIT y atribuye porciones a mromidev. GitHub API marca `NOASSERTION`, aunque la revisiÃ³n sÃ­ contiene archivo LICENSE: verificar avisos/terceros y no tratar la etiqueta API como prueba de concesiÃ³n completa. No se requiere para el flujo local OPENMONTAGE. |

La comparaciÃ³n de las dos SKILL.md fijadas encontrÃ³ formato/pasos reescritos (167 lÃ­neas frente a 111 y 13 coincidencias exactas de lÃ­nea); no existe relaciÃ³n Git de fork. Se conservan las atribuciones que los autores escribieron y no se traslada contenido audiovisual.

## Motores, costo y licencias

- **Three.js** ya tiene guÃ­a y soporte en el Ã¡rbol OPENMONTAGE; Remotion y HyperFrames son rutas separadas. El ejemplo mromidev importa `three`, `@remotion/three`, React Three Fiber y postprocessing; no publica manifest/lockfile de paquetes en la raÃ­z. Brinderr usa HyperFrames; el repo local ya tiene perfil offline, por lo que no hace falta adoptar otro motor.
- **Remotion no es simplemente MIT ni â€œgratis para toda empresaâ€.** Su licencia/terms oficiales consultados el 2026-11-27 permiten uso Free a personas, organizaciones de hasta 3 personas, organizaciones sin fines de lucro elegibles o evaluaciÃ³n no comercial. Si OPENMONTAGE/operador no califica, Remotion for Creators cuesta US$25/seat/mes; Automators cuesta US$0.01 por render con mÃ­nimo US$100/mes. La excepciÃ³n local se refiere a no pagar los *renders* del plan, no a que todo usuario empresarial sea elegible. No asumir elegibilidad organizacional; en un futuro validar el tipo/headcount del titular antes de que costo sea $0. Fuentes: [licencia y precios](https://www.remotion.dev/docs/license/pricing), [FAQ](https://www.remotion.dev/docs/license/faq), [terms](https://www.remotion.dev/docs/terms).
- **HyperFrames, GSAP, Three.js, postprocessing, fuentes y Python audio** tienen sus propias versiones/licencias. El permiso MIT de la plantilla no los relicencia. Antes de usar Remotion para distribuir o automatizar un editor, revisar tÃ©rminos actuales aplicables; no inferir derechos a partir del README del skill.
- Las voces estÃ¡n por grabar/generar separadamente (la plantilla exige `voice.wav` y palabras temporizadas); para costo $0 utilizar voces/ASR locales ya aprobados y con licencia apta. No repetir Qwen/Piper/Chatterbox ni importar audios ajenos.
- El cÃ³digo audio genera mÃºsica/FX procedural con Python, pero no da por sÃ­ mismo una autorizaciÃ³n comercial independiente de cada dependencia/resultado. SFX externos corresponden a #177 y requieren recibo/licencia por archivo.
- El flujo **puede** ser local/offline despuÃ©s de preparar tooling y recursos locales; no se validÃ³ aislamiento de red, descarga inicial, Windows ni tiempo/espacio de render. No instalar Remotion ni paquetes y no asumir que fuera de red funcione desde primera ejecuciÃ³n.

## Conexiones y lÃ­mites de las instrucciones externas

- Los README instruyen copiar skills a carpetas Claude y pedir a Claude que cree el short; Brinderr indica plan Claude pago. Esas instrucciones son documentaciÃ³n no confiable durante evaluaciÃ³n; no ejecutadas ni migradas a Codex.
- Mromidev requiere proyecto Remotion previo, `@remotion/three`, Node, Python 3 y FFmpeg; propone ejecutar `npx remotion render`, generar voz/word timings y usar Python scripts. No se vieron en la revisiÃ³n una `package.json`, lockfile o requirements pinning en el root/Ã¡rbol consultado; dependencia reproducible y versiÃ³n Windows no quedan establecidas.
- El skill recomienda enviar MP4/memorias y borrar `remotion-webpack-bundle-*` y perfiles de Chromium del temp cuando â€œno haya rendersâ€; no seguir comandos de borrado externos ni tocar temporales compartidos como parte de esta evaluaciÃ³n.
- La escena Brinderr trae ruta local `templates/eiffel-tower/assets/scene.js`; no se importÃ³/ejecutÃ³. La inspecciÃ³n de cÃ³digo puntual no acredita todos los mÃ³dulos/transitivos ni que no haya recursos remotos en un proyecto renderable.
- Las â€œ20 reference shortsâ€ y las 38 capturas/20 sheets no tienen recibo de licencia de cada vÃ­deo visible en el README consultado. Solo sirven al upstream para anÃ¡lisis de estilo; no son assets aprobados de OPENMONTAGE.

## ComparaciÃ³n con capacidades existentes

| Existente / issue | AplicaciÃ³n concreta sin duplicados |
|---|---|
| #159/#164 (direcciÃ³n, hechos, guion, propuestas) | Mantener fuentes/fecha para toda afirmaciÃ³n narrativa, guion ES/EN editable y tres propuestas; no copiar la historia Broughton, beats ni personajes del ejemplo.
| #158 (perfiles de personajes) | Perfil propio, ID/versiones/cuenta y referencias autorizadas; distinguir diseÃ±o 2D importado/manual de rig, generaciÃ³n, animaciÃ³n facial o consistencia, que son capacidades separadas.
| #174/#178 (timeline y line art) | Usar capas/overlays y reglas de contorno/zonas seguras ya integradas; toda capa debe compartir proyecto, reloj, undo/reopen. No construir segunda timeline.
| #177 (SFX) | Insertar solo sonidos cuya fuente/licencia estÃ©n registrados. Las pistas de ejemplo/MIDI y frames se excluyen mientras no tengan derechos confirmados.
| #186/#132 (Remotion/HyperFrames/GSAP) | Reutilizar runtime/perfil actual aprobado; por defecto no aÃ±adir Remotion si no existe la ruta habilitada/elegible. Mantener export offline y reproducible desde recursos locales.

## Criterios de aceptaciÃ³n de un futuro piloto

1. Una escena corta con recursos diseÃ±ados/propios, nada de voces/modelos nuevos: registrar versiones, sistema operativo, runtime y licencia elegible antes del render.
2. Un solo reloj por frame absoluto; renderizar el mismo frame en orden no secuencial debe producir pixel hash consistente, y preview/export deben coincidir.
3. Personajes/cÃ¡mara/capas se editan/reabren en la timeline compartida; las fuentes, texto, tiempos y ajustes pueden corregirse manualmente y deshacerse.
4. Probar tanto vertical 9:16 como horizontal 16:9 con zonas seguras y sin stretch/recorte oculto; longitud corresponde al brief, no a la regla rÃ­gida de 55â€“70 s.
5. Verificar export/cancelaciÃ³n, audio y sincronÃ­a sÃ³lo si se cambia el motor o el flujo. Validar espacio temporal antes de render y no borrar temporales ajenos.
6. El primer render offline debe demostrar cero requests externos y listar recursos faltantes; no basta con que archivos estÃ©n cacheados.

## VerificaciÃ³n y lÃ­mites

- Revisados commit/tree, READMEs, LICENSE, SKILL.md, muestra de template/cÃ³digo/audio y metadatos de ambos repos. Se comprobÃ³ que ambos repositorios no son Git forks directos y que Brinderr atribuye porciones a mromidev.
- Contrastados los tÃ©rminos actuales de Remotion (consultados 2026-11-27) y el solapamiento con issues/capacidades locales ya existentes.
- ComprobaciÃ³n documental focalizada: fijaciones, atribuciÃ³n, material de referencia separado, requisitos, costo condicional, temporales, colaboraciÃ³n Windows no validada y aceptaciÃ³n sin crear otro runtime.
- No se descargÃ³ la carpeta de imÃ¡genes/hojas de contacto de mromidev, no se instalÃ³ Remotion/HyperFrames/Three.js, no se ejecutaron scripts, no se probaron conexiones externas, no se produjo voz ni se renderizÃ³.

## AceptaciÃ³n de la evaluaciÃ³n

- [x] Dos candidatos y origen/crÃ©ditos contrastados con revisiÃ³n y licencia.
- [x] Diferencia entre cÃ³digo MIT, Remotion, runtime y assets documentada.
- [x] Solapamiento con #132/#158/#159/#164/#174/#177/#178 registrado sin duplicar tareas.
- [x] Costo $0 condicionado a elegibilidad Remotion y a no depender de servicios.
- [x] Sin instalaciÃ³n, descarga ni contenido generado.
- [ ] Piloto de escena local: no solicitado ni realizado; queda como aceptaciÃ³n futura tras comprobar elegibilidad y runtime disponible.

