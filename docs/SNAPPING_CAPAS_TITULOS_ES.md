# Snapping a capas y títulos — #106, E04/#92

Continuación independiente de #105, carencia registrada en #93/04898cf. Se
reutilizan `editPoints` y `snapTime` del editor; no se añade otro motor ni se
cambia el contrato EDL o el contenido del proyecto.

Con ajuste activado, los gestos que ya usaban puntos temporales reconocen
ahora entrada/salida de capas y títulos. El final de capa es start+(out-in)/speed
en tiempo de montaje, nunca los offsets del archivo fuente. Las capas bloqueadas
pueden ser referencia sin modificarse. El umbral existente8px y desactivación
de snapping conservan su comportamiento. No se añaden keyframes o gestos de
capas que esta entrega no implementa. El posterior comando utiliza el mismo
EDL/revisión/undo del agente; calcular referencias no escribe el proyecto.

Prueba nueva con datos numéricos offline: límites/títulos, velocidad2/.5,
offsets de fuente, inmutabilidad, bloqueo, umbral, modo desactivado, arrays
opcionales e intervalos inválidos. No se repite la suite antigua de aritmética.
No AV, visualización local o interacción de ratón certificadas por estos casos.
No reiniciar servidor, modificar configuraciones ni ComfyUI. Código de UI
necesita recarga; compatibilidad/backend siguen el aviso de #105.
