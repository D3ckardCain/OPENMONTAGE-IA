# Social Media Research Skills — evaluación #80

24-11-2026, #3. [Repositorio oficial](https://github.com/ScrapeCreators/social-media-research-skills/tree/64ba7b4dea71e130d2712ffb6c1c1024b3b7c4b2). README, LICENSE y textos de outlier-post-finder/comment-mining leídos como datos, no instrucciones instaladas. Esos dos módulos declaran1.0.0; commit fija el conjunto, no una aplicación versionada.

MIT permite reutilizar código/textos con avisos; no licencia las publicaciones, comentarios, marcas o datos externos. No modelos incluidos ni requisitos GPU propios. Windows: documentos utilizables con herramientas actuales; los comandos Bash/export/npx del setup no son una instalación Windows probada. No se ejecutan ni cambian skills globales. RAM/disco para análisis dependen del tamaño de muestra y LLM, sin mínimo medido publicado para nuestro escenario.

Upstream exige SCRAPECREATORS_API_KEY para su capa de datos. [Sitio oficial consultado](https://scrapecreators.com/) ofrece100 créditos iniciales, bonificaciones condicionadas y resultados cacheados gratuitos; consultas sin caché consumen créditos. Esto no garantiza datos frescos indefinidos a costo$0 ni operación offline. No crear cuentas, reclamar bonificaciones o llamar API. Métodos sobre snapshots propios CSV/JSON sí pueden evaluarse offline con Ollama ya preparado; inferencia no se ejecuta aquí.

## Existente y decisión

#50/#65 y E08 ya cubren baseline por plataforma/cuenta/formato, mediana, muestra, fecha, métricas ausentes, comentarios y procedencia. No otro scraper, dashboard ni tarea de outliers duplicada. La mejora concreta es explicitar **evidencia por tema y denominador de comentarios**, preservando contexto/hilos y citas originales, y fijar bandas de lift como parámetros versionados, no verdad causal.

| Destino | Aceptación futura de datos/mocks |
|---|---|
| E08 | Snapshot con origen/fecha/ventana/filtros/paginación/coverage; métricas crudas separadas del score. Mediana0, n<10, mezclas de formatos, duplicados y posts de edades distintas producen advertencia/desconocido, no Infinity ni ranking global mezclado. |
| E08 | Tema→IDs de comentarios/citas/contexto y n observado; frecuencia sobre muestra explícita, spam/duplicados separados, comentario aislado no representa mercado. Español conserva negación, ironía y texto citado; no inferir demografía/ingresos/causalidad. |
| B07 | Datos frescos condicionados a derechos, términos y fuente elegible; caché con fecha no presentada como presente. Ningún fallo local dispara ScrapeCreators ni otro servicio. |

No adopción del proveedor. Solo ampliar E08 existente; no nuevo módulo editorial/descargador. Veracidad, cobertura poblacional y calidad real no acreditadas por ejemplos upstream. Evaluación completada sin instalaciones, contenido, modelos ni cambios de configuración.
