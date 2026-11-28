# Ocho descargas LongCat/Wan: esperar confirmación de finalización

Actualización del usuario, 26 de noviembre de 2026: **NO han terminado**. Esta nota registra rutas proporcionadas, no comprueba existencia, tamaño, progreso ni contenido.

| Contenido | Carpeta nueva de descarga |
|---|---|
| LongCat Single 1–6 | `F:\OPENMONTAJE-IA\DESCARGAS_MODELOS\LongCat-Avatar-VERIFICAR\avatar_single` |
| LongCat Multi 1 | `F:\OPENMONTAJE-IA\DESCARGAS_MODELOS\LongCat-Avatar-VERIFICAR\avatar_multi` |
| Wan VACE High | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-VACE-High-VERIFICAR` |

Fuentes/versiones/tamaños/hashes esperados y destinos definitivos ya están fijados en [la tabla LongCat/Wan](LONGCAT_AVATAR_WAN_PLAN_ES.md), commit `ec748f62dbb2690af5ec47ae26236193bd74304b`. No reiniciar el inventario ni releer pesos ya verificados.

Solo después de que el usuario confirme que terminaron:

1. Localizar únicamente los ocho nuevos archivos de estas carpetas; excluir temporales o archivos que sigan activos.
2. Verificar cada peso completo una vez contra tamaño/SHA256/estructura oficial fijados, reutilizando cualquier recibo válido para esa misma identidad y metadatos. No cargar modelos.
3. Comprobar índices, configuraciones y los demás fragmentos dependientes con los resultados guardados, antes de sustituir. Single y Multi mantienen índices/conjuntos separados; conservar Multi 2–6 correctos ya existentes.
4. Integrar en las ubicaciones definitivas y actualizar rutas/recibos. Confirmar identidad de los volúmenes y verificación de la transferencia. Dentro del mismo volumen puede conservarse identidad mediante movimiento atómico; no repetir un hash grande sin causa.
5. Eliminar los anteriores sustituidos únicamente después de acreditar copia final y dependencias. No borrar otros modelos ni dejar copias redundantes. Las carpetas `VERIFICAR` se eliminan solo si están vacías, sin borrado recursivo de contenido desconocido.

La autorización es condicional a esa confirmación; el tiempo transcurrido no la sustituye. Mientras tanto se continúa #174/#177. No se ha consultado ninguna de las tres carpetas indicadas en esta entrega.
