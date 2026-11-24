# STE80 Humanizer — evaluación #91

24-11-2026, #3. [Dodaios/ste80-humanizer fijado](https://github.com/Dodaios/ste80-humanizer/tree/ace4484da2d81dda97861e004c37c0a2e93896d1). README, LICENSE, THIRD_PARTY_NOTICES y scripts/ste_check.py revisados como datos. Commit fija fuente; no se toma un número de estándar o regla como versión instalada de aplicación.

MIT con avisos; THIRD_PARTY_NOTICES incluye catálogo adaptado de blader/humanizer, copyright Siqi Chen2025/MIT. No incluye licencia para redistribuir especificación/diccionario ASD-STE100; marcas y recursos gráficos conservan derechos propios. El repositorio declara reglas parafraseadas y no contiene el estándar. **STE80 no certifica ASD-STE100 ni determina autoría humana/IA; evasión de detectores no es objetivo.**

## Windows, offline y costo

Manifiesto `.claude-plugin/plugin.json` declara **4.0.0** en la misma revisión; metadato leído, sin instalar plugin ni confundir versión del plugin con ASD-STE100 Issue9.

El docstring del checker declara **Python3.8+**; esto precisa el README genérico y no constituye una ejecución verificada en3.8/Windows. `--json` emite hallazgos por línea/regla y salida1 significa hallazgos,2 error de uso: el puente debe distinguir esos estados. Su `STRICT_ONLY_SWAPS` propone should→must y may→can: no aplicar automáticamente a texto protegido, porque cambia modalidad/certeza. WORD_RE centra letras A–Z, razón concreta para no usarlo como contador español sin adaptación.

Checker Python usa biblioteca estándar, sin dependencias runtime declaradas; debe verificarse sintaxis/CLI con intérprete aislado antes de adopción. No se deduce piso Python preciso de “Python” en README. Windows con Python preparado puede leer archivos/texto, sujeto a Unicode/CRLF/rutas/permisos. No GPU/modelo para checker; RAM/disco ligados a longitud, sin benchmark local. Reescritura requiere agente/modelo distinto del checker; Ollama existente, sin API pagada ni otra descarga, es ruta conceptual. Evals upstream llaman agente con permisos Write/Edit/Bash: no ejecutarlos ni instalar skill/plugin/global.

Reglas/texto presentes pueden analizarse offline$0, pero no se ejecutó diagnóstico ni reescritura aquí. No afirmar calidad española por ejemplos en inglés o cuatro casos evaluados por upstream.

## Reutilizar #48/E07, sin otro humanizador

[Evaluación #48](EVALUACION_AVOID_AI_WRITING_ES.md) ya define diagnóstico opcional, reglas versionadas, lengua/offsets, unscored/error, corpus español, preservación y diff. `lib/script_diagnostic.py` y reviewer siguen base. STE80 aporta separación de procedimiento/descripción, condición antes de acción y consistencia terminológica; incorporarlas solo como extensiones de E07, no otro motor/score/gate global.

ASD-STE100 es **inglés**: regex de pasiva, tiempos, phrasal verbs y listas léxicas no se trasladan a español. Límites20/25palabras y6frases son heurísticas contextuales, no calidad universal. Narrativa, poesía, citas y ritmo del autor necesitan modo propio; no aplicar una idea/frase como regla rígida a ficción.

| E07, ampliación acotada | Aceptación futura con strings/mocks |
|---|---|
| Diagnóstico por género/idioma | Hallazgo con regla/version/span/explicación; técnico, deportivo, bíblico y narrativo incluyen negativos/falsos positivos. No-supported/unscored y error separados de limpio. Ninguna reescritura al diagnosticar. |
| Fidelidad antes que score | Candidato/diff separados del original/hash. Preservar cifras/unidades/nombres/citas/atribución, sujeto, negación y modales: puede/no implica debe;40+ no se vuelve40. Contradicción se señala, no se inventa resolución. |
| Términos y condiciones | Glosario de proyecto versionado, mismo concepto/terminología sin reemplazar nombres propios; condición→acción conserva alcance y orden causal. Regla no añade actor/causa desconocidos por exigir voz activa. |
| Revisión trazable | Aceptar/rechazar sugerencia por regla y conservar motivo; evidencia de mejora lingüística aparte de schema/mocks. JS UTF-16/Python puntos de código y CRLF/emoji no desplazan resaltado. |

No nuevos IDs ni instalación. Evaluación completada; español, equivalencia semántica y precisión requieren validación lingüística posterior. Sin contenido del usuario reescrito, inferencia, modelos, paquetes o configuración cambiada.
