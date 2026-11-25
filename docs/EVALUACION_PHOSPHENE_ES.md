# Phosphene — evaluación #99

25-11-2026 UTC. [133fe6b994945d09e1bb9fe6621b84778959d45d](https://github.com/mrbizarro/Phosphene/tree/133fe6b994945d09e1bb9fe6621b84778959d45d).
`VERSION` y README fijan **5.0.86**, corrigiendo la mención inicial5.0.85 sin
mover la revisión. Reutiliza arquitectura/storyboard de #99/7146360468.

## Utilidad y comparación

Interesa el flujo generación→tomas→selección→montaje, no su catálogo de modelos.
OPENMONTAGE ya tiene biblioteca, jobs, recibos, registro de motores y editor
revisionado manual/agente. Mantener ese documento como única fuente de preview,
render y export; no importar otro storyboard o UI. La generación entrega una
toma candidata, no un reemplazo automático del montaje editado por el usuario.

La [arquitectura](https://github.com/mrbizarro/Phosphene/blob/133fe6b994945d09e1bb9fe6621b84778959d45d/docs/ARCHITECTURE.md)
separa cola, editor y render JSON stdin/stdout, pero relata acoplamiento global y
reestructuración de un panel enorme. Reutilizar contratos/accesores únicos, no
replicar ese estado. No se acreditó paridad agente/manual por leer arquitectura.

Hallazgo útil para los reinicios de #92: HTML cargado al iniciar y recursos
servidos desde disco pueden mezclar versiones. Studio carece de identificación
residente de commit, según activación documentada: E01 debe aportar identidad de
build/capacidades coherente entre servidor y UI, con aviso de actualización;
no resolverlo reiniciando automáticamente ni repitiendo capturas HTTP.

## Licencias, Pro, Windows y offline

[Aplicación MIT](https://github.com/mrbizarro/Phosphene/blob/133fe6b994945d09e1bb9fe6621b84778959d45d/LICENSE).
Pesos/LoRAs/recursos no heredan MIT: H3, FLUX, Qwen y otros tienen términos por
variante. Las condiciones ya documentadas de H3/klein no cambian por un port MLX.
README dice gratuito, pero `pro_perks.json` y arquitectura separan funciones
Pro, entre ellas Remote, mejoras de velocidad, re-voice y relleno vertical.
No prometerlas dentro del núcleo gratis ni eludir sus comprobaciones.

El [README fijado](https://github.com/mrbizarro/Phosphene/blob/133fe6b994945d09e1bb9fe6621b84778959d45d/README.md)
declara Apple Silicon M1–M5/MLX y **no Windows**. La existencia de helpers con
nombre windows no acredita una distribución Windows soportada. Tampoco16GB
unificados equivalen a8GBVRAM/16GBRAM. Cifras de tiempos/memoria son mediciones
upstream de Macs, no perfil de nuestra GPU.

Core local sin API/cuenta obligatorias según documentación, una vez preparados
modelos, codecs y fuentes. Instalación, updates y modelos necesitan red; algunos
modelos se obtienen al primer uso. No ejecutar install/update/reset/patches ni
habilitar estadísticas/servicios para la evaluación. Excluir Pro del perfil $0.

| Prioridad / ID | Entrega y aceptación futura |
|---|---|
| P0 E01/E02 | UI muestra build y capacidades del proceso; mismatch conserva edición y ofrece diagnóstico claro sin recarga/reinicio automático |
| P1 E05/E06 | Toma candidata versionada con motor/semilla/recibo; insertar o cambiar versión es operación reversible en el mismo EDL; cancel no reemplaza toma válida |
| P1 E02 | Panel contextual evita prometer controles que backend no admite; biblioteca conserva agrupación de tomas y revisión explícita |
| B01/B04/B06 | Runtime MLX/Windows, licencias de modelos y calidad real quedan condicionados; aprovechar método sin instalar Phosphene |

Evaluación concluida. No se adoptan modelos/UI/otro motor ni se certifica operación
Windows, calidad o funciones Pro. Configuraciones y ComfyUI conservados.
