# Balance estéreo por clip (#174)

Entrega pequeña sobre la EDL compartida, sin motores ni paquetes nuevos. La capacidad `audio_balance` permite atenuar un canal de cada clip de vídeo con audio o cada clip de audio independiente. Los controles aparecen solo si el backend declara esa capacidad y la fuente contiene audio. No sustituye un mezclador de buses, panorama espacial, EQ, compresor, ducking ni automatización; esos criterios de #174 continúan pendientes.

En el inspector, selecciona el clip y abre **Balance estéreo del clip**. El deslizador acepta −1 (izquierda), 0 (centro), +1 (derecha). Se puede usar con teclado; muestra valor y dirección. **Guardar balance** realiza una operación revisionada; **Centrar** guarda 0. No cambia solo el reproductor del navegador. Para escuchar el montaje se debe preparar su vista previa: reproducir la fuente original no procesa efectos. Un render anterior queda invalidado si cambia el balance.

## Semántica y agente

```json
{"operation":"audio_balance","revision":17,"track":"audio","id":"ID_CLIP","balance":-0.4}
```

La misma operación está disponible en `studio_project_edit` → `action:command`. `track` es `audio` o `video` (predeterminado). El valor se guarda como `stereo_balance` en el clip; 0 elimina el ajuste y recupera la identidad audiovisual original. Deshacer/rehacer, guardar/reabrir, copiar/dividir y ripple conservan el contrato del proyecto existente. Se rechazan fuentes sin audio, huecos, clips bloqueados, pistas desconocidas, booleanos, valores no numéricos/no finitos o fuera de −1…1.

Después de la conversión estéreo ya existente, FFmpeg aplica `pan` sin mezclar canales:

- `L_salida = L_entrada × (1 − max(0, balance))`.
- `R_salida = R_entrada × (1 + min(0, balance))`.

El centro no añade filtro; los extremos silencian solo el lado opuesto. No amplifica ni traslada el contenido de un canal al otro. El balance se aplica antes de ganancia/fades y mezcla. El mismo grafo se utiliza en preview y exportación. La fuente mono usa la conversión estéreo ya existente. No es una ley de panorama de potencia constante ni un posicionador espacial.

El formulario bloquea envíos simultáneos y conserva el borrador ante error. Ante HTTP10054, recuperar estado y revisión antes de repetir; no se reenvía automáticamente. La nueva propagación de errores se limita al balance; los demás formularios conservan su manejo previo.

## Evidencia focalizada

- Cinco pruebas nuevas aprobadas en `tests/backlot/test_studio_audio_balance.py`: persistencia/identidad/undo/redo, errores y locks sin mutación, rollback batch y división/ripple, mismo filtro en gráficos de preview/export y comando de agente mediante API TestClient. Fuentes ficticias con probe simulado: estas pruebas no acreditan reproducción audiovisual.
- FFmpeg preparado procesó cuatro señales estéreo de **40 ms** (centro, extremos y +0,5), 1.920 muestras por canal. Error máximo medido frente a las ganancias esperadas: **0**. Es una prueba nueva de procesamiento PCM, sin voz, inferencias ni render de vídeo. Script reproducible opt-in: `python -m scripts.validate_studio_audio_balance`; no hace falta repetirlo tras esta aprobación.
- Chrome operó el control real en escenario explícito de EDL y transporte simulados: teclado, guardar/centrar, lock, exclusión por capability, bloqueo de doble envío y borrador conservado tras error HTTP10054 simulado. No hubo errores de página. No equivale a la API ni al panel del servidor principal.
- `.venv` y Python global no contienen pytest; el entorno QA existente contiene pytest pero no FastAPI. Las primeras invocaciones no ejecutaron pruebas por esas dependencias. Se reutilizó el patrón de QA existente: Python de Studio con paquetes de pytest de QA en su `sys.path` solo durante el proceso, sin instalaciones ni modificaciones de entornos. Entonces pasaron las cinco pruebas.

[Evidencia estructurada](EDITOR_BALANCE_ESTEREO_EVIDENCIA_20261126.json). Sin suite completa, CI, síntesis, hashes de modelos ni renders aprobados repetidos. Activación del servidor principal y escucha humana pendientes; agrupar con keyframes y HyperFrames. El rechazo anterior al reinicio no se elude. PR #2 permanece en borrador y #174 abierto.
