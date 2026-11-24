# Encuadre, títulos, presets y mezcla manual (#92)

Entrega funcional del contrato `timeline-v3`. Los controles aparecen solo cuando
`GET /api/studio/editor/capabilities` confirma sus operaciones. Un servidor Python
anterior no las activa por recargar HTML: el panel las oculta para evitar botones
inoperantes. No se reinició Studio4750, por instrucción del usuario.

Selecciona un clip y abre **Encuadre y transformaciones** en el inspector:
encajar con bandas o recortar para llenar, giro90/180/270, reflejos, zoom1–4
y foco horizontal/vertical0–1. El zoom requiere recorte explícito. Restablecer
elimina la transformación. La fuente original nunca se sobrescribe.

**Títulos visibles** guarda texto, intervalo, tamaño de referencia1080p y posición
segura superior/inferior o centro. La pista adicional permite seleccionarlos;
editar/quitar y deshacer conservan el mismo proyecto que usa el agente.
Se queman realmente con el compositor ASS existente, con texto escapado.
Límite:20 títulos y1000 caracteres cada uno; sin tipografías nuevas ni inferencia.

**Preset de salida editable** permite dimensiones pares64–3840, hasta3840×2160
píxeles y1–60FPS. Nombre y destino son etiquetas locales, no publicación ni
garantía de requisitos de una plataforma. Vista previa y exportación usan el
mismo grafo; la primera limita resolución. No se deforma la relación de aspecto.

**Mezcla de salida** aplica ganancia maestra0–4 y normalización opcional con
`AudioMixer._loudnorm_filter` existente. El limitador no añade ganancia automática.
El medidor del navegador mide el archivo reproducido; no calcula anticipadamente
la mezcla editada. Para oír/ver cambios hay que preparar una vista previa actual.

Todas las escrituras usan revisión, historial y undo/redo de `studio_project_edit`:
`transform`, `title_add/update/remove`, `output_custom`, `audio_mix`. No hay un
segundo proyecto del agente. El hash audiovisual incluye estos cambios, excluye
etiquetas de destino, marcadores y bloqueos. Exportaciones antiguas se conservan;
si su contrato difiere no se presentan como vista previa actual.

## Evidencia y pendientes

`EVIDENCIA_EFECTOS_MANUALES_20261124.json` registra dos MP4 reales de2s,
640×360/24FPS, decodificados completamente, derivados de medios existentes en
un laboratorio aislado, sin modificar el proyecto fuente. Se inspeccionó un
fotograma con título y encuadre; mezcla normalizada medida−18.07LUFS con objetivo−18.
No equivale a escucha, sincronía percibida ni observación del panel local.

Reproducción opt-in: `python -B -m scripts.validate_studio_timeline_model
--source-project ID --workspace RUTA --recheck --effects`, reutilizando el
laboratorio ya preparado. Genera nuevas salidas de QA, conserva anteriores.
Las pruebas unitarias comprueban rollback/undo, validación, identidad y grafo;
la prueba de navegador usa transporte interceptado y el modelo puro real,
sin carga AV. CI y validación local se registran por separado.

Pendientes: activar backend actualizado bajo la restricción de no reiniciar,
observación/escucha en Windows, transiciones, capas de vídeo, cancelación del
export y montaje con proyecto de producción. #92 permanece abierto.
