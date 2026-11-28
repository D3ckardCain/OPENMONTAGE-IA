# Corrección ripple + capa: sincronía global y persistencia (#92)

Reproducción de [7146510875](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/92#issuecomment-7146510875).
Se revisaron los lectores/validadores existentes antes de modificar el código.
Primero pasaron15 regresiones previas de operaciones/capas/efectos. La nueva
regresión por la API real reprodujo un400 en vez del200 esperado.

## Caso copiado y resultado

`scripts/validate_studio_ripple_copy.py` crea una copia aislada a partir del
proyecto existente `edit-827337e03f38`, conserva fuentes/procedencia y copia sus
medios existentes. Solo adapta la copia al caso de tres cortes de2s. No altera
el proyecto original, no genera medios ni inicia FFmpeg/inferencias.

| Elemento | Antes, montaje6s | Tras borrar el segundo corte[2,4), montaje4s |
|---|---|---|
| Capa, duración1s | inicio4 | inicio2, mismo intervalo fuente |
| Audio, duración1s | inicio4 | inicio2, mismo intervalo fuente |
| Título |4–5|2–3, mismo texto/estilo |
| Cue |4–5|2–3, mismo texto |
| Marcador |4.5|2.5 |

**Antes:** API400 por capa fuera de duración; rechazo atómico, sin corrupción
observada. **Después:** API200 y todos los elementos anteriores transformados
con el mismo mapa temporal. Usuario borra, agente deshace, usuario rehace y agente
guarda; una nueva aplicación TestClient reabre el estado persistido e idéntico.
Fuentes, medios originales, configuración de aplicaciones/settings y proyecto
original conservan hashes antes/después. Evidencia en
`EVIDENCIA_RIPPLE_CAPAS_20261124.json`.

## Semántica de la corrección

Se reutilizan `_segments` y `_ripple_time` para todas las pistas afectadas por
`ripple_delete` de vídeo. Audio y capas comparten ahora el mismo lector de
segmentos fuente: convierte entrada/salida con velocidad, conserva procedencia
y orden de composición. Los fades de audio solo se conservan en las partes que
contienen sus intervalos originales. Los títulos y cues comparten el recorte de
intervalos; conservan texto/estilo, sin inferir palabras ni hacer ASR.

Elementos íntegros posteriores se desplazan; los que cruzan el tiempo eliminado
se recortan/dividen; los totalmente eliminados desaparecen. Se conserva el ID en
la primera parte retenida y se asignan IDs nuevos a las siguientes. Undo/redo
restaura exactamente las decisiones y los IDs guardados, no ejecuta otra vez el
split. Marcadores usan intervalos de eliminación semiabiertos[entrada,salida).

Bloqueos que impedirían la transformación producen409 y rollback de toda la
operación. También se protege el fade saliente de un vídeo bloqueado anterior:
no puede cambiar indirectamente al borrar su vecino. Una transición de entrada
que quedara inválidamente en el primer clip mantiene el rechazo atómico400;
debe resolverse explícitamente. Las transiciones válidas de entrada se conservan.

Si la división excede4 entradas de capas o20 títulos, o deja una parte de capa
menor de un fotograma, se rechaza todo con un error claro. No se ocultan pérdidas
descartando partes. Los mínimos de audio/texto siguen la resolución previa de1ms.
No se amplían límites de composición ni se añaden controles de bloqueo nuevos.

El alcance global es la eliminación de intervalos de vídeo. Quitar audio
seleccionado sigue conservando las posiciones de las otras pistas; la UI ya
deshabilita el cierre global cuando la selección es de audio. Borrar con hueco
conserva tiempos. No se cambia la semántica de trim/move/remove individuales.

## Pruebas y límites de comprobación

19 nuevos casos focalizados por API: caso documentado, velocidades0.5/1/2,
cruce/split, eliminaciones no contiguas, elementos totalmente eliminados,
límites exactos, orden de capas, bloqueos, transiciones, límites y rollback.
Verifican fuente, estilos, fades, IDs, revisiones, undo/redo y reapertura.
La suite ampliada inicial terminó126passed/1skipped; después se añadieron y
aprobaron dos casos de borde/orden dentro de esos19 nuevos casos.

Reproducción opt-in, en una raíz nueva dentro de `.runtime/qa`:

```powershell
.venv\Scripts\python.exe -B -m scripts.validate_studio_ripple_copy --source-project edit-827337e03f38 --workspace .runtime/qa/NUEVA-COPIA --phase before
# --phase before debe ejecutarse con código anterior: comprueba el400 original.
# Con el parche, reutilizar esa misma copia para la fase posterior:
.venv\Scripts\python.exe -B -m scripts.validate_studio_ripple_copy --source-project edit-827337e03f38 --workspace .runtime/qa/NUEVA-COPIA --phase after
```

Las pruebas usan rutas reales de FastAPI/TestClient en un proceso y raíz
aislados; los fixtures unitarios usan bytes/probe sintéticos. La copia adicional
contiene medios reales existentes, pero no se renderizó ni reprodujo. Se
comprobó además el grafo de PTS de capa; esto no acredita sincronía percibida,
apariencia del panel ni escucha.

Studio4750 responde salud/capacidades, pero no se reinició ni se inyectó código.
No se declara el parche activado en ese proceso; la validación posterior200
corresponde a la aplicación aislada cargada con el código corregido. PR#2 sigue
en borrador, #92 abierto; sin cambios de ComfyUI/entornos ni costo operativo.
