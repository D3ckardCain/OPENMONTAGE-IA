# Resaltado por palabras guardadas — #174/#115/#129

Se reutilizan `studio_word_clock`, las transcripciones y cues existentes. No hay ASR, traducción, alineador ni modelos nuevos. El texto completo del cue permanece visible y una palabra/unidad ASR cambia de color solo durante su intervalo guardado. Los huecos quedan sin palabra activa; no se reparte artificialmente la duración entre palabras.

En **Resaltado por palabra · tiempos guardados**, elegir transcripción, revisar texto/tiempos y confirmar antes de activar. Cada botón de palabra mueve el cursor al tiempo del montaje existente. Elegir colores o desactivar conserva el estado editable. Usuario y agente comparten la operación `subtitle_karaoke`, revisión optimista, historial y reapertura.

## Correspondencia y límites

El lector existente valida fuente, orden, cobertura declarada y tiempos. Cada cue debe corresponder exactamente a las unidades ASR completas dentro de su intervalo; saltos de línea/reflow se admiten sin cambiar tokens. Si se borra una negación, cambia texto, corta una palabra, se alteran datos ASR o queda obsoleta la revisión, se rechaza el resaltado en lugar de inventar tiempos. La edición manual puede continuar; hay que revisar/reaplicar el borrador o desactivar karaoke antes de exportar quemado si ya no corresponde.

La procedencia incluye ID de ocurrencia, tiempos/racionales de fuente, hash de palabras/transcripción/fuente, cobertura declarada y origen ASR. No se vuelve a hashear el medio. La exactitud de la alineación sigue siendo la evidencia declarada por el ASR original, no una medición nueva por convertir relojes.

Límite2000 palabras/400 cues por consulta. ASS usa eventos de texto completo sin solaparse, particionados en fronteras de palabras/gaps redondeadas a centésimas. No es barrido progresivo de letras ni una precisión de1ms en el quemado. Se rechazan unidades que colapsen a duración cero en ASS. Se reutilizan tamaño/posición y la zona segura configurada, con texto escapado.

**Seleccionable MP4/SRT:** texto/tiempos, sin garantía de color o karaoke. Activar este ajuste no invalida el render seleccionable si nada audiovisual cambia. **ASS descargable/quemado:** resaltado visible; el quemado no es una pista editable. Un cambio de palabras/cobertura/procedencia invalida el render con resaltado y obliga a revisar.

## API y agente

Capability `subtitle_karaoke`. Acción de lectura del puente3.9.0 `subtitle_karaoke` con `set_id`, o `GET .../{pid}/subtitles/karaoke?set_id=...`. Devuelve `ready`, blockers, spans, tiempos, cobertura y hashes. Activación normal mediante acción `command`:

```json
{"operation":"subtitle_karaoke","revision":12,"enabled":true,"set_id":"ID","highlight_color":"#FFD24D","inactive_color":"#FFFFFF","reviewed":true,"input_edl_sha256":"HASH_REPORTE","word_data_sha256":"HASH_PALABRAS"}
```

`enabled:false` conserva ajustes sin resaltado. Colores estrictos #RRGGBB, sin expresiones ASS del usuario. Tras respuesta incierta, recuperar estado antes de repetir la escritura. La salida ASS obsoleta devuelve un error claro; no se presenta como alineación válida.

## Evidencia

9 casos nuevos focalizados acreditan spans/gaps/negación, historial, neutralidad de formato seleccionable, invalidación de palabras/cobertura, errores de revisión/color, reflow compatible y agente/API/ASS. No se repiten pruebas aprobadas de ASR o reloj.

Panel/API reales4779 sobre copia del proyecto portugués con palabras guardadas, recortada a4s para esta prueba. Revisar/activar, undo/redo/reapertura y dos salidas nuevas necesarias: MP4 seleccionable y quemado. Cues seleccionables extraídos coinciden y payload AAC idéntico entre formatos; no se repitió síntesis ni escucha. ASS contiene eventos derivados de los tiempos reales guardados. Fotogramas0,12s y0,52s inspeccionados: «Lamin» y «Yamal» resaltadas respectivamente. Medición de píxeles de color dentro de la región de subtítulos acompaña la inspección, sin inferir alineación acústica.

El primer comparador leyó un snapshot UTF8 con el charset por defecto de Windows; se corrigió la lectura del helper a UTF8 explícito. No había corrupción del texto de proyecto ni se cambiaron sus acentos para hacer pasar la prueba. Se reutilizaron las exportaciones; no se volvieron a renderizar por ese diagnóstico.

[Evidencia](EDITOR_SUBTITULOS_KARAOKE_EVIDENCIA_20261126.json). QA propio cerrado, sin tocar4750. Pendientes: activación conjunta tras confirmación manual, revisión humana, muestra española y estilos por cuenta dependientes168. No se cierran107/115/129 por esta ampliación. .venv/ComfyUI/configuración/originales intactos; PR2 en borrador. La cola continúa con GSAP186/132 y luego P1.
