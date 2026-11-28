# Hypit — evaluación #89

24-11-2026, #3. [Repositorio oficial](https://github.com/hypit-ai/hypit/tree/a53ce54f24ed3b96e87906ac56e5261028b95b71), package **0.3.4**. README, LICENSE, package.json, docs/quickstart y manifiestos runtime-local/browser-capture revisados; no adoptar instrucciones/skills ni ejecutar ejemplos.

## Uso interno y distribución: condiciones distintas

**Licencia personalizada basada en Apache2, no Apache estándar.** Permite uso propio de la organización, incluso comercial, trabajo para clientes y despliegue single-tenant operado por/para una organización. No equivale a incorporar/distribuir Hypit con OpenMontage libremente.

Sin autorización escrita del productor restringe ofrecer funcionalidad a terceros como hosted/managed/SaaS y operar multi-tenant. Define tenant como workspace: dos o más partes externas con workspaces separados constituyen multi-tenant **aunque sea gratuito**. También restringe suministrar Hypit/derivados por beneficio comercial, incluidos componentes integrados en productos. Publicar forks está permitido bajo la misma licencia sin suministro para beneficio comercial: no toda publicación de fuente está prohibida.

No retirar/modificar nombre/logo/copyright en CLI, run reports/manifests o superficies derivadas expuestas al usuario; excepción cuando no se muestran esos componentes. Outputs propios sin condiciones añadidas por Hypit según cláusula3, pero recursos/modelos/proveedores mantienen términos y derechos independientes. No confundir ese permiso con redistribución del software. **Adopción distribuida/SaaS condicionada y no autorizada por esta evaluación; no comprar licencia.**

## Windows, offline y costo

Node>=22.15, pnpm10.33 anunciado, paquetes propios runtime/media y Chromium/codecs/FFmpeg/fuentes deben inventariarse por revisión. Usar Node ya localizado no acredita navegador/renderers preparados ni compatibilidad Windows del conjunto. No se probó build. Concurrencia64Chromium de demos no es presupuesto para16GBRAM/8GBVRAM: memoria, disco temporal y procesos deben acotarse y medirse antes. No extrapolar esos demos.

Composición gráfica/captions puede ser local sin modelos generativos según README, si navegador/codecs/assets/fuentes y tiempos están preparados. Links externos, aprovisionamiento y proveedores necesitan red. Demos declaran cargos y HypiHub/servicios propios; excluidos por costo$0. “Framework gratis” no hace gratuito al Coding Agent ni todos los proveedores; conexión a Ollama/motores existentes es diseño, no prueba realizada. No cambiar CODEX_HOME, skills/MCP/globales ni instalar paquetes.

## Comparación y carencias útiles

Director, edit_decisions, E04 palabras, E05 recibos/invalidación, E06 escena neutral y E11 eventos ya cubren el alcance; WhisperX#72/Cinematic#76/Raea#71 aportan precedentes. No otro director/renderer/ASR/cola/UI. Animations descartado no se reintroduce.

| Grupo | Aceptación futura con datos/mocks |
|---|---|
| E04/E11 | Anclaje por palabra lleva ocurrencia/span, hash transcript, tiempo y origen medido/estimado/desconocido. Palabra ausente/repetida o sin tiempo no se resuelve por coincidencia arbitraria. Cambiar idioma/voz retima candidatos, no conserva tiempos viejos como medidos. |
| E05/E06 | Dependencias de componente→recurso→versión/recibo, diff de variante; cambio de host/guion/voz invalida solo dependientes. Fallo en variante2 no destruye1; sin copiar aprobación ni cache de ejemplo. |
| E01/E10 | Scope de archivos/efectos y procesos/navegadores propios; provider local vs remoto explícito. Mock paquete ausente produce diagnóstico, no npm/uv/download ni proveedor pagado implícito. |
| B04/B06 | Elegibilidad de distribución, avisos, runtime Windows y recursos offline/QA pendientes. Contratos neutrales pueden avanzar sin integrar Hypit. |

No aporte que requiera nuevo ID del backlog. Evaluación completa; sin instalaciones/modelos/render/inferencia/contenido ni cambios de configuración.
