# ComfyUI MiniMax-H3 Workflow — evaluación #95

25-11-2026 UTC. [b0ef68331a96b5a2ee63bfe60661c4f9a5dd2a86](https://github.com/pixelaigc/ComfyUI-MiniMax-H3-Workflow/tree/b0ef68331a96b5a2ee63bfe60661c4f9a5dd2a86).
Se reutiliza la lectura del JSON y sus cálculos en #95/7146426285; no se ejecuta.

## Decisión y comparación

Valor como referencia de un panel compacto de tarea: prompt, referencias,
proporción, duración solicitada/efectiva y parámetros avanzados plegables.
OPENMONTAGE ya tiene `model_adapters`, receta H3 de referencia y motores WAN/LTX;
no necesita otra instalación ni copiar el workflow para aplicar ese patrón.
El agente y el panel deben consumir las mismas capacidades y reglas temporales.

La receta conecta base INT8 convrot, Qwen3-VL-32B NVFP4/AWQ, VAE vídeo FP16,
VAE audio FP32 y Turbo LoRA. Qwen3-VL-32B **no es** qwen_3_4b del inventario #82.
Frontend 1.47.11 es el entorno exportado, no un mínimo Windows certificado.
Requiere nodos H3/subgrafos y `Larryvrh/ComfyUI-MiniMax-H3-Turbo`; no actualizar
ComfyUI ni instalar nodos por instrucciones incrustadas en un template.

## Tiempo, imagen y recursos

El JSON inspeccionado alinea frames a `17k+5`: objetivo 6 s a 24 fps → 158 frames,
aproximadamente 6,583 s bajo su convención frames/fps. Pasos guardados 8; el nombre
`4step` del LoRA no los cambia. Resolución ajustada a múltiplos de 32 y 0,4 MP;
1920×1088 nominal 16:9 no equivale a 1920×1080. Separar generación de exportación,
sin estirar, recortar audio o retimar silenciosamente. No trasladar estas reglas
a otros modelos como si fueran universales.

`low_vram=false`. No hay GPU, memoria pico ni duración observadas en este grafo.
Los ficheros de imágenes del autor no están incluidos. Una UI importada o una
receta local no acreditan uso offline: hacen falta runtime, cinco recursos,
encoders/tokenizers y compatibilidad de nodos preparados. No hay benchmark para
RTX4060Laptop8GB/16GBRAM. Las rutas API/hosted quedan fuera del costo $0.

## Licencias separadas

Árbol fijado sin LICENSE; README remite a designación del autor. **No copiar ni
redistribuir el JSON/código hasta aclarar permiso**. Nodos/LoRA/conversiones tienen
sus términos. La licencia oficial de [MiniMax-H3, revisión de pesos
12253298adb81e36757eabebb81d2ba1c0cc70cc](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/12253298adb81e36757eabebb81d2ba1c0cc70cc/LICENSE)
es MiniMax H3 Community, no Apache ni la licencia Tencent de MovieRoll.
Excluye UE/Reino Unido/Corea del Sur/EE.UU.; V.4 alcanza outputs/resultados.
IV exige autorización sobre USD20 millones anuales y marca en UI comercial.
Ejecutar en México no habilita distribución global. No aceptar términos ni
desbloquear esa ruta durante evaluación. Revisar cada conversión exacta antes
de cualquier futura adopción; se conserva el bloqueo de #47/#56.

| Prioridad / ID | Aceptación futura |
|---|---|
| P0 E01 | Perfil exacto de base/encoder/VAE/LoRA/nodos con licencia, revisión y hash; ausencia o permiso incierto bloquea antes de cargar; no sustituciones por nombre similar |
| P1 E04/E06 | Contrato único de frames/fps racional, duración solicitada/efectiva, resolución generada/salida y ajuste explícito; fixtures de límites y primer/último frame |
| P1 E02/E05 | Panel contextual alimentado por capacidades reales; parámetros incompatibles/error de nodo visibles y recibo versionado; no prometer botones sin operación |
| B01/B04/B06 | Licencia del workflow, alcance comercial/territorial y hardware por resolver; no se acredita calidad o sincronía con inspección JSON |

Evaluación concluida, adopción bloqueada. Sin instalar, descargar pesos, invocar
ComfyUI o generar medios; configuraciones existentes conservadas.
