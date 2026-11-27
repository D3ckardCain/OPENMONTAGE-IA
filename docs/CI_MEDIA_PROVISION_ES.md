# Provisión multimedia del runner: #70

24-11-2026 UTC. Alcance: `.github/scripts/ensure-media-cli.sh`, sus pruebas
aisladas y este manual. Los workflows, lint y selecciones de pruebas se conservan.

## Causa observada

En [CI45330382977](https://github.com/D3ckardCain/OPENMONTAGE-IA/actions/runs/45330382977),
jobs138230015237 y138231809572 terminaron con exit124 en preparación del sistema:
APT descargaba desde us-east-2.ec2.archive.ubuntu.com con progreso muy lento.
El segundo intento pasó minutos descargando libcodec2/libopus/librav1e antes del
límite. pip, lint y tests quedaron skipped. El browser job138229905127 sufrió
también timeout de update. Esto acredita indisponibilidad/rendimiento insuficiente
de esa ruta en los runners observados; no prueba un fallo de FFmpeg o de la app.
Repetir jobs no resolvió la suite principal de ese HEAD.

## Cambio acotado

Si ffmpeg y ffprobe ya están en PATH no se hace trabajo APT. En caso contrario,
provisión solo para Ubuntu amd64 del runner, codename local validado. Se genera
un directorio temporal con sources.list y listas de paquetes propias: Ubuntu base,
updates y security, componentes main/universe. HTTPS a archive.ubuntu.com y
security.ubuntu.com, Signed-By con ubuntu-archive-keyring.gpg del sistema. Se excluye
sourceparts del runner y se aíslan sus índices: ni mirror EC2 ni repositorios de
terceros/cachés previos participan en esa resolución.

No se reescribe /etc/apt ni se deshabilitan firmas/TLS. No latest binario externo,
acciones adicionales, cache ejecutable sin integridad o fallback de proveedor.
--no-install-recommends reduce paquetes opcionales; todas las dependencias obligatorias
de FFmpeg se resuelven por APT. Un update parcial falla con Error-Mode=any, sin
utilizar índices obsoletos como si hubiera tenido éxito.

Se conservan90s de update,180s de install, kill-after10s, timeout HTTP/HTTPS20s,
Acquire::Retries=1 y el límite de paso6min. No bucle de reintento del script, no
aumento de deadlines. Ambas herramientas y sus comandos -version siguen siendo
obligatorios después de instalar. Errores se propagan; limpieza elimina solo el
directorio mktemp propio, usando sudo para parciales propiedad de APT.

## Validación y límites

`python -m unittest discover -s tests -p test_ci_media_setup.py -v` ejecuta los
tests también compatibles con pytest. Sustituye sudo/apt/CLIs por fixtures en PATH;
no realiza instalación ni red. Cubre skip si existen ambos, falta parcial, fuentes
oficiales/firmas/listas aisladas, límites, fallo update sin install, fallo install
sin repetirlo, herramienta ausente tras supuesto éxito, versión que falla y
codename inválido. `bash -n` comprueba sintaxis. No equivale a ejecutar APT real.

La evidencia final de APT/FFmpeg reales, lint, suite completa sin red y browser/
contratos Windows/Linux se registra por commit/run/job en #70 y PR#2. El issue
solo se cierra después de verificar esos resultados. Una caída de los archivos
oficiales sigue fallando visiblemente dentro de los mismos límites; no se promete
eliminar toda dependencia de red del aprovisionamiento.

Las fuentes usan los paquetes firmados del Ubuntu del runner. No fijan snapshot
inmutable de cada paquete ni añaden cobertura de otras arquitecturas/OS. Los tests
de aplicaciones/instalación Windows conservan su entorno y alcance. Este script no
es instalador local de Studio y no toca ComfyUI, configuraciones o candidatos.

## Actualización del job browser-regressions · 2026-11-27

Run [45999054766](https://github.com/D3ckardCain/OPENMONTAGE-IA/actions/runs/45999054766), job 140505746089: el runner identificado por el log usó Ubuntu 26.04 (resolute). La provisión aislada desde los archivos oficiales firmados comenzó la instalación de FFmpeg y descargó al menos 62 paquetes/dependencias; el proceso alcanzó libavfilter11 y terminó en exit 124 al límite interno de 180 s de instalación. El paso de Playwright fue omitido; no es un fallo de test ni una instalación incompleta declarada exitosa.

Se fijó únicamente browser-regressions a ubuntu-24.04; no se cambió la matriz Linux/Windows de contratos, el Python, la selección de paquetes, las fuentes firmadas, el límite de 180 s ni el timeout de 6 min del step. El motivo es evitar que la etiqueta móvil ubuntu-latest cambie la versión base/paquetes de FFmpeg sin relación con este job. Se añade una prueba estática para conservar el pin y verificar que el flujo sigue preparando FFmpeg antes de instalar Chromium y ejecutar Playwright.

Fuentes oficiales de imagen: [tabla de labels de GitHub Actions Runner Images](https://github.com/actions/runner-images#available-images) y [Ubuntu 24.04 image definition](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md). Este cambio es una hipótesis acotada para reducir la variabilidad de APT, no garantía de que paquetes externos nunca fallen. Se ejecutará Playwright solo si APT completa en el runner fijado.
