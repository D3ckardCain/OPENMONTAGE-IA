# Memoria del proyecto en el panel del agente

La memoria visible en Studio se limita al proyecto seleccionado. El panel muestra preferencias y decisiones, referencia de origen, versión del proyecto y si la entrada corresponde a la revisión actual. El contenido se presenta como contexto; no sustituye las instrucciones vigentes.

- Añadir acepta preferencias explícitas y decisiones creativas con referencia de origen obligatoria.
- Corregir crea una versión nueva y retira la anterior del índice; conserva ambas como recibos.
- Retirar del índice usa una tombstone. No borra el recibo ni los originales.
- Mientras el agente trabaja o el backend no coincide con el código en disco, la memoria queda en solo lectura.
- La lista devuelve hasta 50 entradas recientes. Más historial se señala; el endpoint admite un máximo de 100.
- El panel consulta y escribe solo rutas locales del proyecto; no usa modelos, red externa ni telemetría.

Los endpoints GET y POST /api/studio/projects/{project_id}/memory comparten la base SQLite y funciones de lib/project_memory.py usadas por el agente. El POST rechaza campos desconocidos, limita la edición manual a preferencias/decisiones y bloquea escrituras con un agente activo. Si una respuesta de escritura es incierta, la interfaz relee la lista en vez de repetir la mutación.
