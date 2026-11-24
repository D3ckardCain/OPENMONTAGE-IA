# Cancelación de render manual (#92)

El botón **Cancelar render activo** aparece solo si la API anuncia
`render_cancel:true`. Envía el identificador exacto de intento a
`POST /api/studio/editor/{id}/render/cancel`; el agente usa la misma operación
con `studio_project_edit`, acción `render_cancel`, campo `attempt`.
No usa búsquedas por nombre ni termina otros FFmpeg.

`running → cancelling → cancelled`: la petición solo solicita cancelación.
El worker vigila su propio proceso, solicita terminate, espera2s y, si hace
falta, kill con otra espera2s. Solo acredita cierre después de `poll()!=None`.
El proyecto conserva el bloqueo de export hasta ese momento. Si excepcionalmente
el sistema no confirma el cierre, informa fallo explícito y conserva el bloqueo;
no inicia otro escritor ni reintenta indefinidamente. Timeout global sigue600s.

Se comprueba cancelación antes del encoder, entre verificaciones de fuentes y
antes de publicar. El hash de un archivo ya en curso puede terminar antes de
atenderla. No se declara aborto instantáneo de FFprobe/hash. Ante cancelación se
conserva el parcial en su carpeta UUID, sin URL descargable ni estado completado.
Originales y renders previos permanecen. No es reanudación desde bytes parciales:
**Preparar vista previa** crea otro intento desde la misma revisión, sin repetir
importaciones, herramientas de edición ni mutaciones del montaje.

Intento antiguo409; cancelación repetida del mismo intento ya cancelado devuelve
su estado. Reinicio del servidor informa interrupted para trabajo sin dueño;
no resucita un encoder ni simula cancelación. Studio4750 no se reinició.

## Pruebas y alcance

- Pruebas offline: proceso Python real que duerme, cancelación y timeout, cierre
  comprobado, API real en TestClient, origen agente, identidad y revisión intactas,
  rechazo de intento anterior, cancelación antes de spawn y nuevo intento.
- Prueba de navegador CI: botón, intento enviado y recuperación de controles;
  transporte interceptado, no acredita cierre por sí sola.
- `EVIDENCIA_CANCELACION_RENDER_20261124.json`: FFmpeg real con fuente existente,
  API real en proceso aislado. Entrada ralentizada con `-re` solo para obtener
  ventana determinista; cierre confirmado. Nuevo intento sin editar ni importar
  produjo MP4 con hash igual a la prueba previa y decodificación completa.

Validador opt-in `python -B -m scripts.validate_studio_render_cancel --workspace RUTA`
reutiliza el laboratorio preparado; no escribe proyectos activos ni reinicia el
servidor. Resultado no equivale a botón observado en Windows, escucha ni prueba
de cancelación en la instancia activa. Eso sigue pendiente de activar backend y
acceso a la ventana mediante las herramientas de escritorio permitidas.
