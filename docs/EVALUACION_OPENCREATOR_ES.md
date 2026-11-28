# OpenCreator — evaluación #79

24-11-2026; seguimiento #3. [Fuente oficial fijada](https://github.com/krillinai/OpenCreator/tree/55a9db9c0643ab18717e0f2259b03c32867d33c1), antes KrillinAI. Lectura de README, LICENSE, package.json raíz/desktop/daemon y `apps/daemon/src/creator/yt-dlp/update-manager.ts`; sin ejecutar instrucciones, skills o binarios.

## Versión, licencia y requisitos

Desktop declara **3.3.4**, daemon **0.1.0**: no son una versión binaria local acreditada. Código Apache-2.0 con conservación de avisos/modificaciones; componentes no heredan una licencia uniforme. Iconos model-brands llevan MIT LobeHub; modelos, plantillas de terceros, fuentes y servicios requieren revisión individual. Remotion del daemon fija4.0.473: su elegibilidad comercial es independiente (B02), no Apache por inclusión.

Windows dispone de host Electron43.8.1 con daemon/Web compartidos; source usa pnpm9.15.0, TypeScript, dependencias nativas better-sqlite3/sharp y compilación del runtime KrillinAI. Codecs, FFmpeg, yt-dlp, fuentes y Codex CLI forman parte del inventario efectivo. No se establece aquí un mínimo medido de RAM/VRAM/disco: depende del renderer y servicios/modelos seleccionados, no de instalar Electron. No se probó compilación Windows.

README exige Node22+ para desarrollo; el instalador Windows x64 incluye runtime/Codex y no exige Node/pnpm al usuario. Son escenarios distintos, ninguno ejecutado aquí.

## Offline y costo

Guardar archivos/configuración localmente y usar Codex CLI no hace gratuita ni offline la inferencia. Login/clave, catálogo de proveedores y servicios de imagen/vídeo/voz tienen términos/cargos propios. Reutilizar conceptualmente el puente Ollama de OpenMontage, sin afirmar compatibilidad de OpenCreator ya comprobada. Edición SRT con recursos preparados puede ser local; búsqueda, descarga de vídeos, comprobación de actualizaciones y proveedores remotos requieren red.123 lenguas fuente/124 destinos son catálogo, no calidad española verificada.

El runtime puede reutilizar CODEX_HOME, skills y MCP activos. No adoptarlo ni tocar configuración global. En esta evaluación costo$0 por lectura pública; no se promete ejecución completa$0 de la aplicación upstream.

## Comparación y carencias

Studio ya tiene jobs/recibos, cancelación/reanudación, subtítulos y actualización con candidatos/revisión/hash (`lib/update_downloads.py`, `lib/update_center.py`, `lib/application_updates.py`). No duplicar runtime, agente o interfaz. El candidato distingue yt-dlp bundled/active/latest y conserva versión funcional ante fallo; el aporte útil es cerrar el contrato común de **activación reversible de componentes preparados**, no otro downloader ni autoactualización.

Revisiones independientes de outputs/settings y edición de cues amplían E04/E05/E06: conservar original, versión base y recibos válidos; no convertir un cambio de estilo en nueva transcripción.

| Destino | Aceptación futura con datos/mocks |
|---|---|
| E01/E05 | Bundled/active/candidate/revisión/hash separados; candidato corrupto, versión incompatible, bloqueo de archivo Windows o interrupción al activar conserva versión anterior. Smoke mock falla → rollback explícito; ningún update de ComfyUI/global ni red implícita. Reutilizar update_center. |
| E04/E06 | Split/merge de cues conserva spans, idioma, tiempos y fuente; rechaza orden/rango inválido/base obsoleta. Guardar revisión nueva y diff sin sobrescribir versiones anteriores. Cambio de estilo invalida solo derivados pertinentes. |
| E05 | API/panel/agente observan el mismo ID/revisión/estado, error parcial explícito; no repetir etapas con recibo compatible. |

No adopción completa. Windows, recursos, licencias de terceros, precisión española y rendimiento reales siguen condicionados; esta evaluación no los valida. Sin instalaciones, modelos, inferencia, contenido ni cambios de configuración.
