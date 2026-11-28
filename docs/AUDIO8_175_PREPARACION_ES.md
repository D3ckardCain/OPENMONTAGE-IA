# Audio8 #175 — preparación, sin pesos ni síntesis

Selección documental: [Realistic Air oficial](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/6bf7a980759d8022a66922ee975dab99229a2dd9), revisión `6bf7a980759d8022a66922ee975dab99229a2dd9`, licencia Apache-2.0 declarada. El manifiesto `AUDIO8_175_MANIFIESTO_20261126.json` fija 15 archivos mínimos, tamaños, hashes publicados, URLs y destinos propuestos. Total: 2.565.465.528 bytes. No descargar además Preview ni GGUF.

No se localizaron sus pesos en las raíces de modelos C:/D:/F:, descargas de Windows ni los registros HF de FDM revisados. E: está conectado, pero la raíz esperada no existe. Esto describe el alcance de búsqueda; no prueba ausencia en cualquier carpeta arbitraria. No se inició otra descarga de pesos.

Se obtuvieron solo pequeños fuentes, configuraciones y textos legales para revisión estática. Se verificaron contra los Git blobs oficiales. No se ejecutó código remoto. El cargador del codec admite búsqueda remota si falta el archivo: la futura integración deberá exigir el conjunto completo y bloquear red. Usa `torch.load(weights_only=True)` y carga estricta; esta observación no sustituye una auditoría completa.

Python≥3.10, torch/torchaudio≥2.5 y Transformers≥4.57,<5 según la tarjeta. Los metadatos del entorno Qwen existente satisfacen esos rangos (2.6.0+cu124 y 4.57.3); no se modificó ni se cargó el modelo. Compatibilidad efectiva y memoria quedan pendientes. El ensayo upstream H20 BF16 no acredita RTX4060 Laptop 8GB.

Pendientes: localizar o completar los dos pesos exactos, verificar cada archivo nuevo una vez, comprobar memoria y ejecutar una muestra española acotada con recibo y cancelación. No está operativo ni integrado en la ventana de voces todavía. Preview0.1B conserva su licencia comunitaria condicionada por ingresos; no hereda Apache-2.0 de Realistic Air o del código.
