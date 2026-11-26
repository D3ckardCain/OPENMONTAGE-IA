# Cola autónoma: avances y límites comprobados

26-11-2026 UTC. [Evidencia breve](COLA_AUTONOMA_20261126_RESULTADOS.json).

**Actualización tras reinicio manual:** [activación real4750](ACTIVACION_544C57F_ES.md)
y [resultados](ACTIVACION_544C57F_RESULTADOS.json). PID138604, identidad esperada
residente/disco, sin reinicio requerido. Silencios, componentes, recuperación
Qwen y referencias comprobados en copias. HyperFrames genérico sigue sin perfil
heredado en el servidor; reproducción del render existente sí comprobada.
El rechazo de reinicio y PID130700 inferiores son evidencia histórica anterior,
superada por el reinicio manual del usuario, no por una evasión de política.
HTTP10054 sigue observado en cliente Python; write recuperado sin reenviarlo.

## Activación #130/#132: estado previo al reinicio manual

En la entrega anterior4750 respondía con PID130700 e identidad antigua/reinicio requerido.
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

## Resultado conjunto posterior

56 pruebas Python nuevas, ejecutadas por incrementos focalizados:9 evidencia
vídeo,14 Qwen,9 referencias,13 componentes y9 GLB, más2gates de planificación. No se repiten las21 de
silencios, suites aprobadas, ASR, voces españolas ni piloto Blender. CI remota
se registra separadamente tras publicar, sin atribuirle comprobación local.

Chrome/API reales en **4764 aislado**, residente=disco
`576872d95e31a36a2dd77d04984cdea3c797d13cc217086074d1b5d8dec72f63`,
30archivos: selección/transformación manual de capa, undo/redo/save/reopen,
exportación y reproducción sin errores JS. Instancias QA propias previas
identificadas/cerradas, no PID130700/4750. No acredita activación del usuario.

#130: propuesta/revisión/aplicación y sincronización pasaron sobre copia. Muestra
portuguesa final22,36s,559frames,540×960,H264/AAC48k,19subtítulos quemados y116
palabras guardadas; corte9frames257–266. Chrome reprodujo atravesando10,28s y
decodificación completa sin errores. Correlación de ventanas audio0,861/0,976,
desfase aproximado5,75/6,25ms en copia con pista técnica duplicada/limiter; no
medición universal ni escucha. Protección numérica ASR no certifica ausencia
fonética de palabras cortadas. Intervalo acústico sintético; español y silencio
real medido pendientes. La copia QA tenía títulos técnicos sin estilo y texto
mal codificado: corregidos por API desde UTF-8 original antes de acreditar la
misma muestra final. No atribuir defectos de fixture al original. Las8EDL
originales coinciden byte a byte con sus snapshots iniciales.

#132: render previo reutilizado sin repetirlo; perfil de proceso hijo no se
hereda al Studio normal automáticamente. Activación4750 y escucha pendientes.

#149: [modelos completos y runtime aislado](QWEN3_TTS_LOCAL_ES.md). FDM terminó
durante la cola; pesos nuevos verificados una vez, tokenizer compartido,
auxiliares identificados y nombres canónicos recuperados. Importación/pip check
pasan. CPU FP32 rechazada antes de cargar por RAM libre insuficiente; CUDA/8GB
no acreditados. Plan Audio/agente y persistencia sí pasan. No síntesis española,
escucha o cancelación real atribuidas a la preparación.

#145: [contrato inicial compartido](PLAN_REFERENCIAS_LOCAL_ES.md) reutiliza
scene_plan/marcadores, hashes/PTS/cobertura parcial y revisión solo de escenas
modificadas. API real reutilizó recibo #122 sin nueva extracción. No director
automático integral ni nuevo diseñador visual de storyboard.

#146/#147: [componentes y collage propios](COMPONENTES_EDITABLES_LOCALES_ES.md),
una escena QA4s/96frames con vídeo Blender y WAV Piper existentes; tiempos
separados evitan competencia. Edición/undo/persistencia/exportación/reproducción
reales;4ratios con pruebas raster estáticas. Escucha y variantes AV completas
pendientes. No integración total de candidatos ni segmentación automática.

#117/#143: [inspector GLB acotado](INSPECCION_GLB_LOCAL_ES.md), sin Blender ni
payload de malla. Importación visual pendiente de GLB propio;4.5 predeterminado,
sin repetir piloto5.3. #144/#148 mantienen decisiones de no instalar por inercia:
MoviePy sin ventaja inmediata, Chimera requiere preparación Windows considerable.

#113: criterio antes oculto comprobado en escenario explícito permitido de
acciones visibles/contraste/foco/teclado, combinado con activación real previa.
Puede cerrarse ese alcance; no WCAG global. #112 sigue sin recibo Piper elegible:
un render FFmpeg o plan Qwen no es recibo recuperable de síntesis.

Prioridad restante: activación única4750; recursos/medición Qwen; recibo real
#112; escucha y muestra española#107/#130; GLB propio#143; variantes AV de los
componentes y revisión visual ampliada#145. No cerrar por CI, instalación,
metadatos o simulaciones. Ver resultados estructurados para separar alcances.

[Corrección CI basada en logs y comprobaciones focalizadas](CI_COLA_20261126_ES.md).

## Continuación Qwen149 y CI

Los tres workflows de `16842e6` terminaron correctamente: CI45767931949,
contratos PR45767931925 y contratos push45767925629. CI principal:
3814passed/44skipped/3xfailed/40subtests. Esto acredita ese commit, no los
cambios posteriores ni la activación4750.

Se resolvió el bloqueo CPU de Qwen preparando CUDA12.4 en el mismo entorno
aislado. [Manual y evidencia Qwen](QWEN3_TTS_LOCAL_ES.md): muestras españolas
reales VoiceDesign1,92s y Base2,80s con referencia sintética propia; registro,
recuperación y persistencia desde panel real. Cancelación real tras3pasadas,
worker cerrado y GPU liberada, sin repetir síntesis al recuperar.
18casos nuevos focalizados;74casos Python nuevos acumulados en la cola.
No se repitieron ASR/Piper/pilotos/renders aprobados ni hashes de pesos grandes.

Pendientes vigentes: activación4750 rechazada por política; escucha humana;
español audiovisual107/130; recibo Piper112 no elegible (Qwen no lo sustituye);
GLB propio143 y validación AV ampliada de formatos/componentes. PR2 borrador.

Código funcional `4242eca`: CI45773151291 aprobada con3832passed/44skipped/
3xfailed/40subtests. Push45773142874: contratos/instalación Windows/Linux y
43regresiones de navegador aprobados. [Detalle](CI_COLA_20261126_ES.md).
Servidor QA4764 detenido tras finalizar trabajos;4750 sigue PID130700/saludOK.
Workflow PR paralelo45773151258 también terminó **success**;43pruebas browser
aprobadas en76,94s. La preparación pendiente a07:17UTC terminó por sí sola,
sin relanzar ni modificar límites/red. CI principal y ambos contratos verdes.
