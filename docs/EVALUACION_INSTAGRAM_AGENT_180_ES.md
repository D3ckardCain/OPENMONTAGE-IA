# EvaluaciÃ³n de Instagram Agent #180

Fecha: 2026-11-27. RevisiÃ³n documental y estÃ¡tica, sin ejecutar las instrucciones de los repositorios como skills.

## Identidad y revisiones

| Referencia fijada | QuÃ© es | Licencia/requisitos | DecisiÃ³n |
|---|---|---|---|
| [`nategoldai/instagram-agent@acd7615e7ad906809cd65284d70319dd7fe4dfac`](https://github.com/nategoldai/instagram-agent/tree/acd7615e7ad906809cd65284d70319dd7fe4dfac) (2026-10-07) | README anuncia 13 skills Claude: Reels y 26 fÃ³rmulas de hook, captions, carousels, stories, score de perfil, plan, anÃ¡lisis â€œviralâ€, comentarios/replies/DM y humanizer. README afirma que no publica, no usa API y calcula sus cinco herramientas localmente sobre texto. | MIT; licencia raÃ­z indica copyright Jake Schincariol, aunque el README se presenta como â€œby NateGoldâ€. Requiere Python para scripts; no muestra una dependencia pip externa en los scripts revisados. | Referencia de estructura editorial. No afirmar que el repositorio sea la fuente original del trabajo ni copiarlo sin preservar avisos y resolver la procedencia/atribuciÃ³n del fork.
| [`Domotech-Solutions/instagram-agent-chatgpt@d53a2d5bf244824e72a2f280c847125604965497`](https://github.com/Domotech-Solutions/instagram-agent-chatgpt/tree/d53a2d5bf244824e72a2f280c847125604965497) (2026-10-07) | AdaptaciÃ³n independiente portable para ChatGPT/Codex, 14 skills, setup de voz en espaÃ±ol/inglÃ©s, datos de usuario, captions y carruseles; README dice que no publica, comenta, sigue, da like ni envÃ­a DM automÃ¡ticamente. Se identifica derivado de Jake Schincariol. | MIT con copyright de Jake Schincariol y Domotech Solutions; seis herramientas Python declaradas como estÃ¡ndar. InvestigaciÃ³n opcional por browser de forma pequeÃ±a/read-only, `yt-dlp` o renderer de carruseles; no se instalan por defecto. | Encaja mejor como referencia de instrucciones para Codex, pero no hay razÃ³n para aÃ±adir un segundo pack de skills ni otra ruta de estado. Las instrucciones no son polÃ­ticas ni acciones de publicaciÃ³n.
| [`Jakeschincariol/instagram-agent-skill@d03c56bb598be770c60b201f94237e5d1a4268a6`](https://github.com/Jakeschincariol/instagram-agent-skill/tree/d03c56bb598be770c60b201f94237e5d1a4268a6) (2026-09-13) | Repositorio original que Domotech declara como base; 13 skills Claude, MIT; scripts de evaluaciÃ³n editorial local. | La licencia MIT se refiere al cÃ³digo; no certifica factualidad de consejos, precisiÃ³n de mÃ©tricas ni derechos de ejemplos/perfiles. | Revisado para desambiguar procedencia; no duplicar los otros forks ni considerar su licencia como autorizaciÃ³n para usar contenido ajeno.

No existe una sola publicaciÃ³n con el nombre â€œInstagram Agentâ€. Se mantuvieron los tres repositorios separados y fijados por SHA.

## QuÃ© se puede aprovechar en OPENMONTAGE

- Brief â†’ tres hooks/propuestas â†’ guion hablado y texto en pantalla â†’ caption con ventana de preview â†’ plan semanal editable: encaja en #159/#164 y los controles manuales de #174.
- Guardar un perfil de voz editorial, swipe file y plan con `account_id` estable: #168 requiere espacios aislados por cuenta; no reutilizar perfil de una cuenta en otra.
- Carrusel: especificaciÃ³n editable por pÃ¡gina antes del render, usando #174/HyperFrames local; no incorporar renderer o imÃ¡genes del repositorio ajeno.
- Research: proporciÃ³n de rendimiento relativa a la mediana de la cuenta puede describirse como cÃ¡lculo sobre datos suministrados. Cualquier mÃ©trica debe llevar fuente/URL, fecha, cuenta, muestra y cobertura; no inventar datos ni prometer viralidad.
- El calendario de posteos propuesto es material editorial, no el scheduler o publicaciÃ³n de #169. No OAuth, carga, comentarios, DM, likes o interacciÃ³n automatizada en esta evaluaciÃ³n.
- Adaptar a Ollama solo a travÃ©s del puente existente y con costo $0; los scripts analÃ­ticos son locales deterministas y no necesitan llamada a modelo. Un skill gratuito no implica que un servicio/modelo remoto o una API comercial sea gratuito.

No se propone copiar el cÃ³digo en esta fase: las tareas de editor/planificaciÃ³n ya existen en #159/#164/#174. Si una utilidad concreta se implementa despuÃ©s, se debe conservar MIT/copyright/atribuciÃ³n y auditar el cambio por separado.

## AuditorÃ­a estÃ¡tica de scripts y lÃ­mites

Se revisaron los seis archivos Python que aparecen en el Ã¡rbol del candidato Nate Gold (no cinco): `caption.py`, `detect.py`, `humanize.py`, `beats.py`, `hookscore.py` y `swipe.py`. No se ejecutaron.

- Los mÃ³dulos importan biblioteca estÃ¡ndar y leen archivos de texto/JSON o stdin. `humanize.py` puede escribir el resultado en la ruta dada con `-o`; `swipe.py` puede escribir Markdown en `--out` y crear su carpeta destino. No se observÃ³ `requests`, `urllib`, socket, subprocess ni shell en estos scripts. Es una inspecciÃ³n estÃ¡tica de la revisiÃ³n, no prueba de comportamiento de toda instrucciÃ³n/skill.
- El modo `/ig-viral` describe â€œreading, not scrapingâ€ de muestras pequeÃ±as; aun asÃ­ se basa en la persona/mercado indicados y puede sugerir interacciÃ³n. La adaptaciÃ³n de Domotech prohÃ­be scraping a escala y engagement automatizado; OPENMONTAGE debe conservar ese lÃ­mite.
- `detect.py` estima cinco seÃ±ales de texto y una puntuaciÃ³n â€œhumanâ€; no es detector fiable ni prueba de autorÃ­a. El README y `ig-human/SKILL.md` describen `humanize.py` eliminando caracteres de formato invisibles. Eliminar un separador puede cambiar el texto; siempre presentar antes/despuÃ©s para ediciÃ³n del usuario y jamÃ¡s usarlo como evasiÃ³n de una marca de agua, aviso o detector.
- Las puntuaciones de hook/perfil son heurÃ­sticas no calibradas, no indicadores reales de rendimiento ni promesas de crecimiento. No promover una score 70/100 o â€œPASSâ€ como hecho de audiencia.
- Las reglas de caption que reflejan lÃ­mites visibles o polÃ­ticas de Instagram cambian. Verificarlas contra fuentes oficiales y fecha antes de mostrarlas como lÃ­mites de plataforma.
- El informe no ejecutÃ³ ni auditÃ³ exhaustivamente cada instrucciÃ³n narrativa de las 13/14 skills, paquetes plugin, fuentes de investigaciÃ³n, samples o cualquier browser tool opcional.

## Diferencias frente a los issues actuales

| Ya cubierto / relacionado | QuÃ© falta Ãºtil, sin duplicar |
|---|---|
| #159/#164: planificaciÃ³n, brief audiovisual, propuestas y revisiÃ³n | Interfaz de hook/caption previa a render con variantes ES/EN, datos editables y aprobaciÃ³n explÃ­cita de texto.
| #168: aislamiento por cuenta y estado de agente | Perfil de voz/swipe plan por `account_id`, con migraciÃ³n y pruebas de no fuga. Guardar autorÃ­a/fuente y no inferir transferencia entre cuentas.
| #169: scheduler/publicador y recibos | Mantener el calendario editorial de skills separado del scheduler. Una propuesta no da permiso para publicar.
| #174: editor y catÃ¡logo manual | Preview real del texto y overlay/carrusel con herramientas existentes, no visualizaciÃ³n estÃ¡tica afirmada como render.

No se abre nuevo backlog: los componentes candidatos estÃ¡n expresamente cubiertos por esos issues.

## Criterios de aceptaciÃ³n para una futura adaptaciÃ³n local

1. Mismo proyecto/cuenta y los mismos comandos de revisiÃ³n, aprobaciÃ³n e historial que Studio/agente; guardar/reabrir sin cruzar `account_id`.
2. Fixtures pequeÃ±os ES/EN: acentos, Ã±, puntuaciÃ³n y tono del usuario; revisiÃ³n del significado y negaciones; reportes no afirman â€œhumanoâ€ ni garantÃ­a de engagement.
3. Preview de 125 caracteres, textos de carrusel/overlay y tiempos derivados del guion real; usuario puede editar antes de aplicar. Verificar lÃ­mites actuales solo con URL oficial/fecha.
4. Si existe research, mostrar fuente, fecha, denominador, tamaÃ±o de muestra y campos faltantes. Sin scraping a escala ni engagement artificial.
5. `humanize.py` no se usa para evadir detectores, desmarcar contenido sintÃ©tico ni quitar indicadores de procedencia; se conserva el original y se revisa cualquier cambio.
6. El pack editorial nunca puede publicar/schedule por sÃ­ mismo; acciones de #169 siguen los permisos y confirmaciones de su issue.

## VerificaciÃ³n de esta evaluaciÃ³n

- RevisiÃ³n fijada de los tres repositorios, README, LICENSE, manifiesto/tree y scripts del candidato principal; cruce con #159/#164/#168/#169/#174.
- Chequeo focalizado: nombres/SHA, requisitos, licencias, procedencia, servicios opcionales, lÃ­mites de publicaciÃ³n, escritura a archivo y criterios sin duplicaciÃ³n.
- Sin instalaciÃ³n, descarga, ejecuciÃ³n de scripts, lectura de cuentas/redes, research en Instagram, contenido generado o interacciÃ³n/publicaciÃ³n.
- No se validÃ³ en Windows el runtime, plugins, consejos de crecimiento, privacidad de plugins ni compatibilidad de la UI.

## AceptaciÃ³n de evaluaciÃ³n

- [x] Candidatos desambiguados, revisiones y licencias fijadas.
- [x] Funciones editoriales Ãºtiles relacionadas a backlog existente.
- [x] Scripts auditados estÃ¡ticamente y riesgos documentados sin ejecutarlos.
- [x] Costo $0, offline y lÃ­mites de plataforma/uso distinguidos.
- [ ] Persistencia de perfil y salidas ES/EN de OPENMONTAGE: trabajo futuro en #159/#168/#174.

