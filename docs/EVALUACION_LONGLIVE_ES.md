# LongLive 1.0, 2.0 y Plug — evaluación #98

25-11-2026 UTC. Código [31c70d9071cd7851d82939806dc9fac645fcabe5](https://github.com/NVlabs/LongLive/tree/31c70d9071cd7851d82939806dc9fac645fcabe5).
Se reutiliza #98/7146391963 y se completan licencias/Plug/NVFP4. Long-WAM/robótica
quedan fuera de esta evaluación; no se leen ni ejecutan sus stacks.

## Decisión y comparación

Interés en continuidad entre segmentos e instrucciones que cambian durante una
sesión. No sustituir motores/adaptadores WAN/LTX existentes: definir antes el
contrato de segmentos, prompt vigente, contexto y recibos sobre E05/E06/E11.
Exportar un segmento terminado no significa poder serializar y reanudar su KV
cache ni obtener generación interactiva en tiempo real.

| Ruta | Evidencia upstream y límite local |
|---|---|
| 1.0 | Modelo1.3B y demostraciones largas/H100. No certifican memoria/latencia en8GB ni calidad estable en240s locales |
| 2.0 FP8 | Python3.10, Torch2.8+cu128, TorchAO0.13 en H100SM90; CC>=8.9. Carga BF16 antes de cuantizar; el smoke config solo valida8frames latentes, no vídeo largo. Cumplir arquitectura no garantiza pico de memoria |
| 2.0 NVFP4 | Recetas con FourOverSix/TransformerEngine y kernels CUDA, objetivos SM100/120; no receta validada para RTX4060Laptop. Los backends y formatos de checkpoint no son intercambiables |
| Plug | Adaptadores por familia Wan2.1-14B/Wan2.2-5B/MiniMax-H3, few-step y CFG distintos; mantener conditioning propio. Python3.12/Torch2.9.1. Merge requiere pesos DiT sin cuantizar, RAM y shapes compatibles; no ejecutarlo sobre originales |

Fuentes: [2.0 README](https://github.com/NVlabs/LongLive/blob/31c70d9071cd7851d82939806dc9fac645fcabe5/LongLive2.0/README.md),
[Plug README](https://github.com/NVlabs/LongLive/blob/31c70d9071cd7851d82939806dc9fac645fcabe5/LongLive-Plug/README.md).
Las cifras2.0 de29,7/45,7FPS excluyen decodificación VAE y proceden de GB200180GB;
no son tiempos fin a fin ni resultados de la laptop. La integración comunitaria
Plug citada prueba una ruta Windows11/RTX5090/BF16-14B, no todas las variantes.

## Licencias: el cambio a Apache del código no resuelve pesos

[Código Apache-2.0](https://github.com/NVlabs/LongLive/blob/31c70d9071cd7851d82939806dc9fac645fcabe5/LICENSE).
Metadata oficial consultada sin descargar pesos:

| Artefacto / revisión HF | Términos declarados y decisión |
|---|---|
| [LongLive-1.3B@cda9138d93872ef109d9a74c270184eb3a5acc6e](https://huggingface.co/Efficient-Large-Model/LongLive-1.3B/tree/cda9138d93872ef109d9a74c270184eb3a5acc6e) | CC-BY-NC-SA-4.0 en ficha; comercial bloqueado hasta aclarar artefacto/permiso. No sustituir por Apache del código |
| [2.0 BF16@8521079b863720a57c1a8d9b19c8d9e6ccb04c0f](https://huggingface.co/Efficient-Large-Model/LongLive-2.0-5B/tree/8521079b863720a57c1a8d9b19c8d9e6ccb04c0f) | NVIDIA Open Model License, no Apache |
| [2.0 NVFP4-S4@427ffb75f0a3ae82714cd4b3aaa7463839da38a7](https://huggingface.co/Efficient-Large-Model/LongLive-2.0-5B-NVFP4-S4/tree/427ffb75f0a3ae82714cd4b3aaa7463839da38a7) | Misma licencia NVIDIA; revisar cada conversión/backend y companions |
| [Plug Wan2.2 few-step@38a6ec4e8f5b644749d3072bfe1ac383d00951c0](https://huggingface.co/Efficient-Large-Model/LongLive-Plug-Wan2.2-TI2V-5B-few-step/tree/38a6ec4e8f5b644749d3072bfe1ac383d00951c0) | Ficha Apache-2.0 del adaptador; no habilita otros adaptadores ni cambia licencia del backbone |

[NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/),
texto24-10-2025: admite uso comercial sujeto a términos, política y redistribución
con licencia/avisos. No clasificarla como NC ni como permiso incondicional.
El texto de trial alojado en la ficha no convierte un servicio API en requisito
para inferencia local. H3 conserva sus propios límites territoriales/comerciales;
Wan/tokenizer/VAE/LoRA y datos tienen términos separados.

## Tareas, offline y prioridad

P1 E05/E06/E11: segmento y prompt versionados, reloj/contexto declarados, cancelación
y recibo parcial; reanudar solo estados que el backend realmente pueda restaurar.
Aceptación con datos: cambio de prompt invalida lo dependiente, conserva segmentos
completos y distingue recomputación de reanudación nativa. P0 E01: perfil por
familia, cuantización, licencia y backend; una cifra de tamaño no acredita VRAM.

Adopción de runtime P3, condicionada a B01/B04/B06: hardware/Windows, pico de RAM,
licencias por artefacto y necesidad frente a motores actuales. Offline solo con
stack/pesos completos y recursos sin egreso; no requiere API pagada en teoría,
pero no se acredita ejecución útil $0 aquí. No instalar, fusionar LoRAs, descargar
pesos o generar vídeo para completar esta evaluación.
