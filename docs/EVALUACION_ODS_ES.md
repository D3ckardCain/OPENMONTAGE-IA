# ODS V3: evaluación #66

24-11-2026 UTC. `Osmantic/ODS@58b547240edc5364e99457f352769162c8c98d64` main
fijado para lectura, producto3.0.0 prerelease. Tag publicado v3.0.0 es otro snapshot;
no desplegarlo por coincidir número. Sin instaladores, contenedores ni servicios.

## Decisión y existente

ODS integra stack completo de modelos/Portal/servicios; no sustituir ni reinstalar
Ollama, ComfyUI o OPENMONTAGE. Ya hay diagnósticos, catálogo/configuración de apps,
comparación de updates, SHA256 de candidatos, descarga reanudable separada y muestreo
RAM/VRAM (`application_updates.py`, `update_downloads.py`, `resource_sampling.py`).
Su valor potencial es ownership de servicios y recuperación modular; agrupar E01
diagnóstico y E05 lifecycle, no otro dashboard ni descarga automática por hardware.

## Fuentes y estado de seguridad

[README](https://github.com/Osmantic/ODS/blob/58b547240edc5364e99457f352769162c8c98d64/README.md)
advierte instaladores sobre main móvil sin release firmado calificado. `ods update`
refresca imágenes, no necesariamente código instalado: separar ambas identidades.
[Release notes](https://github.com/Osmantic/ODS/blob/58b547240edc5364e99457f352769162c8c98d64/ods/docs/RELEASE_NOTES_3.0.0.md)
fija tagv3.0.0 en bec0c42e7c9885a5aecd419a166a6a81e0d37236 y advierte
[GHSA-vqpg-pvjj-4cmq](https://github.com/Osmantic/ODS/security/advisories/GHSA-vqpg-pvjj-4cmq),
con corrección84f4a8a10 posterior en main y relación con GHSA-v3hj-52g2-2hmc.
No certificar este HEAD como auditado/libre de vulnerabilidades por leer notas o
tener CI. La consulta API de advisories no está admitida por el conector; se consultó
también la página oficial web. No se ejecutó exploit ni se cambió configuración.

[Security guide](https://github.com/Osmantic/ODS/blob/58b547240edc5364e99457f352769162c8c98d64/ods/SECURITY.md)
distingue localhost, host-agent/clave y trust zone de contenedores. Docker access
puede controlar host; proceso externo no debe pasar a administrado por detectar puerto.
Defaults11434/3000/3001 pueden colisionar; no parar ni reclamar nuestros servicios.

## Licencias y requisitos

[LICENSE Apache2](https://github.com/Osmantic/ODS/blob/58b547240edc5364e99457f352769162c8c98d64/LICENSE),
[LICENSING](https://github.com/Osmantic/ODS/blob/58b547240edc5364e99457f352769162c8c98d64/ods/LICENSING.md),
[Pixel license](https://github.com/Osmantic/ODS/blob/58b547240edc5364e99457f352769162c8c98d64/ods/vendor/pixel/LICENSE.md):
Pixel permite uso incluso comercial dentro de ODS, no extraerlo a OPENMONTAGE.
Avisos históricos no son licencia operativa. Terceros/pesos/imágenes no se relicencian;
[revisión upstream](https://github.com/Osmantic/ODS/blob/58b547240edc5364e99457f352769162c8c98d64/ods/docs/THIRD-PARTY-LICENSING.md)
identifica restricciones OpenWebUI/n8n y pesos AudioCraft/XTTS, además de gaps.
No importar recipes que aceptan términos automáticamente ni copiar Pixel/UI.

Windows propone WSL2/Ubuntu24.04/Docker Desktop, virtualización, driver NVIDIA570+
y reinicio; no preparación inocua. [Docker Desktop](https://docs.docker.com/subscription/desktop-license/)
tiene elegibilidad gratuita por escenario, no gratis universal para organizaciones.
Runtime/imagen/modelo, espacio y concurrencia deben cerrarse antes de instalación;
no tratar selección automática de modelo como prueba de memoria suficiente.

## $0, local y offline

ODS dice sin telemetría propia, pero default consulta GitHub, descarga modelos/imágenes
y puede buscar web; cloud/hybrid son opcionales, excluidos. Operación offline requiere
artefactos presentes, descubrimiento/updates/búsqueda desactivados y egreso probado,
no un dashboard accesible. No descargar otro stack para obtener funciones ya presentes.
Ninguna instalación o aceptación de términos realizada.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Ownership/doctor E01 | Reportar servicio externo vs propio, executable/puerto/instancia/revisión; fixtures de puerto ocupado y acceso fallido no modifican ni detienen procesos |
| P1 | Recuperación E05 | Estado/code revision/image digest separados; backup/restore y rollback planificados con mocks, sin sobreescribir settings/instalaciones |
| P1 | Updates verificables E01 | Mantener candidatos separados; fuente/commit/hash/avisos y requisitos antes de activar; no elevar latest o dashboard vivo a certificado |
| P3 | Adopción de componente aislado | Seleccionar solo código Apache elegible, preservar avisos y excluir Pixel/recipes no revisadas; beneficio frente a existente medido |

Bloqueos: prerelease sin calificación firmada, cambios del sistema, licencias mixtas
y cierre de recursos. No impiden contratos propios de diagnóstico/ownership.
Configuraciones, servicios y Python ComfyUI conservados; sin contenido generado.
