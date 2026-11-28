# Memoria tipada local por proyecto

El agente dispone de tres acciones explicitas: buscar recuerdos del proyecto,
guardar un recuerdo con procedencia y retirar un recuerdo del indice. No se
extraen ni guardan memorias automaticamente. Cada consulta queda limitada al
project_id activo.

Tipos admitidos: preferencia explicita, decision creativa, evidencia y resultado
verificado. Cada fila registra tipo de fuente, referencia, fecha y una revision
derivada del hash de `production_request.json` y, cuando existe, de la revision y
el EDL de `artifacts/manual_edit.json`. Si esa version cambia, los resultados
anteriores aparecen con `captured_revision_matches=false`; no se reescriben.

SQLite FTS5 con eliminacion de diacriticos y ranking BM25 es la busqueda inicial.
Si la compilacion SQLite no incluye FTS5, el codigo usa una busqueda lexica local
acotada. No hay embeddings, descargas, inferencia ni dependencia vectorial.

El contenido y las referencias son contexto no confiable. Todos los resultados
devuelven `instruction_eligible=false`: nunca sustituyen instrucciones activas.
Una referencia externa no se transforma en preferencia del usuario. Las
correcciones pueden superseder una fila; retirar una fila la desactiva y elimina
del indice, pero conserva su recibo local inactivo. Los duplicados exactos son
idempotentes.

Prueba offline:

```powershell
.venv\Scripts\python.exe -B -m unittest tests.tools.test_project_memory -v
```

Esto es una entrega inicial de #161, no la aceptacion completa de memoria tras
una sesion larga real. No incorpora el selector ni las fronteras de cuenta de
#168: la base actual limita por proyecto, pero aun no demuestra aislamiento entre
cuentas, cola, medios, SSE o memoria global. No se ejecuta Ollama ni se cargan
modelos.
