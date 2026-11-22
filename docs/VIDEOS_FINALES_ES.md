# Manual de Videos finales

Abre **Videos finales** en el menú del Estudio y pulsa **Actualizar videos finales**. La lista lee los recibos del disco de proyectos activo. «Disponible» significa que el archivo existe en ese momento; aún no se ha comprobado su hash. Si el disco está desconectado, la app lo indica en vez de mostrar una lista vacía.

## Revisar un proyecto

1. Expande el proyecto. Revisa el estado técnico, la selección deportiva asociada si existe, y si la copia final sigue vigente.
2. Pulsa **Abrir proyecto** para ver el video y sus artefactos. Una verificación técnica confirma formato, decodificación y hashes guardados durante el render; revisa tú la calidad visual y la exactitud del contenido.
3. Pulsa **Comprobar integridad ahora** cuando necesites confirmar el estado actual de los archivos. La app calcula SHA-256 de los renders y, si hay una entrega registrada, de sus copias. Muestra por archivo si coincide, falta, cambió, no puede leerse o tiene una ruta o recibo inválido. Repetir la comprobación sustituye el resultado anterior.

La comprobación es local, de solo lectura y se limita a dieciséis salidas por proyecto. Lee en bloques de 4 MiB; con videos grandes puede tardar. No inicia modelos ni publica videos. Comprueba bytes, no calidad editorial, licencias ni derechos.

## Cuando aparece «revisar datos o revisión»

Una selección deportiva modificada o una solicitud de cambios posterior al render deja el recibo anterior como histórico. Los archivos se conservan. Produce y verifica el video actualizado antes de tratarlo como vigente. Una nueva verificación también deja histórica cualquier copia final previa cuyo origen y SHA-256 no correspondan al render nuevo.

Si falla únicamente la copia al disco final y el render conserva verificación vigente, abre el proyecto y pulsa **Reintentar entrega verificada**. El sistema comprueba las etapas y el expediente vigente, y copia sin regenerar. Rechaza una verificación anterior a una revisión o selección nueva. La publicación en redes sigue siendo una acción separada.

Consulta [Cola de producciones](COLA_PRODUCCIONES_ES.md) para el orden y los reintentos, y [Estudio de producción](ESTUDIO_PRODUCCION_ES.md) para crear y aprobar proyectos.
