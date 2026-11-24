# OpenJutsu: evaluación #56

24-11-2026 UTC. Fuente `D3voz/openjutsu@7fe118bb5a61fcfac0148e1bfea3dd29884dbf26`.
package privado sin versión semántica: fijar commit, no inventar release. Revisión
de README, licencia, package, launcher, setup, transporte y dos workflows API.
No instalar, ejecutar ni modificar ComfyUI/Python/nodos actuales.

## Decisión y contraste

Candidato de edición localizada con máscara/roles, no reemplazo del Studio.
OPENMONTAGE ya permite grafos ComfyUI propios, bindings, etiquetas de modelos,
procedencia y registros de prompt_id (`tools/video/comfyui_video.py`,
`lib/comfy_job_records.py`, `lib/model_adapters.py`). Eso no equivale a edición
H3/SAM preparada ni certifica seguimiento de personas, objetos o relighting.
Reutilizar ese puente; no importar Next.js ni otra cola/proxy antes de demostrar
necesidad. Agrupar sus requisitos H3 con [FreeVideo #47](EVALUACION_FREEVIDEO_ES.md),
manteniendo separados runtime, loaders, cuantización y grafos.

Lectura de [simple.api.json](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/workflows/simple.api.json)
y [object.api.json](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/workflows/object.api.json):
70 y 54 nodos respectivamente; incluyen SAM3_VideoTrack, plan de swap, latent de
edición, context loop y ensamblado. No son un prompt intercambiable con WAN/LTX.
No se probó inferencia ni se auditó cada nodo externo.

## Requisitos y límites

[README](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/README.md):
Node>=22.6, ComfyUI>=0.41.2, GPU NVIDIA; prueba upstream RTX4060Ti16GB/64GBRAM.
La cifra de demo no acredita laptop8GB/16GB ni cualquier duración/resolución.
H3 diffusion/LoRA, encoder32B cuantizado, VAE vídeo/audio, SAM3.1 y VLM visual son
recursos distintos; tamaño de archivo no es pico VRAM. Alternativas VLM pequeñas no
reducen automáticamente requisitos del generador. Flujo picture agrega FLUX,
SolarRenderer/control y normales; no incluirlo en un perfil mínimo sin necesidad.

[package](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/package.json):
@comfyorg/sdk0.5.0, Next^16.4.2, React^19.3.1; rangos no son lock de una instalación.
[launcher](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/start_openjutsu.bat)
crea .venv-proxy, instala comfy-api-proxy0.1.6, aplica
[patch_proxy.py](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/patch_proxy.py),
ejecuta npm ci/build y crea configuración. Abrirlo no es diagnóstico sin efectos.
No se ejecutó ni se aplicó su ajuste AIOHTTP_NOSENDFILE o websocket a ComfyUI.

[setup](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/lib/setup.ts)
inspecciona nodos/listas de modelos elegidos y endpoint de reconnect; no comprueba
dependencias Python, SHA256 ni memoria. Discriminar archivo ausente, nodo no
registrado, error de importación, acceso y recurso insuficiente en futuros reportes.

## Licencias, $0 y offline

[Código MIT](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/LICENSE)
con avisos; no cubre modelos/nodos. H3 Community exige revisar territorio,
distribución de outputs y demás condiciones del artefacto exacto; la revisión #47
es señal de bloqueo compartido, no licencia verificada de todos estos archivos.
SAM, VLM, FLUX, LoRAs, detectores y nodos necesitan versiones/avisos propios.
InsightFace buffalo_l se descarga al primer uso según README: excluir face-fix
hasta resolver pesos, derechos y cierre offline; MIT de la app no lo habilita.

[Transporte](https://github.com/D3voz/openjutsu/blob/7fe118bb5a61fcfac0148e1bfea3dd29884dbf26/lib/comfy.ts)
usa SDK y proxy; low() cae en COMFY_CLOUD_BASE_URL sin COMFY_BASE_URL. Configurar
endpoint local explícito y rechazar ausencia/remoto, sin fallback de pago. Offline
solo con todo aprovisionado y egreso bloqueado, no probado aquí. No claves, cloud,
modelos ni descargas ejecutadas. Fallos de caras pequeñas/reflejos y persistencia
del proxy no se resuelven por tener una web accesible.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P0 | Perfil elegible cerrado junto a #47 | Artefactos/commits/SHA256/tamaños/licencias y disco/RAM/VRAM separados; condiciones incompatibles dejan ruta bloqueada, nunca descarga implícita |
| P1 | Preflight de grafo | Fixtures object_info/modelos de ambos grafos, nodos faltantes/import fallido y acceso denegado; no ejecutar ni instalar nodos |
| P1 | Contrato de máscaras/roles | IDs, intervalos, máscara, identidad y regiones preservadas trazables; sintéticos sin personas reales; incompatibilidades explícitas |
| P2 | Adaptador al puente existente | prompt_id/seed/grafo/hash/progreso y recibos; localhost obligatorio, sin proxy nuevo salvo necesidad probada |
| P2 | Cancelación/recuperación | Cerrar SSE no se anuncia como interrupción GPU; cancelar solo trabajo propio, persistir evidencia backend, no repetir segmentos completados |
| P3 | Plan de calidad posterior | Hardware y licencia resueltos antes de pruebas reales; caras pequeñas/reflejos/máscaras revisados visualmente, no aprobación automática |

Bloqueada adopción ejecutable por cierre de licencias/perfil/hardware y necesidad
de instancia aislada. Especificación/preflight con mocks puede avanzar sin instalar.
No se declara automatización completa ni modificación del contenido realizada.
