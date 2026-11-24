# Local Deep Research — evaluación #81

24-11-2026; #3. [Código main fijado](https://github.com/LearningCircuit/local-deep-research/tree/7490efa217a16685c78880169f3e8e63a14b78cc). README, LICENSE, pyproject, versión y release oficial revisados. [Estable v2.0.4](https://github.com/LearningCircuit/local-deep-research/releases/tag/v2.0.4), tag resuelto a `8669e980f5f7565bcd96907d3184505506239178`; no confundir tag estable con main ni imagen Docker sin digest.

MIT del código permite reutilización con avisos; datasets, motores de búsqueda, modelos y dependencias mantienen términos propios. No se adoptan corpus/embeddings por la licencia de la aplicación.

## Windows y recursos

Main requiere **Python >=3.12,<3.15**: .venv3.11 de Studio no es destino compatible y se conserva. README ofrece Windows nativo con SQLCipher en wheels; exportación PDF requiere Pango. CPU x86-64 con AVX según documentación; wheels/dependencias concretas deben comprobarse en entorno aislado. Docker/WSL2 es ruta alternativa, no requisito de Studio ni prueba de compatibilidad; host networking Docker Desktop4.34+ exige configuración aparte. No desplegar.

RAM/VRAM/disco dependen de LLM, tamaño de documentos, índice y concurrencia; no hay garantía para laptop8GB/16GB. Resultados Qwen3.6-27B/RTX3090 y benchmarks con buscador cloud no prueban desempeño español local ni memoria suficiente. No descargar modelos para reproducirlos.

## Offline, costo y límites

Ollama/OpenAI-compatible puede usar un modelo realmente local preparado, pero un endpoint loopback también puede reenviar a cloud. SearXNG local consulta buscadores de Internet: búsqueda fresca no es offline. Biblioteca/documentos locales y recursos preparados son el escenario sin red; modos Private only/Strict son guardas con límites documentados, no aislamiento absoluto. Navegador JS opcional/descargas/embeddings necesitan inventario y control de egreso. API comercial y Docker Desktop elegibilidad no se presuponen gratuitos; no son necesarios para nuestros contratos.

[Advisories oficiales](https://github.com/LearningCircuit/local-deep-research/security/advisories) incluyen bypass de autenticación crítico GHSA-fjvm-966v-hmm2 y fallos de SSRF/sesiones. La API del conector no admitió ese endpoint; se contrastó la página oficial. La release2.0.4 incluye endurecimiento de destino de credenciales, límites de subida y redirecciones. Esto no equivale a auditoría de seguridad completa ni a ausencia de vulnerabilidades. Antes de desplegar: verificar rangos corregidos de todos los avisos contra versión elegida; nunca habilitar fallback SQLite sin autenticación efectiva para servicio compartido.

## Existente y decisión

OpenMontage ya conecta Feedparser/Trafilatura en `lib/document_reading.py`/worker aislado, research y Ollama/director. No segundo agente, biblioteca vectorial o UI por defecto. E08/E05/E10 pueden incorporar **dossier con trazabilidad afirmación→pasaje** y presupuesto de investigación, sin ejecutar LDR.

| Grupo | Aceptación futura con documentos textuales/mocks |
|---|---|
| E08 | Cada afirmación lleva fuente/hash/fecha y pasaje/offset; cita inexistente, truncada o que no respalda afirmación produce unsupported, no cita inventada. Diferenciar contradicción, fuente obsoleta y sin evidencia. Español preserva negaciones/cifras. |
| E08/E05 | Presupuesto de consultas/pasos/tiempo y bytes, parada/reanudación con snapshot de fuentes; fallo parcial no repite extracción válida ni declara dossier completo. Caché fechada y fuentes descartadas conservadas. |
| E10 | Mocks de documento que intenta ordenar nuevas llamadas, URL/redirección fuera de scope y endpoint relay; no ejecutar instrucciones de la fuente ni ampliar red por fallo. Contrato local de lectura existente, sin servidor nuevo. |
| B03/B07 | Runtime Python3.12 y posibles dependencias de índice/red son bloqueos de adopción; modelos y fuentes con licencias propias. No modificar Studio/ComfyUI para resolverlos. |

Evaluación terminada; operación Windows/offline, citas correctas y calidad/rendimiento reales no probados. Sin instalaciones, modelos, inferencia, contenido ni configuración modificada.
