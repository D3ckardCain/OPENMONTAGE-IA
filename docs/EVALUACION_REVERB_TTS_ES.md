# Evaluación Reverb-TTS — #78

24-11-2026; seguimiento de #3. Revisión documental de código y metadatos públicos. No se instalaron paquetes, descargaron pesos o presets ni generó audio.

## Versiones y fuentes fijadas

| Componente | Revisión observada |
|---|---|
| [Código oficial](https://github.com/software-mansion-labs/Reverb-TTS/tree/2c72a7f9e9b7e8c9540d8823c7a8ef8833fd8346) | `2c72a7f9e9b7e8c9540d8823c7a8ef8833fd8346`, pyproject **1.0.1**; README, LICENSE, docs/reference.md, docs/usage.md, tts.py, text.py y audio.py revisados. |
| [Pesos y presets](https://huggingface.co/software-mansion/Reverb-TTS/tree/72be799c8fb6d56a206d260b425c48bf3bd5943d) | Código fija tag **v1.0.0**, resuelto a `72be799c8fb6d56a206d260b425c48bf3bd5943d`; HEAD observado `d0dd065f2a7147ba6509007409200c802fe720b3`. No confundir versiones de paquete y pesos. Solo se leyeron API de metadatos y model card. |
| [Codec fijado por código](https://huggingface.co/eustlb/higgs-audio-v2-tokenizer/tree/0e3a9177c2991016b8e5e17d23aa474ee665bef2) | `0e3a9177c2991016b8e5e17d23aa474ee665bef2`; prototipo sin mantenimiento y sin archivo LICENSE propio en su inventario. README remite al repositorio oficial Boson y declara archivos idénticos; no se verificó identidad binaria. |
| [Codec oficial Boson](https://huggingface.co/bosonai/higgs-audio-v2-tokenizer/tree/815a03f1b57dcb5ae918db415f22cd0c8a6f0f54) | `815a03f1b57dcb5ae918db415f22cd0c8a6f0f54`; metadatos `license: other`, texto BOSON HIGGS AUDIO 2 COMMUNITY LICENSE AGREEMENT leído. |
| [Verbalis](https://github.com/software-mansion-labs/Verbalis/tree/b14f1b3f96e759326935de12f81b35b87ec57f6a) | `b14f1b3f96e759326935de12f81b35b87ec57f6a`, **0.1.1** en cpp/CMakeLists.txt; MIT, THIRD_PARTY_NOTICES, README y manifiesto revisados. |

## Licencias y elegibilidad

El código Reverb es Apache-2.0: conservar licencia, avisos y modificaciones al distribuir. **Los pesos son CC-BY-NC-4.0 y permanecen bloqueados para producción comercial/monetizada.** El permiso del código no habilita pesos. La condición NC considera finalidad comercial, no solo si se cobra por una llamada. No convertir esta ruta en instalación pendiente automática ni proponer eludirla. [Texto íntegro CC](https://creativecommons.org/licenses/by-nc/4.0/legalcode.en).

Los presets son códigos de referencias en `voices/` del repositorio de pesos; no se encontró una licencia comercial separada que elimine NC ni documentación individual suficiente sobre derechos de cada voz. Una referencia propia requiere consentimiento y derechos adecuados; guardarla como códigos no elimina esa obligación.

El codec oficial incorpora términos Meta Llama 3 por referencia, avisos/atribución, política de uso y limitaciones adicionales. Su sección comercial exige licencia ampliada al superar **100.000 usuarios activos anuales**; no es Apache/MIT ni una aprobación comercial general. El alcance exacto de obligaciones incorporadas queda pendiente antes de adoptar/distribuir el artefacto. Cambiar al repositorio oficial tampoco resuelve NC de Reverb. B08 conserva ambas condiciones por separado.

Verbalis MIT es evaluable de forma independiente. Sus avisos incluyen cn2an MIT y Unicode v3 para código; datos de prueba tienen licencias propias (NeMo/WeText Apache-2.0 y corpus Leipzig CC-BY-4.0). No copiar corpus upstream como fixtures sin revisar su origen. No se importó código ni datos.

## Windows, recursos y offline

Python >=3.10, Torch/Torchaudio >=2.4, Transformers >=5.3,<6, huggingface-hub >=1.0, safetensors >=0.4, soundfile >=0.12, NumPy >=1.24 y Verbalis >=0.1.1,<0.2. No son versiones congeladas del entorno local. Windows requeriría wheels compatibles y entorno aislado; no se modifica .venv ni Python de ComfyUI. MPS corresponde a Apple; en Windows evaluar CUDA/CPU y recursos reales, sin suponer compatibilidad por la etiqueta OS Independent.

Modelo 297M + decoder 22M, siete idiomas incluido español. Documentación recomienda referencia de 3–10 s; >15 s puede degradar. El model card menciona 3–20 s en un resumen: conservar esa discrepancia y usar la recomendación detallada, no prometer tolerancia universal.

Paquete ofrece fp32/fp16/int8/int4; **convierte las variantes al dtype de ejecución al cargar**, por lo que tamaño de archivo cuantizado no demuestra igual ahorro de VRAM ni aceleración. Model card lista int8a8, pero VARIANTS del código revisado no lo admite. ExecuTorch tiene rutas MLX/Vulkan/QNN; sus demos no prueban runtime Windows. Benchmarks H200/5090 batch32 y Apple no predicen rendimiento de RTX4060 Laptop8GB/16GBRAM ni latencia de texto largo.

`from_pretrained` puede descargar modelo/tokenizer y codec por separado. Pasar carpeta local para el modelo **no localiza automáticamente el codec**. `preset_voices()` consulta listado remoto salvo carpeta de presets; `preset_voice()` puede usar caché o descargar. Verbalis usa reglas compiladas, no pesos, pero requiere paquete preparado. Offline exige inventario completo, revisiones/hashes, rutas locales/cache y red deshabilitada comprobada; ausencia debe dar error, nunca descarga implícita. No se acreditó operación offline del candidato. Uso no comercial local puede evitar cargos con recursos preparados; costo $0 no resuelve licencia comercial.

## Comparación y carencias útiles

OpenMontage ya tiene adaptadores/selectores de voz, perfiles y elegibilidad E16, ASR y tiempos E04, jobs E05; VoiceStudio #63 y VibeVoice #68 cubren funciones solapadas. No añadir otro selector/UI ni habilitar Reverb.

La aportación diferencial útil es **normalización española trazable antes de voz**, independiente del modelo. Verbalis ofrece `process_with_changes`; Python cuenta puntos de código y TypeScript unidades UTF-16, distinción necesaria para acentos y emoji. Español tiene revisión automatizada declarada, no la misma revisión humana de inglés/polaco: requerirá corpus propio y revisión lingüística.

## Tareas y aceptación futura

| Destino | Entrega | Criterio sin audio/modelos |
|---|---|---|
| E16/E04 | Contrato de texto original, texto hablado y mapa de sustituciones con versión/idioma/opciones/origen | Fixtures escritos de `12,50 €`, `1.234,56`, `03/04/2026`, `25 °C`, kg, siglas, negaciones, emoji y nombres propios. Fechas/monedas ambiguas quedan señaladas; no inventar una lectura. Original inmutable y offsets definidos; ida/vuelta del mapa comprobada. |
| E16 | Normalizador desacoplado y elegibilidad por artefacto | Mock de normalizador ausente/error/idioma no admitido; sin instalación ni fallback online. Pesos NC o licencia desconocida bloquean uso monetizado aunque código sea Apache. Referencia/preset sin derechos no se declara autorizado. |
| E04/E05 | Separar duración estimada, solicitada y medida; segmentación estable | Metadatos sintéticos con IDs/semillas/spans; una frase larga puede exceder el objetivo de ~15s; duración forzada altera la estrategia. Recorte de bordes/200ms finales no equivale a duración exacta ni alineación de palabras. Fallo/reanudación conserva segmentos válidos, sin inferencia. |

Implementación futura mediante mocks y herramientas existentes, no una integración Reverb aprobada. Evaluación completada; bloqueos comerciales y técnicos documentados, sin descarga de modelos, aceptación de términos ni generación.
