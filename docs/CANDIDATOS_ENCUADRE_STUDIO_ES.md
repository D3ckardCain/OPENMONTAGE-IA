# Candidatos por palabras y revisión de encuadre — #107

Implementación E03/E04 basada en #103, vinculada a #92/#3 y al backlog único.
No instala AutoClip ni otro ASR/selector/reframe. Reutiliza la selección editorial
de Clip Factory, `transcriber.word_timestamps`, `studio_project_edit`, el EDL y
sus comandos add/trim/transform y el render FFmpeg existentes. No ejecuta modelos.

## Flujo manual

1. Seleccionar un proyecto editable y una fuente de vídeo ya registrada. En
   Biblioteca, abrir **Candidatos por palabras**. Importar un JSON ya producido
   por el ASR existente; segmentos sin tiempos por palabra no son suficientes.
2. Confirmar fuente y cobertura procesada del ASR en segundos de la **fuente**.
   El final puede rellenarse con duration_seconds del JSON: es una declaración,
   no evidencia independiente de cobertura. Para fragmentos, indicar offset de
   tiempos: solo se suma a las palabras, no a rangos de cobertura ya absolutos.
3. Clic en palabra para inicio y Mayús+clic para final, o corregir los campos
   de palabra inicial/final inclusiva desde cero. Escribir un motivo editorial.
   Guardar propuesta, que aún no se inserta en el montaje. Más propuestas pueden
   usar el conjunto guardado sin reimportar ni repetir ASR.
4. Revisar palabras y tiempos, motivo, texto previo/posterior y cobertura. El
   corte se amplía a frase completa por puntuación para conservar, por ejemplo,
   **No recomiendo quitar la protección**, aunque se haya seleccionado desde
   «recomiendo». Las palabras/negaciones no se reescriben ni resumen. Abreviaturas,
   puntuación ASR o antecedentes pueden requerir otra propuesta más amplia: el
   algoritmo léxico no garantiza significado autónomo. Confirmar revisión de
   negaciones/antecedentes/final antes de aceptar; también se puede rechazar.
5. Corregir límites con las palabras del **mismo conjunto**, que devuelve el
   candidato a pendiente. Añadir el aceptado al montaje crea un clip recortado
   por el motor existente, en un commit reversible. Repetir el mismo insert
   falla claramente; duplicación posterior es una decisión explícita del editor.
6. Seleccionar el clip insertado. En Encuadre, pulsar **Revisar encuadre con la
   fuente**. Se carga el vídeo local del clip y un canvas de su encuadre; mover
   foco/zoom, giro/reflejo o elegir encajar con bandas. La vista cambia sin guardar
   hasta **Aplicar encuadre**. Usar undo/redo y guardar/reabrir como siempre.
7. Preparar la vista previa FFmpeg del montaje para revisar también subtítulos,
   títulos, audio y tiempos. Exportar solo después de esa revisión. El canvas
   es previsualización local de transform estático, no un render final validado.

Los paneles usan scroll interno; no cambian la estructura widescreen. Navegadores
sin decoder de la fuente muestran error y remiten a la vista previa existente.
Seek/escala del navegador y redondeo/SAR/rotación pueden diferir de FFmpeg:
**no se promete exactitud de fotograma ni paridad de píxel por el canvas**.
Fuentes y resultados anteriores no se sobrescriben. No hay exportación automática.

## Contrato compartido con el agente

Usar la herramienta existente `studio_project_edit`, `action:capabilities` y
`action:read`; exigir `clip_candidates` y obtener source_id/revisión actuales.
La selección editorial sigue el director Clip Factory: contexto autónomo,
negaciones, cifras y diversidad; no se introduce ranking/viralidad automático.
Enviar `action:command` con revision y uno de estos comandos por la misma API
`/api/studio/editor/{pid}/agent-command` que usa el EDL manual:

```json
{
  "operation": "candidate_import",
  "revision": 1,
  "source_id": "ID_REGISTRADO",
  "transcript": {
    "language": "es",
    "model_size": "IDENTIDAD_ASR_EXISTENTE",
    "word_timestamps": [
      {"word": "No", "start": 1.0, "end": 1.2},
      {"word": "cambiar.", "start": 1.3, "end": 1.8}
    ]
  },
  "processed_ranges": [[0, 2]],
  "time_offset": 0,
  "proposals": [{"first_word": 1, "last_word": 1, "reason": "Advertencia; conservar negación y cierre"}]
}
```

