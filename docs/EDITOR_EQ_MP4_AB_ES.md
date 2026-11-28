# EQ/compresor: comparación MP4 real (#174)

Validación del 26-11-2026 sobre una copia, servidor aislado 4770. Un único MP4 nuevo con EQ y compresor; se reutilizó el bypass aprobado. Mismo clip, EDL salvo bypass y configuración: 4 s, 640×360, 8 fps, H.264/AAC, estéreo 48 kHz. Original y Studio 4750 intactos.

Los 32 fotogramas decodificados coinciden. Cada audio contiene 192.000 muestras por canal. EQ: 120 Hz +6 dB, 1000 Hz 0, 6000 Hz −6; compresor: −18 dB, ratio 4, ataque 5 ms, release 100 ms. El clip afectado ocupa 1,000–1,5271875 s.

RMS global bypass/procesado: −13,6994/−13,7224 dBFS; en la ventana afectada: −11,8881/−11,9983 dBFS. Pico global de muestra: −0,4412 dBFS en ambos, cero muestras fuera de escala. La energía del cambio dentro/fuera del intervalo es 252,52×. Son mediciones de mezcla codificada, no una medida de calidad percibida ni de true peak. No se repitieron PCM sintéticos, catálogo, CI ni render bypass.

[Informe completo](EDITOR_EQ_MP4_EVIDENCIA_20261126.json). El comparador usa snapshots Python nativos para conservar flotantes y enteros de metadatos: serializarlos mediante JavaScript alteraba la representación de la identidad. No se encontró un fallo del motor que requiriera corregirlo.

## Una única escucha humana pendiente

Abrir `C:\OPENMONTAGE-IA\projects\qa174-eq-ab-review\escucha-ab.html`. Alternar A/B en el primer impacto (1,000–1,527 s), manteniendo el mismo volumen. Indicar preferencia A/B y si se oye distorsión o bombeo. A es bypass; B lleva la cadena activa. La página conserva el instante al cambiar. Se comprobó en navegador duración 4 s, cambio en 1,125 s y ausencia de errores; esto no acredita escucha humana. Los MP4 de revisión son enlaces duros locales, sin copias físicas adicionales.

## Activación principal pendiente

Esperar confirmación explícita del reinicio manual. Después, sin reiniciar: comprobar identidad residente/disco y capabilities `audio_processing`, `sfx_catalog`, `sfx_favorites`; en una nueva copia verificar una preescucha/inserción y guardar EQ/compresor/bypass, deshacer/rehacer y reapertura. Recuperar estado antes de repetir escrituras con respuesta incierta. Registrar resultados por separado en #174/#177; no repetir síntesis, renders ni pruebas aprobadas.

Las ocho descargas LongCat/Wan tienen otra condición independiente: esperar confirmación de finalización. Sus carpetas VERIFICAR no se han consultado. PR #2 permanece en borrador; quedan pendientes buses, automatización y otras partes de #174.
