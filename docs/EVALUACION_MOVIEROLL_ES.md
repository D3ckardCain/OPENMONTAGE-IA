# MovieRoll — evaluación #88

24-11-2026, #3. [Tencent-Hunyuan/MovieRoll fijado](https://github.com/Tencent-Hunyuan/MovieRoll/tree/0b5f73e2d7cad86826dcf8fc420991d789d88646). README, LICENSE completo con Exhibit A y requirements raíz/movieroll revisados. Base/Distilled son variantes, no números de versión semántica; commit fija el código. No se aceptó acceso gated ni se descargaron pesos.

## Bloqueo de licencia

**Tencent Hunyuan Community**, no MIT/Apache. Territorio excluye **UE, Reino Unido y Corea del Sur**. Sección5(c) abarca uso/reproducción/modificación/distribución/exhibición de Works, **Outputs y resultados fuera del territorio**. Ejecutar en México no habilita automáticamente publicación internacional.6(d) dice que Tencent no reclama derechos en outputs, pero no elimina5(c).

Distribución exige licencia/avisos de cambios/NOTICE y divulgación del proveedor real sin atribuir respaldo de Tencent. Política de uso incorporada; no entrenar otros modelos con works/outputs fuera de excepciones previstas. Comercial: umbral de **100 millones MAU** en condiciones de sección4 exige autorización aparte; estar bajo ese umbral tampoco elimina territorio/avisos/recursos. No comprar licencia ni asumir derechos globales. **Adopción y distribución internacional bloqueadas** hasta resolver alcance aplicable.

Checkpoint MovieRoll, VAE HunyuanVideo1.5, Qwen2.5-VL7B, ByT5-small y Glyph-SDXL-v2 requieren licencias/huellas/tamaños separados. No se verificó cierre completo de esos recursos ni se dedujo licencia uniforme de LICENSE raíz. Fuentes oficiales enlazadas por README; inventario de pesos pendiente, sin descargarlos.

## Bloqueo técnico y Windows

Native README: Python3.12, PyTorch CUDA (requirements>=2.6), BF16, FlashAttention2 y3; **FA3 Hopper/sm90**, no RTX4060Laptop8GB. Ejemplo de pipeline completo en una GPU96GB es capacidad observada declarada, no mínimo universal inferido. **Sin CPU offload en entry point nativo**, soporte4090/5090 figura TODO: no viable acreditado aquí ni en una4080. Windows, kernels, RAM/disco y español sin validar. SGLang/vLLM-Omni son rutas separadas con requisitos/licencias/compatibilidad propios, no atajos probados ni motivo para tocar ComfyUI.

Base:480p/50pasos/AnnealCFG; Distilled T2V/I2V:480×864 o inverso/5pasos. Cinco pasos no demuestra velocidad/calidad/continuidad local. Streaming playback figura TODO, no implementado por llamarse streaming el modelo. Descargas gated, VAE y encoders son red de aprovisionamiento; inferencia solo sería offline con todos preparados. No API pagada necesaria en teoría, pero hardware/licencia actuales impiden declarar operación útil$0 aquí.

## Comparación y aceptación futura

WAN/LTX/director ya inventariados se conservan. Ventanas, caché KV jerárquica/recomputación y eventos aportan referencias para **E05/E06/E11**, no otro motor ni cache de tensores portable garantizada.

| Grupo | Criterio con texto/datos/mocks |
|---|---|
| E06/E11 | Eventos con actor/acción/tiempos/orden/contexto y revisión; ventanas enlazan estado previo y dependencias. Solape, evento ausente, cambio de actor y reloj incorrecto son errores; no afirmar continuidad visual por pasar esquema. |
| E05 | Recibo por segmento y contexto/modelo/parámetros/hash; cambio de contexto invalida posteriores afectados. Mock de crash/cancelación conserva segmentos válidos, checkpoint incompatible no reutiliza caché. No repetir herramientas completadas ni prometer persistencia KV upstream no probada. |
| E01/B01/B06 | Perfil de hardware/kernels/variante y licencia territorial/output explícitos; GPU incompatible o permiso incierto bloquea antes de inferencia. Calidad/streaming/rendimiento reales pendientes. |

Se amplían grupos existentes; no instalar MovieRoll ni nuevos runtimes. Evaluación terminada con bloqueos de adopción documentados, sin modelos/contenido/configuraciones modificadas.
