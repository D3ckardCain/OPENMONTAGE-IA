# HyperFrames offline: preparación y muestra real — #132

26-11-2026 UTC. [Resultados](HYPERFRAMES_132_PILOTO_20261126.json).
Actualiza el [diagnóstico anterior](HYPERFRAMES_DIAGNOSTICO_LOCAL_ES.md), sin repetir sus pruebas.

## Preparación

Se reutilizaron Node22.23.5, Chrome instalado y FFmpeg/FFprobe9.0.2. Solo faltaban
HyperFrames0.9.96 y GSAP3.14.2 en las ubicaciones y caché revisadas. Se prepararon
una vez en `.runtime/hyperframes-0.9.96`:78 paquetes, versiones exactas, scripts
desactivados, sin descargar navegador. [Lock con integridades npm](provenance/hyperframes-0.9.96-package-lock.json).
No reinstalar para repetir la muestra.

Primer intento: `UNABLE_TO_VERIFY_LEAF_SIGNATURE`, sin paquetes instalados.
Segundo: `--use-system-ca` solo en el proceso Node de preparación, usando
certificados de Windows y manteniendo TLS activo. Sin cambios npm globales.
Doctor real aprobó los requisitos obligatorios. Whisper, Kokoro, MusicGen y
Docker siguen ausentes para HyperFrames y opcionales para esta composición.

