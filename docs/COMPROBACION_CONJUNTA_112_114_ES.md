# Comprobación conjunta breve tras una activación manual

Preparada, **no ejecutada**. Revisados los cuerpos y pendientes actuales de
#112,#113,#114. Las pruebas de contrato/fixtures ya aprobaron; no se vuelven a
ejecutar sus26casos,#11226casos,#113cuatro viewports ni las síntesis de #111.
Objetivo: comprobar **la activación real** en4750, no repetir toda la regresión.

## Una sola activación

Cuando se decida activar el lote completo, comprobar primero que no haya trabajos
activos e identificar el proceso dueño de4750. Detener únicamente su consola de
Studio con Ctrl+C y esperar salida; no detener ComfyUI/Ollama ni otros procesos.
Después, una sola vez:

```powershell
Set-Location -LiteralPath C:\OPENMONTAGE-IA
& .\.venv\Scripts\python.exe -B -m backlot serve --port 4750
```

Recargar el panel. Registrar fecha/PID, salud y `/api/studio/identity`: residente
y disco disponibles/coherentes, restart_required=false, identidad de la UI
coincidente y capacidades de esa misma instancia. Si falla, **detener el smoke**
y registrar discrepancia; no encadenar reinicios ni tomar CI como activación.

## Smoke de aproximadamente cinco minutos

| Paso | Comprobación mínima | Evidencia/criterio |
|---|---|---|
| #112 | En un proyecto QA, consultar un request_id ya completado de **este contrato** y pulsar Recuperar última solicitud; recargar una vez y recuperar otra vez | Mismo request_id/WAV/hash, estado completed, ningún POST de síntesis ni WAV adicional; voz/hablante/texto corresponden al recibo. GET y recuperación UI, no otra toma |
| #113 | En Producción, inspeccionar un botón primario habilitado y recorrer por teclado un campo→submit→iniciar/detener/aprobar sin activarlos | Colores computados blanco/#238636, ratio>=4.5, foco perceptible y orden/foco conservados. Un viewport real, no repetir matriz320–1280 ni acciones de agentes |
| #114 | En una pestaña/contexto QA aislado, interceptar y devolver400 a **un** intento de formulario; provocar dos submit durante el mismo envío | Un POST interceptado, cero POST reales; texto/rutas/Unicode intactos, mensaje legible, aria-busy retirado y botón/foco recuperados. No guardar settings ni crear proyectos reales |

Para #114, bloquear en el contexto QA **todas** las mutaciones antes de abrir la
página. Únicamente el POST elegido recibe la respuesta sintética; cualquier otro
POST se bloquea y se registra. No desactivar controles ni introducir fallos en
el servidor para simular un error. Las comprobaciones de otras respuestas
400/403/500/timeout y de doble envío ya tienen evidencia offline: no repetirlas.

## Recurso necesario para recuperar sin sintetizar

#112 exige recibo nuevo con text_sha256/wave_sha256 y huella de sus recursos.
Las preescuchas aprobadas de #111 **anteriores al contrato** no se convierten en
solicitudes #112 ni se completan sus metadatos por suposición. Sus recibos no
demuestran por sí solos el hash de texto requerido por el contrato nuevo.

Si después del reinicio no hay request_id completado elegible, comprobar solo
presencia de contrato/API/controles y registrar **recuperación end-to-end pendiente
por falta de recibo elegible**. Usar para completar ese paso la siguiente
preescucha normal explícitamente autorizada, conservando su request_id; no lanzar
otra síntesis solo para repetir #111 ni fabricar un recibo/proveedor simulado
como si fuera una voz real. Ese pendiente no impide registrar los otros pasos.

## Registro y cierre

En cada issue registrar resultado **observado**, no solo casilla marcada:
instancia/revisión, paso, esperado/observado, recurso QA, límites y enlace al
informe común. No cerrar #112 por API presente si no se recuperó un completado
acreditado; no cerrar #113/#114 por sus fixtures sin comprobar el panel cargado.
El error400 de #114 se identifica siempre como simulado en cliente, no fallo
real del servidor. Una espera cancelada no prueba proceso detenido.

No ejecutar síntesis, ASR, render ni nuevas baterías aprobadas en esta revisión.
Naturalidad/robótica de voces sigue aplazada. Mantener PR#2 en borrador,
presupuesto$0, originales/settings/.venv/ComfyUI intactos. Lectores de pantalla,
alto contraste físico, cancelación del cálculo y cobertura global E02/E05 siguen
fuera de este smoke. No se reinicia Studio durante la preparación.
