# Voces: reproducir muestras existentes

Continuación de #96 y c4161e9. No se repiten las síntesis españolas.

En Audio, abre **Voces Chatterbox · muestras guardadas** y pulsa **Reproducir**
en la tarjeta es-MX/LatAm o es-ES. La ventana usa tarjetas, no combobox, según
#174. **Actualizar muestras** vuelve a consultar archivos, no genera voz.
El reproductor usa los WAV
ya comprobados de2,32s y2,20s, sin importar Torch ni cargar pesos. La selección
se conserva localmente al reabrir. Escucha humana/calidad sigue pendiente.
La creación de nuevas tomas desde este panel continúa separada y pendiente;
el control actual reproduce archivos, no envía peticiones de inferencia.

GET `/api/studio/editor/chatterbox/profiles` incluye `samples`; cada muestra
ofrece un enlace GET `/api/studio/editor/chatterbox/profiles/{id}/sample`.
Se comprueban el recibo completado, identidad actual del WAV y pertenencia a
`projects/`; perfiles desconocidos, archivos cambiados o rutas externas no se
exponen. La recuperación no depende de que el modelo/GPU siga disponible.
Un futuro recibo válido de Turbo inglés puede aparecer sin cambiar el panel;
no se ofrece como sustituto español ni como muestra completada inexistente.

Cuatro pruebas nuevas focalizadas pasan: recuperación sin runtime, identidad
cambiada/perfil desconocido, ruta externa y recibo Turbo explícito. La prueba
real en Studio aislado4766 decodifica/reproduce ambos WAV, observa avanzar el
tiempo del reproductor y recupera la selección tras recargar. Solo GET,
ninguna síntesis ni escritura, errores de página0; no representa escucha humana.

Activación agrupada con el perfil persistente HyperFrames de #132: comprobar
trabajos activos, conservar estado y detener/arrancar únicamente4750 desde
`C:\OPENMONTAGE-IA` con `.venv`. Antes de actuar, inspección del servidor:
PID138604, cola pausada/vacía, worker y tarea local inactivos;48 archivos de
estado guardados en copia privada, ningún estado persistente activo.
Se ejecutó UN reinicio autorizado: PID138604 detenido y Studio iniciado con
`.venv` desde el mismo proyecto. PID activo153088, salud correcta, huella
residente=disco y `restart_required=false`. Capacidad de muestras guardadas
activa; HyperFrames disponible mediante perfil persistente/ejecución CLI ya
acreditada. No se repitieron probe/doctor/render ni se usó perfil QA al arrancar.
Los48 estados guardados permanecen idénticos tras la activación.

En4750 se comprobó reproducción real de los dos WAV, recuperación al recargar,
ventana visual con tarjetas, foco de teclado, Esc que cierra/pausa y GitHub Dark.
Solo GET, errores de página0, sin síntesis ni escucha humana. El ajuste de
tarjetas fue estático del panel y no necesitó otro reinicio del backend.
Datos en `ACTIVACION_MUESTRAS_HYPERFRAMES_20261126.json`.

Turbo continúa necesitando identificar una referencia local autorizada >5s.
Las muestras sintéticas encontradas son más cortas; se solicitó la ruta y su
procedencia al usuario mientras continúa el trabajo independiente. No se
repite ni rellena la referencia para eludir el requisito, ni se usa una voz
real sin autorización. CosyVoice sigue pendiente de recursos, sin nueva carga.

Audio8 #175 y mejoras del editor #174 se añadieron DESPUÉS de esta tarea,
junto a la revisión de la lista completa de descargas acordada. Mantener
verificaciones válidas y PR2 en borrador; no instalar ni descargar duplicados.
