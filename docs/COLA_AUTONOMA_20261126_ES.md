# Cola autónoma: avances y límites comprobados

26-11-2026 UTC. [Evidencia breve](COLA_AUTONOMA_20261126_RESULTADOS.json).

## Activación #130/#132

4750 responde, PID130700 sigue con identidad antigua/reinicio requerido.
Cola pausada/vacía, agentes/análisis y exportaciones consultados sin actividad;
11proyectos inspeccionados. Artefactos de edición persistidos respaldados en
`.runtime/qa/activation130132-snapshots`, sin modificar originales. No se afirma
haber guardado texto de formularios aún no enviado desde el navegador del usuario.

La política rechazó la orden que detenía solo PID130700 y arrancaba Studio desde
`.venv`: `blocked by policy`. No se intentó otro método para detenerlo.
Activación residente pendiente, no resuelta por CI/pruebas aisladas.

Paso manual cuando no haya trabajos: en la consola original de Studio, Ctrl+C
y esperar la salida; no cerrar otras consolas. Después:

```powershell
Set-Location -LiteralPath C:\OPENMONTAGE-IA
& .\.venv\Scripts\python.exe -B -m backlot serve --port 4750
```

Mantener un solo proceso propietario de4750. Si Ctrl+C no finaliza, no abrir otra
instancia encima ni desactivar la política; conservar ese bloqueo para resolverlo
manualmente. Tras el reinicio comprobar identidad/salud/capacidades, sin volver a
renderizar HyperFrames ni repetir los21casos de aplicación aprobados.

Se añadieron controles reales de propuestas de silencio al panel de candidatos:
JSON de análisis existente, márgenes/mínimo, selección explícita, revisión,
consulta de fuente y aplicación compartida. No inicia ASR/análisis/inferencia.
La vista diferencia fixtures sintéticos y rechaza revisión obsoleta/doble envío.

Panel real con HTTP/backend actuales comprobado en instancia **aislada4761** y
copia portuguesa: propuesta7candidatos; aplicación9frames,116palabras guardadas,
undo/redo/save/reopen exactos. Esto prueba los nuevos controles, no activación4750.
El render existente de HyperFrames se conserva; no se repitió. La escucha humana
no se afirma y no detiene las tareas independientes.

## Descargas Qwen #149

[Inventario, revisiones, hashes y acciones](QWEN149_PREPARACION_20261126.json).
Los pesos nuevos siguen como `.fdmdownload`, con registros FDM no finalizados.
Tamaño preasignado completo no equivale a descarga completa. No se hashearon ni
renombraron/promovieron esos temporales ni se modificó FDM. Algunas rutas son
todavía directorios con nombre de archivo; los destinos FDM no finalizados se
dejaron intactos. `Base/model.safetensors` contiene un auxiliar, no se borró.
FDM incluye destinos/URLs de variantes mezcladas: corregirlos en FDM antes de
finalizar; nunca sustituir config Base por config VoiceDesign por tener mismo nombre.

Tokenizer oficial idéntico en ambas revisiones,682293092bytes/SHA256836b7b…1258.
Se verificó una vez el existente en D:0.6B Base, se copió a la subcarpeta correcta
de Base en C: y se verificó una vez la transferencia. VoiceDesign usa un enlace
duro al mismo contenido en C:, archivo regular transparente al acceso local,
sin otra descarga ni duplicar los datos. Configs permanecen por modelo. Caché
registra identidad/metadatos posteriores al enlace; no volver a leer682MB por rutina.

El peso antiguo bajo D:VoiceDesign tiene SHA25638b1d597…2f5137: coincide exactamente
con **CustomVoice oficial** revisión0c0e305…, no con VoiceDesign391e8db…. Queda
identificado como variante distinta/mal ubicada, conservado y excluido de carga.
No se declara corrupción ni se ha vuelto a leer CustomVoice para compararlo.
No se retoma #82 ni su Qwen de8GB.

Auxiliares existentes se compararon con Git blobs oficiales fijados; copiados
sin sobrescribir o aplazados si tienen destino FDM no finalizado. Única descarga:
README Base oficial de57817bytes. `speech_tokenizer/config.json` y
`configuration.json` se tratan como archivos diferentes.

## #112/#113 y decisiones independientes

No hay registros de solicitud en `projects/*/artifacts/piper_previews/*.json`:
falta un recibo elegible de #112. WAVs sueltos anteriores no se convierten en
solicitudes nuevas; no fabricar recibos ni repetir Piper para cerrar el criterio.

#113: escenario explícito de acciones de agente visibles con HTML/CSS reales,
1280×900, sin JS de producción y red abortada. Iniciar/reanudar, detener y aprobar
etapa: contraste12.8804:1, foco sólido2px, activación Enter/Espacio con contadores
locales. No agente real iniciado; no repetir formularios/tamaños aprobados.

#144: MoviePy1.0.3 ya está en el entorno MuseTalk; no es la API2.2 evaluada.
Capas/títulos/mezcla/cortes actuales ya usan FFmpeg. Sin mejora inmediata
demostrada, no instalar/actualizar MoviePy ni duplicar FFmpeg. Reconsiderar solo
ante una operación de máscara/función por fotograma que el grafo actual no resuelva,
con presupuesto de CPU/RAM y benchmark acotado antes de adoptar.

#148: no rustc/cargo/Bun en PATH; la revisión fijada no publica build Windows.
CLI WAV es la vía futura preferible al navegador/DAW, pero requeriría toolchain
MSVC/Rust y prueba fonética española no acreditada. No compilar/instalar por inercia.

#143: no GLB propio localizado en projects/assets/local_library revisados; no
afirmar ausencia global. Se conserva el plan de inspección de escala/ejes/PBR y
transformaciones sin World Labs/FAL. No generar/exportar un objeto solo para
fabricar esa prueba ni repetir el piloto Blender5.3;4.5 permanece predeterminado.

PR#2 borrador. Costo$0. ComfyUI, entornos y configuraciones existentes conservados.
