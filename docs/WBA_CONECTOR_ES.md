# Rankings WBA para agentes

Herramienta `official_wba_live`, capacidad `boxing_rankings`. Consulta nueva a https://www.wbaboxing.com/wba-ranking sin clave, modelos ni API de pago.

- `rankings`: devuelve puestos 1–15 por división del ranking masculino.
- `resolve_boxer`: recibe `name`, normaliza acentos/mayúsculas y devuelve candidatos oficiales. No escoge arbitrariamente entre homónimos.

Cada registro conserva puesto, división, nombre, ID de perfil, país y procedencia. Se separa el mes publicado (`as_of_month`) de la fecha de consulta (`retrieved_at`). El mes puede ser anterior al actual: no debe anunciarse como actualizado al día. Las vacantes «NOT RATED» conservan nombre e ID nulos; no se inventa un boxeador. Formatos inesperados, duplicados o divisiones incompletas producen error sin respaldo antiguo.

El 20-11-2026 se comprobó la página oficial: 17 divisiones y 255 puestos, con mes de referencia 2026-10. Se comprobó además la resolución por nombre de Tyson Fury. Estos datos no se guardaron como base estadística para futuras producciones.

## Límites

No incluye campeones situados fuera de los puestos 1–15, ranking femenino, récord de combates, nocauts ni rankings de otros organismos. Un boxeador no encontrado puede ser campeón o estar clasificado en otra categoría u organismo; no inferir lo contrario. El texto de títulos regionales se conserva literalmente, sin transformarlo en palmarés verificado. El acceso a la información no da permiso para reutilizar fotos, logos o videos.

El agente puede usar el resultado para investigación y guion. La plantilla gráfica FIFA/UEFA/MLB todavía no admite este informe de ranking; falta esa adaptación visual y una fuente específica para los récords de combates.