Fuentes fijadas: [CLI0.9.96](https://registry.npmjs.org/hyperframes/0.9.96),
[GSAP3.14.2](https://registry.npmjs.org/gsap/3.14.2),
[upstream revisado](https://github.com/heygen-com/hyperframes/tree/1e7d00496692d4c264ffeb59e85175752f39ea2d).
CLI Apache2.0; GSAP conserva su [licencia estándar sin cargo](https://gsap.com/standard-license/),
no MIT. Encabezado y metadata conservados. Audio: Sharvard CC BY3.0 y atribución
HiFiTTS/Cori Samuel92 CC BY4.0. Costo operativo$0.

## Uso por el agente

Pipeline `hyperframes-offline-pilot`, director `skills/qa/hyperframes-offline-pilot.md`,
herramienta registrada `hyperframes_offline_pilot`, proyecto separado
`qa132-hyperframes-offline`. Autorización completa registrada antes de assets.
Checkpoints y recibos permiten reanudar sin repetir herramientas completadas.

`scripts/run_hyperframes_offline.py` transporta una llamada del registro; no
instala ni dirige etapas. Perfil privado JSON: `node`, `browser`, `package_dir`,
`scratch`. El perfil local preparado está en
`.runtime/qa/hyperframes-offline-profile.json`; no se publica por sus rutas personales.
Los ejecutables multimedia se resuelven desde las rutas guardadas existentes.

Contrato de uso, solo con etapa `in_progress` y entradas revisadas:

```powershell
& .\.venv\Scripts\python.exe -B scripts/run_hyperframes_offline.py `
  --profile .runtime/qa/hyperframes-offline-profile.json `
  --project qa132-hyperframes-offline --stage compose `
  --tool hyperframes_offline_pilot `
  --inputs projects/qa132-hyperframes-offline/artifacts/tool-render.json
```

El render ya terminó: **no ejecutarlo otra vez**. Se rechaza sobrescribir salida,
workspace o evidencia de cancelación existente. El piloto está limitado a este
proyecto; no es un nuevo editor. Consultar los recibos para continuar.

Variables exclusivas del hijo desactivan updates, auto-install, skills,
telemetría y warm-check. Cachés/config/extracción aisladas. Preload Node bloquea
destinos externos y registra intentos; CSP permite recursos locales y fuentes
embebidas. No modifica la red de Windows ni aísla todo el egreso de Chrome.

## Validación real

HyperFrames produjo4s,640×360,24fps,96fotogramas H.264/AAC,114526bytes. SHA256:
`7002df57de36fc99ee37b6d9a0de9f9b1b69d8e0bb1ee31ba2befe6f692f8683`.
Cinco fotogramas codificados inspeccionados: texto legible y cuadrado propio
en movimiento. Recursos propios separados, sin plantilla de catálogo.

WAV español existente de3.610703s, colocado a0.25s, sin nueva síntesis ni ASR.
Decodificación completa correcta. Envolventes RMS a10ms: correlación0.9990599,
desplazamiento medido250ms, tolerancia1/24s. El marcador señala inicio del
archivo, no primer fonema; sin afirmación de lip sync. Chrome reprodujo hasta
el final96fotogramas/0descartados, sin errores, y permitió seek0.3s/2.5s.

Segunda captura cancelada tras1/96fotogramas. `taskkill /T /F` recibió solo el
PID creado por la herramienta. Raíz y13descendientes ausentes en la consulta
posterior de solo lectura. Dos Chrome aún aparecían inmediatamente después de
taskkill; desaparecieron sin kills adicionales. Sin MP4 parcial promovido;
el vídeo terminado conservó su SHA256. Código130 normalizado por el transporte,
salida nativa1 tras terminación forzada: no es cancelación limpia del CLI ni
validación de cancelación desde Studio4750.

Antes del primer render exitoso se corrigieron fallos reales de CSP para fuentes
embebidas y oclusión de texto por el fondo; evidencias fallidas conservadas.
El registro Node muestra515 conexiones loopback y5 intentos a Google Fonts
**bloqueados**: no ausencia de intentos. No se capturó egreso global del navegador.
La reproducción del MP4 solicitó solo HTML/vídeo `file:`.

Cuatro pruebas Python nuevas aprobadas; seis comprobaciones Node nuevas
(HTTP loopback real y cinco rechazos externos). Pytest se reutilizó desde QA;
`.venv` no contiene pytest y no se modificó. Sintaxis comprobada. Sin repetir
las23+5pruebas anteriores, suite completa ni CI.

## Pendientes

Escucha humana y naturalidad aplazadas. Scaffold genérico aún usa CDN/registro
mutable: solo el workspace propio con recursos congelados acredita este render
offline. Activación/importaciones y cancelación UI4750 no comprobadas. #132 sigue
abierto. No reinicios, cambios ComfyUI, originales o configuraciones. PR#2 borrador.

Vista local: `projects/qa132-hyperframes-offline/review.html`.
MP4/audio/capturas/paquetes y perfil privado no se suben a GitHub.

## Siguiente entrega: GSAP local en scaffold, adaptador0.3.1

Ya implementada y [probada de forma focalizada](HYPERFRAMES_132_GSAP_LOCAL_RESULTADOS.json):
`scaffold_workspace`/`render` aceptan `local_gsap_package_dir` o la variable
del hijo `HYPERFRAMES_GSAP_PACKAGE_DIR`. El transporte offline selecciona el
GSAP ya preparado junto al paquete HyperFrames; el perfil puede declarar
`gsap_package_dir` si su distribución local es diferente. No instala nada.

Se exigen package.json/name/versión3.14.2/licencia y JS con SHA256
`c174bfce53a729418d57a8ad8625e7247c793a22fef8e2851e3cfa3de9cd8280`.
Manifest limitado100KB y JS2MB. Fallo de recurso explícito bloquea antes de crear
workspace, sin CDN fallback. Staging común conserva JS, encabezado y metadata de
licencia por contenido, con `.openmontage-gsap.json`; repetir scaffold reutiliza
la misma copia. Se comprueban hashes también después de copiar.

Cinco pruebas nuevas: recurso/atribución/reutilización, hash incorrecto,
ausencia, versión incompatible y selección compartida desde el entorno hijo.
El GSAP preparado real y su selección por perfil se verificaron en solo lectura.
No se volvió a renderizar: no se atribuye QA audiovisual del piloto al scaffold.

Sin selección local explícita/perfil, el modo previo conserva CDN por
compatibilidad; no es offline. El registro de bloques aún apunta a main y
`add_block` sigue siendo una operación explícita separada que puede usar red.
Fuentes, medios externos y subcomposiciones requieren revisión propia. Esta
entrega elimina la dependencia CDN de GSAP cuando se selecciona local, sin
afirmar que cualquier HTML sea autónomo u offline. Activación de imports en
Studio se agrupa con próximas entregas, sin reiniciar ahora.
