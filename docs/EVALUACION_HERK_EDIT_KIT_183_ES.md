# EvaluaciÃ³n de Herk Edit Kit #183

Fecha: 2026-11-27. RevisiÃ³n estÃ¡tica fijada a [`nateherkai/herk-edit-kit@10511e5af86fc47756ea89803b397422e2d89284`](https://github.com/nateherkai/herk-edit-kit/tree/10511e5af86fc47756ea89803b397422e2d89284), anteriormente HyperFrames Student Kit. No se instalÃ³, ejecutÃ³, copiÃ³ ni descargÃ³ el kit.

## DecisiÃ³n

No integrar el kit como un segundo editor ni como una cola de producciÃ³n paralela. Reutilizar selectivamente criterios y contratos dentro de #107, #130, #132 y #174, usando la EDL compartida, palabras/transcripciÃ³n existentes, FFmpeg y GSAP/HyperFrames ya preparados. No repetir ASR, voces ni renders aprobados. No usar ElevenLabs, Kie.ai ni fuentes remotas.

El valor principal estÃ¡ en su estructura de revisiÃ³n: candidatos explÃ­citos antes de aplicar cortes; contexto por palabra; validaciÃ³n de sincronÃ­a; reglas editoriales y componentes grÃ¡ficos versionables. OPENMONTAGE debe mantener una Ãºnica revisiÃ³n/proyecto, historial reversible y responsabilidad humana antes de eliminar material.

## RevisiÃ³n fijada y condiciones

| Campo | Evidencia oficial en la revisiÃ³n | DecisiÃ³n |
|---|---|---|
| VersiÃ³n y runtime | `package.json`: `herk-edit-kit` **2.0.0**, CommonJS, Node **>=22**; dependencias de desarrollo `hyperframes` **0.7.109**, GSAP **3.14.2**, Playwright **^1.59.1**. Requiere Git, FFmpeg/ffprobe y Chrome/Chromium. | No crear otro Node/runtime ni alterar instalaciones. Reutilizar adaptadores y perfil offline existentes. |
| Licencia | RaÃ­z MIT; permiso adicional `licenses/PIPELINE-USE-PERMISSION.txt` para materiales de pipeline. `THIRD_PARTY_NOTICES.md` excluye explÃ­citamente logo, guÃ­a, tokens de marca y contenido de ejemplos AIS del permiso de reutilizaciÃ³n. Fuentes, HyperFrames, GSAP y assets conservan avisos/licencias propios. | MIT del cÃ³digo no concede los assets AIS. No copiar marcas, clips, capturas o ejemplos. Conservar avisos si se reutiliza cÃ³digo sustancial y auditar cada dependencia/asset por separado. |
| Servicios y operaciÃ³n | README dice que el starter sintÃ©tico no necesita API de pago; transcripciÃ³n predeterminada usa ElevenLabs Scribe, Kie.ai es opcional; se puede aportar transcript local o adaptar a Whisper local. La primera ejecuciÃ³n de HyperFrames puede descargar/cachear sustituciones de fuentes. | Perfil offline explÃ­cito: usar palabras guardadas y fuentes locales; fallar con recurso faltante en vez de descarga. No ejecutar setup ni preflight durante esta evaluaciÃ³n. |
| Motion cards | README anuncia **406 tarjetas en borrador**, dos templates de escena, no 406 componentes verificados. Los assets/diseÃ±os de ejemplos tienen restricciones. | Tratar el catÃ¡logo como material de referencia; validar componentes en OPENMONTAGE antes de mostrar disponibilidad o copiar markup. No adoptar la marca ni sus plantillas completas. |

## Capacidades observadas y diferencias

- `cut-silences` lee transcript con palabras y tiempos, propone EDL/decisiones y puede producir un filtro FFmpeg; es distinta de detecciÃ³n de errores del habla.
- `find-cut-candidates` identifica mecÃ¡nicamente repeticiones/posibles retakes/false starts con contexto y confianza. Declara en el cÃ³digo que propone y no decide. `apply-cuts` espera una lista aprobada, genera keep/delete ranges, retemporiza palabras y puede renderizar por FFmpeg.
- `validate-beat-sync` comprueba relaciÃ³n entre beat, `data-anchor` y palabra del transcript; no mide por sÃ­ mismo la inteligibilidad musical o la sincronÃ­a audiovisual final.
- El flujo entrega archivos/EDL auxiliares junto al transcript y render final; no equivale al comando de ediciÃ³n compartido en Studio/agente, historial del proyecto, transacciÃ³n reversible o protecciÃ³n de concurrencia de OPENMONTAGE.
- Hallazgo de localizaciÃ³n importante: `find-cut-candidates.mjs` normaliza con expresiones `[a-z0-9]`. En espaÃ±ol retira letras acentuadas y `Ã±` (p. ej., reduce `acciÃ³n` a `accin`, `aÃ±o` a `ao`). No reutilizar sin normalizaciÃ³n Unicode y casos de regresiÃ³n en espaÃ±ol. La revisiÃ³n no ejecutÃ³ el script: conclusiÃ³n estÃ¡tica por expresiÃ³n regular.
- El README describe Whisper local como alternativa a Scribe, pero el helper provisto usa ElevenLabs; decir â€œcompatible con Whisperâ€ no significa que venga un adaptador local validado. OPENMONTAGE ya tiene transcript ASR local guardado: leerlo sin repetir inferencia.

## Brechas Ãºtiles para OPENMONTAGE, sin duplicar tareas

1. En #107/#130, representar cada corte propuesto con palabras removidas y conservadas, contexto, motivo, confianza, cobertura/origen del transcript y revisiÃ³n humana. Ninguna confianza debe disparar borrado automÃ¡tico.
2. En #130/#174, aplicar los cortes aprobados como un Ãºnico comando reversible a vÃ­deo, audio, capas/tÃ­tulos, subtÃ­tulos, marcadores y keyframes; conservar borde/regla ripple elegida y guardado/reapertura. No usar el renderizador de Herk como una segunda EDL.
3. En #132/#174, adaptar solo tarjetas visuales concretas al catÃ¡logo editable existente. Mantener recursos locales, zonas seguras/plataforma, procedencia, propiedad manual y pruebas de tiempo determinista. No importar los 406 borradores de golpe.
4. Corregir la normalizaciÃ³n lingÃ¼Ã­stica antes de cualquier port de detecciÃ³n: Unicode Letter/Number, espaÃ±ol con acentos/Ã±, puntuaciÃ³n, contracciones y fixtures no audiovisuales; preservar negaciones/contexto y transcript original.

## AceptaciÃ³n para una implementaciÃ³n posterior

- Probar con la copia autorizada y transcript portuguÃ©s/espaÃ±ol ya guardado, sin repetir ASR. Incluir un candidato real y un falso positivo protegido, registrar decisiÃ³n aceptar/rechazar y confirmar que solo se modifica la copia.
- Comparar estructura EDL antes/despuÃ©s; sincronizar vÃ­deo, audio, capas, tÃ­tulos, subtÃ­tulos y marcadores; deshacer/rehacer y guardar/reabrir.
- Verificar el audio/video de salida solo si una modificaciÃ³n de render lo requiere; no repetir renders aprobados por un cambio puramente documental.
- Para grÃ¡ficos, una tarjeta local de prueba con tiempo absoluto, licencia/atribuciÃ³n propia y ninguna peticiÃ³n externa; catÃ¡logo no debe afirmar que todas las cards ajenas son vÃ¡lidas.
- AceptaciÃ³n audiovisual y humana se mantiene separada de revisiÃ³n estÃ¡tica de cÃ³digo/documentaciÃ³n.

## VerificaciÃ³n y lÃ­mites de esta evaluaciÃ³n

- Revisados README, manifest, MIT, permiso de pipeline, third-party notices, scripts de detecciÃ³n/aplicaciÃ³n de cortes, validador de beat-sync y Ã¡rbol de skills/templates de la revisiÃ³n indicada.
- ComprobaciÃ³n documental focalizada: fijaciÃ³n, versiones, Node/requisitos, servicios opcionales, condiciones de assets, pasos ya cubiertos en #107/#130/#132/#174, problema ASCII en espaÃ±ol y aceptaciÃ³n sin duplicar runtime.
- No se ejecutaron `npm ci`, setup, tests, HyperFrames, Chrome, FFmpeg ni transcripciÃ³n. No se comprobÃ³ la compatibilidad de la revisiÃ³n con esta mÃ¡quina ni su estado offline efectivo. No se inspeccionaron descargas/modelos ni proyectos originales.

## AceptaciÃ³n de la evaluaciÃ³n

- [x] SHA upstream y versiones fijadas.
- [x] Licencias y excepciones de assets separadas.
- [x] ReutilizaciÃ³n y carencias verificables documentadas sin importar otro editor.
- [x] No instalaciones, descargas, ejecuciÃ³n ni contenido generado.
- [ ] Pruebas funcionales de los contratos OPENMONTAGE: pertenecen a #107/#130/#132/#174 y a las copias ya autorizadas.

