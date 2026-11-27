# EvaluaciÃ³n de Timeline Studio / AI Video Editor #182

Fecha: 2026-11-27. Proyecto fijado: [`MartinDelophy/ai-video-editor@087e2f78dbc0ef2c1843daa82236367cb274b9ff`](https://github.com/MartinDelophy/ai-video-editor/tree/087e2f78dbc0ef2c1843daa82236367cb274b9ff). El nombre del issue no determina otro producto: esta evaluaciÃ³n trata solamente ese repositorio.

## DecisiÃ³n

No instalarlo ni reemplazar OPENMONTAGE. Es una aplicaciÃ³n/editor alternativo de gran alcance. Algunas interacciones documentadas son referencias concretas para #174 y su WebMCP para coordinaciÃ³n manual/agente, pero OPENMONTAGE ya tiene un editor compartido y un motor de comandos/historial; duplicar su runtime, storage y catÃ¡logos aumentarÃ­a el mantenimiento y duplicarÃ­a modelos.

Reutilizar los patrones pequeÃ±os de selecciÃ³n contextual, previews y snapping, controles de curva, export con progreso/cancelaciÃ³n y confirmaciÃ³n/undo en el mismo editor. Para SFX, reutilizar el requisito de bÃºsqueda/preview/inserciÃ³n de #177, condicionado a verificar licencia por archivo. No asumir que todas las capacidades anunciadas estÃ¡n activas en OPENMONTAGE ni que la demo del upstream acredita compatibilidad local.

## VersiÃ³n, requisitos y costo

- README del commit fijado anuncia actualizaciones hasta 2026-11-13 y llama al proyecto â€œlocal-first browser AI video editorâ€; `package.json` es v1.0.0 `private`, Vite/React, con scripts locales `host`, `dev`, `agent`, `mcp`, `skill:doctor/setup` y dependencias web de codec/modelos.
- El build del repositorio usa numerosos paquetes JS/WASM (FFmpeg, Mediabunny/LibAV, Transformers/ONNX Runtime, MediaPipe, Kokoro, Whisper-related features, etc.). No es una sola dependencia pequeÃ±a. El README dice Node/npm para desarrollar; no presenta una instalaciÃ³n Windows empaquetada verificada aquÃ­. No instalar otro entorno ni copiar estos paquetes a `.venv`/ComfyUI.
- La ediciÃ³n del navegador usa recursos locales y anuncia export determinista/offline, incluyendo 4K con carga bajo demanda. Aun asÃ­, cada modelo/asset externo tiene que estar disponible localmente; la documentaciÃ³n del proyecto advierte que el cache/descargador puede traer recursos. No iniciar setup/doctor ni inferir que primera apertura funciona sin red.
- La ediciÃ³n **Anna** es una ediciÃ³n distinta: README dice que guarda proyectos y medios en nube, planifica con metadata del clip sin analizar sus frames/audio y permite cortes simples 1Ã—; no equivale al agente local ni al editor offline.
- La integraciÃ³n de agente publicada vÃ­a WebMCP es una mejora progresiva, con especificaciÃ³n declarada como borrador de grupo comunitario; solo estÃ¡ disponible en navegadores/hosts compatibles. El repo documenta transacciones, estado, undo y export/cancel real en su editor; eso no acredita que el host de OPENMONTAGE pueda descubrirlo ni que sea compatible con nuestra EDL.

## Funciones confirmadas en README y cÃ³digo

| FunciÃ³n de referencia | Evidencia upstream revisada | ReutilizaciÃ³n posible / lÃ­mite |
|---|---|---|
| Scrub y miniaturas | Changelog del README: miniaturas de importaciÃ³n en lotes y menos trabajo durante el arrastre del playhead; `TimelineThumbnails.jsx`. | #174 ya prioriza preview de timeline; medir actualizaciÃ³n por arrastre y nÃºmero de decodes antes de copiar una tÃ©cnica. No trasladar arquitectura React/WebCodecs completa. |
| Reemplazo de clip | README: seleccionar rango de otra fuente o mover rango conservando duraciÃ³n/velocidad; contextual properties panel. | Ãštil como control de #92/#174 si mantiene explÃ­citos source-in/out y velocidad. Prueba en copia contra contrato actual; no insertar un estado paralelo. |
| Snap de grupos | README afirma que la guÃ­a ajusta el grupo seleccionado sin alterar el espaciado entre clips. | Criterio de aceptaciÃ³n para ediciÃ³n multiselecciÃ³n: offsets relativos estables, snapping visible, undo/reopen. No duplicar la lÃ³gica ya completada de ripple. |
| Keyframes/ganancia/fades | `VisualClipKeyframes.jsx`, `TimelineGain.jsx`, `TimelineAudioFades.jsx` implementan marcadores arrastrables, control de ganancia y envolvente editable. | Referencia de interacciÃ³n visual para #174; ya se entregaron curvas/automatizaciÃ³n en ese issue. No inferir equivalencia de render/audio sin comparar la implementaciÃ³n local. |
| Color y catÃ¡logo SFX | README anuncia RGB parade, ruedas de color, beats editables y biblioteca de 120 SFX. `MODEL_LICENSES.md` advierte que medios, modelos y fuentes no heredan MIT. | Las 120 muestras no se reutilizan hasta catalogar origen/licencia/hash; eso ya corresponde a #177 y no a 120 descargas nuevas. RGB parade solo si falta un scope integrado local, no un widget decorativo. |
| Agente/WebMCP | `docs/webmcp.md` describe herramientas del proyecto abierto: inspecciÃ³n de timeline/assets, transacciones editables, undo, guardado `.timeline`, export con progreso y cancelaciÃ³n. | PatrÃ³n para hacer inspeccionables las mismas acciones. WebMCP es experimental y no sustituye el puente/API validado de OPENMONTAGE ni debe abrir otro editor/proyecto. |

## Licencias y uso responsable

- `LICENSE` raÃ­z es MIT para el cÃ³digo original; `MODEL_LICENSES.md` aclara que pesos, datasets, medios, fuentes y dependencias no reciben automÃ¡ticamente MIT.
- Face swap MobileFaceSwap/ArcFace/SCRFD se marca investigaciÃ³n y con permisos comerciales no concedidos/no confirmados. No ofrecerlo como candidato comercial hasta verificar derechos de cada peso.
- Kokoro/Piper/VITS, Whisper, JoyVASA/LivePortrait, Stable Audio y demÃ¡s modelos tienen tÃ©rminos propios por checkpoint. No descargar una copia paralela ni decir que un nombre de familia acredita una licencia.
- Clips SFX de ejemplo/catÃ¡logo tambiÃ©n tienen licencia por recurso. El contador â€œ120â€ no acredita redistribuciÃ³n; contrastar #177 antes de integrar cualquier sonido.
- La polÃ­tica del proyecto requiere autorizaciÃ³n de likeness y evita suplantaciÃ³n. No se usaron imÃ¡genes reales ni recursos del demo.

## Brechas para anotar en issues existentes

1. **#174:** mantener en una sola lÃ­nea de comandos la curva/fades, selecciÃ³n contextual, snap de grupos y export que consume la misma automatizaciÃ³n que preview. Su prueba acepta audio/video/subs sincronizados, persistencia y undo; no repetir renders ya aprobados sin cambio relevante.
2. **#177:** listado de sonidos con bÃºsqueda, preescucha, atributos y arrastre es un patrÃ³n Ãºtil; importar solo archivos autorizados ya catalogados, sin asumir licencia del kit.
3. **#92:** controles visibles y contextual inspector deben seguir siendo manualmente editables con el agente detenido; no simular preview ni exponer funciones sin backend.
4. **Puente:** preferir los comandos/versiones/recibos existentes de OPENMONTAGE. El WebMCP externo depende de la API del navegador; no se adopta por registro visible ni se usa como nuevo endpoint de escritura.

## Criterios de aceptaciÃ³n si se adapta una interacciÃ³n

- Sobre copia del mismo proyecto OPENMONTAGE: operaciÃ³n manual y agente invocan el mismo comando/revisiÃ³n; un cambio produce una sola transacciÃ³n; undo/redo y guardar/reabrir mantienen resultados.
- Para reemplazar/snap: medir source range, duraciÃ³n/velocidad y offsets de clip; no modificar silenciosamente espacios ni sincro de audio, capas, tÃ­tulos o cues.
- Para controles de ganancia/fade/efecto: el export decodificado debe corresponder a preview y valores guardados; bypass vuelve al material original.
- Para SFX: recibo del archivo con hash, origen, creador, tÃ©rminos, atribuciÃ³n, duraciÃ³n, canales y licencia comercial; previews no deben llamar servicios externos.
- CancelaciÃ³n y recuperaciÃ³n se validan en herramientas locales de OPENMONTAGE, no se extrapolan del demo del repositorio externo.

## VerificaciÃ³n y lÃ­mites

- Revisados README/changelog, `package.json`, Ã¡rbol de mÃ³dulos de timeline, keyframes, gain/fades, scopes, WebMCP y `MODEL_LICENSES.md` en la revisiÃ³n fijada.
- Contraste de solapamiento con #174, #177 y la base compartida ya presente. La salida no modifica backlog porque las tareas ya estÃ¡n abiertas en esos issues.
- No se instalaron dependencias, no se hizo doctor/setup, no se ejecutÃ³ la app ni WebMCP, no se inspeccionaron modelos/medios locales y no hubo export, inferencia ni prueba Windows/offline.
- Afirmaciones de marketing/README sobre 4K, offline o capacidades del agente no se tratan como validaciones locales. La licencia comercial de cada artefacto sigue pendiente de revisiÃ³n individual antes de redistribuir.

## AceptaciÃ³n de la evaluaciÃ³n

- [x] Repositorio y SHA inequÃ­vocos y fijados.
- [x] MÃ³dulos/capacidades Ãºtiles contrastados con la base y los issues abiertos.
- [x] Licencias y recursos de pago/modelos separados.
- [x] Criterios verificables sin instalar ni generar contenido.
- [ ] Compatibilidad audiovisual/Windows en esta mÃ¡quina: no ejecutada; no requerida para esta evaluaciÃ³n documental.

