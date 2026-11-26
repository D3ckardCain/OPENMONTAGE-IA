# Mezclador de las pistas existentes — #174

Entrega funcional local, sin paquetes ni otra timeline. En Audio, **Mezclador de pistas** ofrece dos grupos: audio de todos los cortes de vídeo y todos los clips de audio añadidos. Cada grupo tiene nivel lineal 0–4, silencio y solo. No son buses arbitrarios ni una pista independiente por cada clip.

Guardar aplica ambos grupos mediante un único comando reversible. Restablecer devuelve nivel 1 y desactiva silencio/solo, sin borrar ajustes de los clips. Los controles se ocultan si el backend carece de `track_mixer`. No cambian el sonido del reproductor de fuente: preparar el montaje para escuchar la mezcla. No hay DSP en directo.

Silencio prevalece sobre solo. Si una pista tiene solo, la otra se silencia; ambas en solo son audibles. El solo de clip existente sigue siendo un filtro adicional de clips: quitarlo para escuchar todos los clips de una pista. Poner en solo una pista vacía puede producir silencio, de forma explícita. Ganancia, silencio, solo y bloqueo de cada clip se conservan; un bloqueo no impide ajustar el mezclador global porque no modifica el clip.

La ganancia de pista se aplica después del procesamiento, ganancia y fades del clip, antes de sus retardos/unión y de la mezcla/normalización/limitador existentes. No hay compresor de bus. La identidad de render incorpora las ganancias efectivas: ajustes neutros recuperan un render compatible previo; la EDL conserva también el estado editorial de solo/silencio. El mismo grafo se utiliza en preview y exportación.

## Agente

Comando normal del puente `studio_project_edit`, acción `command`, con revisión actual y capability `track_mixer`:

```json
{"operation":"track_mixer","revision":12,"mixer":{"video":{"gain":0.6,"muted":false,"solo":false},"audio":{"gain":0.35,"muted":false,"solo":true}}}
```

`mixer:{}` restablece. Cada comando sustituye el mezclador completo; omitir una pista la devuelve a valores por defecto. No reintentar escrituras con respuesta incierta: recuperar estado/revisión antes. No se modifica la procedencia de los medios originales.

## Evidencia y límites

- 13 casos nuevos focalizados aprobados en `tests/backlot/test_studio_track_mixer.py`: historial/reapertura, neutro e identidad efectiva, parámetros inválidos sin mutación, revisión obsoleta, solo/silencio/bloqueo, posición del filtro, mismo grafo preview/export y acceso del agente por API. Fixtures de medios simuladas para estas pruebas; no acreditan escucha audiovisual.
- Navegador real contra servidor aislado 4771 y copia del proyecto de 4 s existente: niveles de ambas pistas, solo, silencio, restablecer, deshacer/rehacer y recarga/reapertura persistentes. Cero errores JavaScript. Sin render ni reproducción repetida. [Informe](EDITOR_MEZCLADOR_EVIDENCIA_20261126.json).
- `.venv` no incluía pytest; se reutilizaron los paquetes QA existentes mediante el runner aislado, sin instalar ni modificar entornos. No se repitieron suites previas ni CI.
- Pendientes: activación y controles en 4750 tras confirmación del reinicio manual; comprobación audiovisual específica del mezclador. La comparación MP4 EQ aprobada sigue siendo evidencia de EQ/compresor, no de estos nuevos controles. La única escucha humana preparada sigue siendo `projects/qa174-eq-ab-review/escucha-ab.html`; no se añadió otra tarea de escucha.
- Continúan pendientes automatización de volumen, ducking, medidores actuales, buses arbitrarios, estilos de subtítulos por cuenta y las demás brechas de #174. No se declara paridad Fairlight ni se cierra el issue. PR #2 en borrador.

Activación agrupada: además de las capacidades ya documentadas, exigir `track_mixer` e identidad residente igual al disco actual; no utilizar el fingerprint de la entrega EQ anterior como identidad de esta ampliación. No reiniciar hasta la confirmación indicada por el usuario.

Actualización: [salida codificada y sincronización validadas](EDITOR_MEZCLADOR_EXPORT_ES.md). [Ducking local](EDITOR_DUCKING_ES.md) entregado aparte; las menciones anteriores a ambas comprobaciones como pendientes son históricas. La activación4750 y escucha humana siguen pendientes.
