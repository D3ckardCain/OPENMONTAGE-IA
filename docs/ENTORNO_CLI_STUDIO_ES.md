# Herramientas CLI guardadas en Studio

Node.js se registra como aplicación `managed_cli`, con el ejecutable `node.exe`
o `node`. El registro conserva los ajustes de las otras aplicaciones. No acepta
instaladores ni abre una consola independiente desde Aplicaciones.

Al iniciar `python -m backlot serve`, el servidor construye su PATH de proceso
con las carpetas de FFmpeg/FFprobe guardadas y una distribución Node.js completa
registrada en `applications.json`. Node debe tener npm y npx junto al ejecutable.
Una ruta ausente, por ejemplo un disco desconectado, se omite para no impedir que
abra Studio. No cambia PATH de Windows, el entorno del terminal que lo inició,
el registro del sistema o los Python de otros programas. Reinicia únicamente
Studio, con la cola sin trabajos, después de cambiar esas rutas para aplicarlas
a las herramientas que consultan PATH directamente.

La preparación comprobó Node.js portable v22.23.5 Windows x64, npm/npx 10.9.9.
El ZIP original se conserva y su SHA256
`4a191082e9706866830379d577d2cc8a50c776fcd9436a8d061b063ed0d9a0e3`
coincide con el [manifiesto oficial](https://nodejs.org/dist/v22.23.5/SHASUMS256.txt).
Se conservó el Node embebido en MSYS de OpenModelica, que no era un runtime
registrado en Studio. La distribución dedicada no lo reemplaza.

La API de aplicaciones confirma Node.js configurado y el ejecutable localizado.
La inspección del panel mediante Chrome con depuración remota fue rechazada por
la revisión automática de comandos con «blocked by policy». No se presenta esa
inspección visual como realizada por Codex. Posteriormente el usuario confirmó
«Node.js · Ejecutable localizado» en el panel y cerró #26. Esa confirmación
resuelve el pendiente visual; no se repite la instalación ni la comprobación.

Las pruebas verifican conservación, PATH del proceso sin mutación del entorno
original, deduplicación, discos ausentes, runtime parcial, rechazo de instaladores
y consolas y aplicación del entorno antes del arranque del servidor. Los cinco
fallos iniciales de contratos por ffprobe/npx ausentes desaparecieron al exponer
esas rutas al proceso de QA: los 53 contratos implicados pasaron.

Node/npm disponibles no demuestran que Remotion, HyperFrames, sus paquetes o un
navegador estén instalados o que un render funcione. No se instalaron paquetes de
composición ni se renderizó contenido como parte de esta preparación.

## Ejecución automática de pruebas

Las herramientas pytest se instalaron en `.runtime/qa/venv`, conservando `.venv`.
Los tests usan los paquetes de Studio mediante PYTHONPATH y los ejecutables por
PATH del proceso. La protección existente de tests/conftest.py bloquea sockets
externos de Python y omite pruebas live_api. Para npm se usa
`npm_config_offline=true` y `npm_config_ignore_scripts=true` en el proceso de QA.

Los scripts manuales tests/qa/test_01–test_08 realizan trabajo al importarse:
pueden escribir medios y el caso end-to-end limpia resultados de QA anteriores.
Ahora se omiten de la recolección automática salvo `OPENMONTAGE_MANUAL_QA=1`.
Su ejecución directa con Python se conserva. HyperFrames test_09 mantiene su
propio opt-in. Así la suite automática no inicia esos flujos por recolectar tests.
