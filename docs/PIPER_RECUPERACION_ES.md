# Piper: recuperar solicitudes sin repetir síntesis (#112 / E05)

Carencia observada tras #111: cada POST de preescucha generaba otro UUID/WAV.
Perder la respuesta HTTP y reintentar podía repetir trabajo ya completado.
Se reutilizan `studio.save_json`, `LOCK`, el worker Piper, el lector SHA acotado
y su caché por identidad/metadatos ya existentes, además de las rutas del editor.
No se añade otro scheduler, motor TTS, instalación ni servicio remoto.

## Usuario y agente comparten la solicitud

POST `/api/studio/editor/{pid}/piper/preview` admite `request_id`:32hex minúsculas,
`voice`, `speaker_id`, `text`. Conservar el mismo ID para recuperar ese intento.
GET `/api/studio/editor/{pid}/piper/requests/{request_id}` consulta/reconcilia sin
ejecutar proveedor. Un cliente antiguo sin ID recibe uno nuevo por compatibilidad;
la garantía de reintento requiere que conserve y reenvíe el ID.

El agente reutiliza `PiperTTS`0.3.0: `operation=preview` con project_id,
request_id,text,model (ID de voz),speaker_id llama al mismo contrato. Para
consultar, `operation=status` con project_id/request_id, sin texto y sin síntesis;
la consulta sigue disponible aunque el runtime no lo esté. La operación directa
anterior `synthesize` conserva su salida explícita; no promete idempotencia sin
usar el contrato de preview. No hay motor ni recibos privados del agente.

Ejemplo de forma (no inicia nada por leer este manual):

```json
{"request_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","voice":"en_GB-vctk-medium","speaker_id":54,"text":"Synthetic local test."}
```

En Audio: Crear preescucha guarda el token por proyecto en sessionStorage
(solo el token, no el texto). Tras un error, Recuperar última solicitud consulta
el estado; después de recargar la pestaña puede restaurar voz/hablante/texto y
WAV desde el proyecto compartido. Si el almacenamiento del navegador falla,
se conserva el token en memoria durante esa página; tras cerrarla, recuperar
requiere conocer el ID guardado en el servidor. No se prometen garantías de
persistencia del navegador cuando su almacenamiento está deshabilitado.

Repetir Crear con las mismas entradas usa el mismo ID y el recibo completado,
sin otra síntesis. Cambiar entradas prepara una solicitud distinta; también
existe Nueva solicitud (otra toma), que solo limpia el token y no inicia trabajo.
El botón Crear posterior es la acción explícita que lo inicia. Resultados y
parciales anteriores se conservan; nunca se sobrescriben ni borran originales.
Cambiar voz/hablante/texto limpia el audio mostrado para evitar oír una toma
anterior con una selección distinta. Controles bloqueados mientras se espera
la operación; cambiar de proyecto no incorpora su resultado al proyecto nuevo.

## Evidencia, estados y límites

Estado atómico en `artifacts/piper_previews/{id}.json`; reserva exclusiva `.claim`
impide que dos instancias lancen el mismo ID. Estados: running,completed,failed,
interrupted,invalid. Un único proveedor activo por instancia; no cola nueva.
Entradas y huella incluyen texto/voz/hablante, SHA256 real de recursos contra
catálogo, revisión, ejecutable Python, metadatos instalados y código de worker/
adaptador. Es una huella de ese alcance, no auditoría completa del entorno.
Los modelos se verifican mediante caché existente de identidad+metadatos;
modificaciones invalidan caché. No se descarga ni carga modelo por consultar.

Un resultado completado solo se reutiliza con WAV completo, hash correcto,
recibo íntegro, voz/hablante/hash de texto correctos y recursos/runtime vigentes.
El worker añade `text_sha256` y `wave_sha256`. No se migran/adjudican a un ID
las preescuchas antiguas sin estos datos. Una cabecera WAV válida por sí sola
no basta: se comprueba también la longitud efectiva de sus frames.

Mismo ID con otras entradas devuelve409. Estado cambiado, salida parcial,
recibo corrupto o archivo/recurso distinto nunca se convierte en éxito ni
dispara síntesis automática. Si el worker terminó y dejó recibo verificable pero
el servidor no guardó el estado final, GET recupera completed. Sin esa evidencia
queda interrupted; no se afirma que haya muerto un proceso ajeno/orfandado.
La operación incierta no se relanza con el mismo ID. Una nueva toma explícita
usa un ID nuevo y conserva la anterior para inspección.

Perder HTTP/detener espera del navegador **no** prueba detener inferencia. Esta
entrega no añade cancelación del cálculo ni control de un proceso huérfano.
Se conserva el timeout síncrono existente del proveedor; una cola/cancelación
multimedia completa sigue siendo otra ampliación de E05. `interrupted` no
significa `process_stopped`. No se confunde SHA/decodificación con naturalidad.

## Validación focalizada

26 casos nuevos aprobados: recibo reutilizado, deriva de entradas/runtime/pesos,
salida/recibo corruptos, WAV truncado aun con checksum del parcial, reinicio tras
recibo, reserva sin estado, carrera de dos solicitudes, fallo de proveedor,
tokens/rutas inválidos y API real en TestClient. Proveedor contado/simulado,
ONNX/executable ficticios y WAV PCM sintético diminuto; **no síntesis real**.

`scripts/validate_piper_recovery_ui.cjs`, Chrome/Playwright instalados: backend
sintético pierde la primera respuesta; recuperar, repetir y recargar conservan
una ejecución/recibo aunque haya dos POST. Comprueba limpieza del audio obsoleto
y que Nueva solicitud no inicia proveedor. Sin síntesis de voces españolas,
instalaciones, descarga de pesos ni suites aprobadas repetidas.

Implementación preparada para siguiente activación manual agrupada: no se
reinició el servidor4750 para esta entrega. La activación REAL de #111 se había
comprobado antes de editar: PID125660, resident=disk=e68adc7a05b647f5d49b31b293b2d093a2c024d06ce5ee51b5e7d2c72fecc647,
restart_required=false,109 hablantes y preescucha VCTK2.147846s correcta. Eso
acredita #111, no activación de este contrato nuevo de recuperación. La UI nueva
exige `preview_contract=1` y explica si falta activar el backend.

Configuraciones, originales, .venv y ComfyUI intactos. #111: usuario confirmó
Davefx y Sharvard F/M; valoración natural/robótica aplazada. Sin repetirlos.
PR#2 en borrador. Sin nueva CI completa atribuida a estas pruebas focalizadas.
