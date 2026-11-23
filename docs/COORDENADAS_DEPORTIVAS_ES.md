# Coordenadas deportivas locales

El agente descubre `sports_coordinates_doctor` y `sports_coordinates` mediante
la capacidad `sports_coordinate_analysis` del registro de Studio. Son herramientas
locales de costo cero. Lee `tool_info` y las instrucciones de la etapa antes de
usar `execute_tool`. El diagnóstico se llama con inputs `{}`.

El entorno existente `.runtime/sports-analysis/venv` contiene Kloppy 3.19.1 y
MPLSoccer 1.8.1. Se reutiliza sin modificar `.venv`, ComfyUI o las fuentes
oficiales. El adaptador comprueba las versiones y rechaza cambios no validados.
El subproceso usa Python aislado, entrada estándar limitada, tiempo máximo de
45 segundos y auditoría que bloquea sockets. No descarga datos ni crea figuras.

## Entrada y llamada

Guarda un JSON dentro del proyecto con esta estructura de ejemplo sintético:

```json
{
  "source": {"pitch_length_m":105,"pitch_width_m":68,"unit":"normalized","origin":"top_left","y_axis":"down"},
  "target": {"pitch_length_m":105,"pitch_width_m":68,"unit":"m","origin":"bottom_left","y_axis":"up"},
  "points": [[0,0],[0.5,0.5],[1,1]]
}
```

Después llama `execute_tool`:

```json
{"name":"sports_coordinates","inputs":{"project_id":"mi-proyecto","input_path":"assets/coordinates.json","output_path":"artifacts/coordinates-report.json"}}
```

Longitud y anchura son medidas físicas en metros y se exigen en ambos sistemas.
No se inventa un campo de 105x68 cuando faltan. Esta operación conserva el mismo
campo físico; rechaza dimensiones distintas entre origen y destino. El alcance
es fútbol de campo, longitud 70–130 m, anchura 40–100 m y longitud mayor a anchura.
No se presenta como validación reglamentaria de un estadio.

Unidades admitidas: `m`, `cm` y `normalized`. Eje X longitudinal creciente a la
derecha. Origen `top_left` exige Y `down`, `bottom_left` exige Y `up`; `center`
admite ambas orientaciones de Y. El sistema normalizado ocupa 0–1 con origen en
una esquina, o -0.5–0.5 con origen central. Las coordenadas métricas se ajustan
a la longitud/anchura declaradas. No se infieren dirección de ataque, periodo,
posesión o cambios de lado. Estos conceptos requieren metadatos y otra operación.

## Puente y resultado

Se construye `CustomCoordinateSystem` de Kloppy con dimensiones explícitas.
Sus métodos públicos `Dimension.to_base/from_base` convierten hacia un campo
métrico con origen inferior izquierdo. La API pública `mplsoccer.Standardizer`
produce además coordenadas StatsBomb 120x80 y comprueba la conversión inversa.
Así se evita el método experimental `to_mplsoccer()` que en estas versiones
importa un módulo trasladado. No se modifica ninguna biblioteca ni se introducen
alias de módulos globales. StatsBomb usa una transformación por marcas del campo;
no debe interpretarse su cuadrícula como metros ni como simple escalado uniforme.

El informe incluye puntos en el sistema destino, cuadrícula StatsBomb, distancias
métricas entre puntos consecutivos, errores numéricos de ida/vuelta, versiones y
procedencia. Los metadatos del JSON son declaraciones no verificadas externamente.
Se conservan ruta relativa de entrada, SHA256 de los bytes efectivamente pasados
al subproceso, tamaño, SHA256 del worker y fecha UTC. La versión y el hash del
worker identifican el software declarado, sin certificar cada archivo instalado
de sus dependencias. Los ZIP originales y recibos de preparación permanecen locales.

El agente recibe resumen, hasta diez puntos, ruta y SHA256 del informe completo.
Se permiten hasta 1000 puntos y 500000 bytes. Se rechazan números no finitos,
campos faltantes, valores fuera del terreno y orientaciones incompatibles. No se
recortan silenciosamente puntos externos. La salida debe ser un JSON nuevo en
assets/, artifacts/ o workspaces/ del mismo proyecto, incluyendo resolución de
enlaces simbólicos. La publicación atómica sin sobrescritura requiere enlaces de
archivo, como los de NTFS. Errores `SPORTS_*` distinguen estas condiciones.

## Validación y límites

Las pruebas usan entradas sintéticas offline con las bibliotecas reales,
incluyendo esquinas, centro, unidades, orientación, dimensiones asimétricas,
ida/vuelta, errores y puente del agente. Se omiten en equipos sin el entorno
opcional instalado. El resto de la suite no requiere estas dependencias.
No se analizan partidos reales ni se crean figuras. No se validan aquí lectores
de eventos/tracking, modelos tácticos, estadísticas deportivas o render.

Fuentes oficiales: [Kloppy Dimension](https://kloppy.pysport.org/reference/domain/models/pitch/dimension/),
[sistemas de coordenadas](https://kloppy.pysport.org/user-guide/concepts/coordinates/),
[MPLSoccer Standardizer](https://mplsoccer.readthedocs.io/en/latest/gallery/pitch_plots/plot_standardize.html).
