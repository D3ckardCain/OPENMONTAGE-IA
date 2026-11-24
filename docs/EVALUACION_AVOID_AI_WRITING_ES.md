# avoid-ai-writing — evaluación #48

24-11-2026 UTC. Fuente oficial fijada:
[cd5573a1](https://github.com/conorbronsdon/avoid-ai-writing/tree/cd5573a185f3ab468b094fc2cf2fa193fcaeaf53),
HEAD consultado; package/SKILL3.39.0. Revisión estática de detector, categorías,
validador y CLI; instrucciones externas tratadas como datos, no instaladas ni adoptadas
como política de la sesión. No se analizó un guion del usuario ni se reescribió contenido.

## Decisión y comparación

Adoptar potencialmente un diagnóstico editorial optativo y explicable, no un detector
de autoría ni una reescritura automática. Mantener original/voz y el revisor actual.

| Función | Ya disponible en OPENMONTAGE | Carencia / reutilización propuesta |
|---|---|---|
| Integridad del guion | `script_diagnostic.py`: esquema, IDs, tiempos, palabras, estimación de locución y referencias declaradas | No duplica esas verificaciones. Añadir hallazgos de estilo con fragmentos/ubicación, regla y lengua |
| Revisión editorial | Directores de guion y `skills/meta/reviewer.md` ya exigen hechos/fuentes, revisión y aprobación | Un catálogo determinista puede hacer visibles repeticiones/plantillas; no debe reemplazar el juicio editorial |
| Preservación | Artefactos/checkpoints/historial y procedencia existentes | Comparación antes/después de citas, cifras y estructura es útil. El validador upstream es mecánico, no prueba equivalencia semántica |
| Reescritura | Ollama/LocalAgent locales y control de revisión | Solo propuestas de diff autorizadas en fase futura; sin proveedor nuevo, gate global o edición directa del JSON del guion |

Fuentes: [detector](https://github.com/conorbronsdon/avoid-ai-writing/blob/cd5573a185f3ab468b094fc2cf2fa193fcaeaf53/detector/patterns.js),
[categorías](https://github.com/conorbronsdon/avoid-ai-writing/blob/cd5573a185f3ab468b094fc2cf2fa193fcaeaf53/detector/CATEGORIES.md),
[preservación](https://github.com/conorbronsdon/avoid-ai-writing/blob/cd5573a185f3ab468b094fc2cf2fa193fcaeaf53/detector/validate.js).
No se ha validado cada patrón mediante ejecución ni se ha medido precisión local.

## Idioma, resultados y límites

El propio SKILL declara calibración para inglés. Reglas de vocabulario/gramática,
frecuencias y umbrales no pasan automáticamente a español. Separar `en`, `es` y
mezcla; etiquetas en español no convierten un detector inglés en multilingüe.
En español se necesitan reglas/falsos positivos propios: acentos, ¿¡, ñ, registro,
terminología técnica y citas. No penalizar sistemáticamente a hablantes no nativos.

El [README del detector](https://github.com/conorbronsdon/avoid-ai-writing/blob/cd5573a185f3ab468b094fc2cf2fa193fcaeaf53/detector/README.md)
describe score, clasificación y probabilidades. El panel propuesto solo mostrará
hallazgos de calidad, no HUMAN_ONLY/AI_ONLY como veredictos ni probabilidades de autoría.
UNSCORED incluye texto vacío/corto, escritura no soportada o más de10,000palabras;
score0 ahí no significa limpio. Un fallo de herramienta tampoco es ausencia de problemas.

La protección debe abarcar hechos, cifras/unidades, fechas, negaciones, sujetos,
comparaciones, incertidumbre, citas/atribución, versículos y estadísticas deportivas.
Aunque un validador conserve números, puede perder una negación o cambiar quién hizo
qué. Requiere invariantes de dominio y revisión humana/editorial, no solo score menor.
Offsets JS UTF-16 y texto normalizado deben mapearse al original antes de resaltar;
probar CRLF, Unicode y emojis, no aplicar posiciones a ciegas sobre JSON o bytes.

## Licencia, dependencias y offline

[MIT](https://github.com/conorbronsdon/avoid-ai-writing/blob/cd5573a185f3ab468b094fc2cf2fa193fcaeaf53/LICENSE):
conservar copyright/licencia en adaptaciones sustanciales; OPENMONTAGE sigue AGPLv3.
Las fuentes de corpus citadas por upstream tienen derechos propios: no redistribuir
corpus ni presentarlo como evidencia propia. Fijar versión/hash de reglas adoptadas.

[package.json](https://github.com/conorbronsdon/avoid-ai-writing/blob/cd5573a185f3ab468b094fc2cf2fa193fcaeaf53/package.json)
exige Node>=18 y el detector se declara sin dependencias de runtime ni API. Node ya
preparado es suficiente para una evaluación ejecutable futura, sin npm install en
.venv/ComfyUI. El [CLI](https://github.com/conorbronsdon/avoid-ai-writing/blob/cd5573a185f3ab468b094fc2cf2fa193fcaeaf53/bin/avoid-ai-writing.js)
lee texto/archivos y emite diagnóstico; el gate y scripts de corpus son vías distintas.
No ejecutar corpus:fetch, normalizadores con --write ni instalar hooks por esta revisión.
Detección sobre texto/reglas presentes puede ser offline y costo externo$0; reescribir
requiere el agente local preparado y recursos disponibles, sin fallback comercial.

## Tareas futuras con aceptación

| Prioridad | Tarea | Aceptación |
|---|---|---|
| P0 | Contrato de diagnóstico | ID/versión de regla, lengua, fragmento y offset verificables, severidad editorial y estado unscored/error separado; timeout/tamaño acotados y cero mutaciones |
| P0 | Perfil español | Corpus sintético de positivos/negativos por regla, registro técnico/deportivo/bíblico, métricas de falsos positivos y revisión de ambigüedades; no reutilizar umbrales de autoría |
| P1 | Preservación y diff | Original/hash y candidato aparte; invariantes numéricas/citas/negaciones/atribución, estructura y offsets; rechazo de cambios de hechos aun si baja el score |
| P1 | Studio/agente | Reusar diagnóstico de guion y revisor; explicar sugerencias, permitir descartarlas y conservar decisiones. Pruebas con Ollama simulado; no reescribir al pulsar Diagnosticar |
| P2 | Contexto acotado | Cargar solo reglas/referencias pertinentes, no SKILL.full completo en cada turno; versionado y pruebas de migración sin borrar opiniones editoriales previas |

No se ejecutaron detector, Node, pruebas upstream o modelos en esta evaluación.
No se promete evasión de detectores, prueba de autoría o una tasa de error española.
Evaluación completada; implementación/validación lingüística quedan pendientes.