Ejemplo exclusivamente sintético, no salida de un modelo ejecutado. Agente debe
usar el objeto real del ASR, no inventar palabras/tiempos desde este ejemplo.

- `candidate_propose`: set_id, first_word, last_word, reason; reutiliza el ASR.
- `candidate_review`: set_id, id, status pending/accepted/rejected. Aceptar exige
  context_confirmed:true. Corrección opcional first_word/last_word amplía de nuevo
  a frase y devuelve la revisión a pendiente si así se solicita. review_note
  opcional. No aceptar el contexto de forma mecánica por pasar validación.
- `candidate_insert`: set_id, id aceptado; add/trim existentes, una revisión/undo.
- `transform` existente aplica fit, zoom, focus_x/focus_y, rotation/flip. Usuario
  y agente leen el mismo resultado; nunca otra copia privada de selección/EDL.

Conjuntos en `edit_decisions.candidate_sets` conservan JSON original como objeto,
palabras con índices/tiempos, hash canónico del JSON (no SHA del archivo original),
huella de la fuente registrada, lengua/modelo declarados, offset, motivo, estado,
spans solicitados/ampliados y mapa de cobertura ASR/no procesado. Huella de fuente
ASR opcional, si existe debe coincidir; sin ella el enlace es explícito del
operador, no una verificación independiente del origen del ASR. No se rehashea
un vídeo completo ni se vuelve a reconocer audio al crear propuestas.

Cobertura ASR completa declarada **no significa** toda la fuente revisada
editorialmente, contenido sin errores o selección exhaustiva. Tiempos no ordenados,
fuera de fuente/cobertura y frases que cruzan huecos sin procesar se rechazan;
no se rellenan silencios inventando palabras. Tokens de duración cero se conservan
sin fabricar alineación, pero un clip final debe tener duración válida.

Cada clip insertado guarda snapshot de referencia al candidato/ASR/span/texto y
motivo. Corregir o rechazar después una propuesta **no reescribe clips ya
insertados**; editar el clip es otra operación reversible. Undo/redo y reapertura
del EDL conservan la procedencia. Revisión obsoleta/conflictos mantienen rollback.

## Límites de esta entrega

Hasta10 conjuntos/proyecto,5000palabras y50propuestas/conjunto. API conserva límite
600KB de comando; UI450KB por JSON. Para fuentes largas usar fragmentos con offsets
y cobertura explícitos. No se cambia configuración, entorno ni Python de ComfyUI.

El control manual reutiliza transform/FFmpeg, **no ejecuta AutoReframe ni su
detector de caras**. El reencuadre automático existente permanece disponible por
sus herramientas; no se añade otro tracker, identificación de hablante o confianza
ficticia. Trayectorias/keyframes automáticos y zonas seguras de palabra dinámicas
siguen pendientes, no se certifican por este transform estático. Bandas permiten
conservar el plano completo si el recorte excluye personas o texto.

## Pruebas y activación

Pruebas focalizadas con palabras/metadatos sintéticos, API real en TestClient y
herramienta agente existente contra esa API: negación, contexto, repetición de
palabras, cobertura parcial/unión/huecos, offset, rechazos, índices/tiempos
inválidos, revisión obsoleta, inserción/undo/reopen y transform persistente.
Node comprueba formulario real con DOM sintético, draft recuperable tras error,
geometría y handlers de preview/seek/cambio de foco/parada. No cargan pesos ni
validan audio, píxeles de vídeo o ventana real.

Resultado: **15 pruebas pytest aprobadas** (14 del contrato/API/agente y1 wrapper
que ejecuta **6 casos Node** de interfaz/geometría). Sin pruebas antiguas repetidas.
El primer chequeo geométrico detectó una aserción de0 frente a-0; se corrigió
esa distinción irrelevante de signo en el test, sin ocultar un fallo del recorte.
Advertencia pytest-asyncio de scope predeterminado permanece visible, sin omisiones.
Parseo/sintaxis de los módulos modificados y enlaces documentales comprobados.

Activación en4750 y comprobación con medios/escucha son pendientes separados:
no se reinicia el servidor. El aviso de #105 debe impedir usar API antigua como
si tuviera esta entrega. PR#2 permanece borrador y HTTP sigue documentado sin
nuevas capturas o cambios de red. No se repiten suites/CI ya aprobadas.
