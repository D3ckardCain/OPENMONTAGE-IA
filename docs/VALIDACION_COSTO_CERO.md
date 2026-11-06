# Validación local del modo de costo cero

## Resultado verificable

Comprobación enfocada del fork: **213 tests aprobados, 1 omitido y 14 subtests
aprobados**, en 8.30 segundos en el entorno de desarrollo. El omitido corresponde
al grupo de UI que requiere Playwright, no instalado. No es una medición de
generación de IA ni de rendimiento de la PC del propietario.

Incluye biblioteca/núcleo, endpoints y estado del panel Backlot, bloqueo de
proveedores de pago, preflights, metadata, flujo Wan local contra servidor HTTP
emulado, caché y regresiones con clips sintéticos FFmpeg. No usa modelos de IA,
GPU ni servicios comerciales.

Comando reproducible con las dependencias de desarrollo y FFmpeg instalados:

```bash
make test-zero-cost
```

El Makefile enumera los directorios y archivos exactos. El resultado no se
presenta como aprobación de `make test` ni de todos los contratos upstream.

## Correcciones comprobadas

- Las sobreescrituras de `get_info()` y `dry_run()` de proveedores bloqueados
  pasan por la política; no pueden iniciar sus propios sondeos remotos.
- Los costos locales positivos/no verificables no ofrecen ejecución en preflight.
  Un fallo al estimar no derriba ese preflight.
- Un backend de runtime desconocido puede inspeccionarse y queda bloqueado.
- El guard de pruebas se instala antes de la recolección, no solo en fixtures.
- Se rechazan conexiones y resoluciones DNS externas, incluso hacia dominios
  de ejemplo como `comfy.test` si una simulación quedó incompleta.
- Node, npm, npx, gestores equivalentes, clientes de descarga y shells no se
  lanzan realmente desde la suite automatizada. Sus pruebas deben simular el
  transporte. FFmpeg y helpers Python locales siguen disponibles.
- El antiguo opt-in `OPENMONTAGE_ALLOW_NETWORK=1` no habilita llamadas reales en
  esta suite. Las pruebas `live_api` permanecen omitidas.

## Suite heredada: todavía pendiente

Se intentó ejecutar la suite completa. La revisión automática bloqueó dos
ejecuciones por intentos de telemetría hacia PostHog y de acceso a `comfy.test`.
No se afirma qué contenido tenía ese tráfico ni que se transfirieran datos.
Después se añadieron y probaron las barreras anteriores; la validación enfocada
sí terminó sin permitir esas rutas.

Los scripts `tests/qa/test_*.py` ejecutaban renders y programas externos durante
su importación. Se conservan, pero quedan fuera de la recolección automatizada;
no se ejecutaron completos ni se consideran aprobados. Su ejecución manual
requiere revisar sus efectos y dependencias por separado.

También quedan expectativas upstream incompatibles con el fork. Por ejemplo,
`tests/tools/test_3d_asset_generation.py::test_atlas_cost_matrix_and_missing_key`
espera pedir una clave comercial; ahora recibe `ZERO_COST_POLICY`. Una pasada
de diagnóstico con parada en el primer fallo obtuvo 115 aprobados, 1 omitido y
ese fallo. No se han omitido automáticamente esos contratos ni se ha desactivado
la política para conseguir una suite verde. Requieren adaptación explícita.

La pasada amplia de pruebas locales fue interrumpida antes de finalizar; no
existe un resultado completo aprobado de esa pasada. El PR sigue en borrador.

## Límites

El guard pertenece al proceso Python de pytest. No es un aislamiento del sistema
operativo ni garantiza el comportamiento de procesos descendientes arbitrarios
o de código que reemplace las funciones interceptadas. No debe usarse como
autorización para ejecutar pruebas con credenciales comerciales.

Pendiente por separado: finalizar descarga y medir inferencia real en la PC
Windows confirmada (i7-12650H, 16 GB RAM, RTX 4060 Laptop 8188 MiB), utilizando el
flujo local previsto. La calidad y velocidad comerciales siguen sin demostrar.
