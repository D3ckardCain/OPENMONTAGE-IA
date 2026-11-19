# Integraciones preparadas para pruebas reales

46 familias: 31 motores nativos y 15 rutas ComfyUI. Ninguna inferencia nueva está certificada en esta fase.

Una receta implementada no garantiza que el runtime, sus versiones o los pesos completos estén instalados. En ComfyUI el grafo API se materializa mediante el botón de preparación contra la versión real del servidor, antes de generar. Las variantes concretas se revisan al vincular los pesos.

| Familia | Ruta preparada | Entradas principales |
|---|---|---|
| qwen-edit | canvas_compiler | text, output_dir |
| faster-whisper | isolated_native_workflow | input_path, output_dir |
| chatterbox | isolated_native_workflow | text, output_dir |
| cosyvoice | isolated_native_workflow | text, reference_audio, reference_text, output_dir |
| depth | isolated_native_workflow | input_path, output_dir |
| qwen3 | isolated_native_workflow | text, output_dir |
| qwen-vl | isolated_native_workflow | input_path, text, output_dir |
| wan-vace | canvas_compiler | text, output_dir |
| wan-camera | isolated_native_workflow | text, input_path, camera_path, output_dir |
| aligner | isolated_native_workflow | input_path, text, language, output_dir |
| birefnet | isolated_native_workflow | input_path, output_dir |
| grounding-dino | isolated_native_workflow | input_path, text, output_dir |
| florence | isolated_native_workflow | input_path, output_dir |
| siglip | isolated_native_workflow | input_path, labels, output_dir |
| m2m100 | isolated_native_workflow | text, source_language, language, output_dir |
| parakeet | isolated_native_workflow | input_path, output_dir |
| smolvlm | isolated_native_workflow | input_path, text, output_dir |
| wan-control | isolated_native_workflow | text, control_video, output_dir |
| wan-s2v | isolated_native_workflow | text, input_path, reference_audio, output_dir |
| voice-design | isolated_native_workflow | text, instruction, language, output_dir |
| dwpose | isolated_native_workflow | input_path, output_dir |
| lama | isolated_native_workflow | input_path, mask_path, output_dir |
| silero | isolated_native_workflow | input_path, output_dir |
| minilm | isolated_native_workflow | text, output_dir |
| ocr-latin | isolated_native_workflow | input_path, output_dir |
| ocr-det | isolated_native_workflow | input_path, output_dir |
| wan | wan_api_preset | text, output_dir |
| cosmos | canvas_compiler | text, output_dir |
| ltx-legacy | canvas_compiler | text, output_dir |
| mochi | canvas_compiler | text, output_dir |
| cogvideo | isolated_native_workflow | text, output_dir |
| kandinsky | canvas_compiler | text, output_dir |
| longcat | isolated_native_workflow | text, output_dir |
| longcat-avatar | isolated_native_workflow | text, input_path, reference_audio, output_dir |
| magihuman | isolated_native_workflow | text, output_dir |
| ltx23 | canvas_compiler | text, output_dir |
| ltx25 | canvas_compiler | text, output_dir |
| hunyuan15 | canvas_compiler | text, output_dir |
| framepack | isolated_native_workflow | text, input_path, output_dir |
| h3 | canvas_compiler | text, output_dir |
| qwen-image | canvas_compiler | text, output_dir |
| flux-klein | canvas_compiler | text, output_dir |
| z-image | canvas_compiler | text, output_dir |
| kokoro | isolated_native_workflow | text, voice, output_dir |
| qwen-tts | isolated_native_workflow | text, voice, language, output_dir |
| acestep | canvas_compiler | text, output_dir |

Los requisitos de los motores originales y de las aplicaciones están en CENTRO_MANDO_INTEGRACIONES_ES.md. Los orígenes de las plantillas y las revisiones se conservan en sus manifiestos.

Comprobación de código: 113 pruebas de contratos pasadas. No se ejecutó ningún modelo real, instalador o aplicación de escritorio.
