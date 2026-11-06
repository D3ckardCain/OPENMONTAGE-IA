# Validación local del modo de costo cero

## Resultado verificable

Comprobación ampliada del fork: **614 tests aprobados, 1 omitido y 14 subtests
aprobados**, en 12.38 segundos en el entorno de desarrollo. El omitido corresponde
al grupo de UI que requiere Playwright, no instalado. No es una medición de
generación de IA ni de rendimiento de la PC del propietario.

Incluye biblioteca/núcleo, endpoints y estado del panel Backlot, bloqueo de
proveedores de pago, preflights, metadata, flujo Wan local contra servidor HTTP
emulado, caché y regresiones con clips sintéticos FFmpeg. No usa modelos de IA,
GPU ni servicios comerciales.

La ampliación incluye 248 contratos de las fases 0–3 y nueve comprobaciones de
recursos 3D/Blender. Además comprueba 95 adaptadores reales deshabilitados del
catálogo: estado, metadata, simulación y ejecución quedan bloqueados antes de
alcanzar el estimador de precios, la caché o el transporte HTTP, incluso con
credenciales ficticias configuradas. No certifica el funcionamiento de sus APIs.

Comando reproducible con las dependencias de desarrollo y FFmpeg instalados:

```bash
make test-zero-cost
```

El Makefile enumera los directorios y archivos exactos. El resultado no se
presenta como aprobación de `make test` ni de todos los contratos upstream.

## Correcciones comprobadas

- Los selectores excluyen adaptadores bloqueados antes de sondear sus operaciones
  o puntuarlos, y no los anuncian como alternativas.
- El selector video conecta con Wan T2V/I2V, adapta duración/proporción y conserva
  la semilla cero. Los controles de selección no llegan a contratos estrictos.
- Una operación de movimiento sin proveedor compatible se bloquea. Ni el selector
  ni el registro proponen imágenes estáticas como alternativa automática al video.
- Las referencias locales no se suben automáticamente a fal.ai. El proveedor local
  fallido no provoca un reintento comercial ni un cambio silencioso de proveedor.
- Véanse el alcance y las conversiones exactas en [Selección local](SELECCION_LOCAL.md).

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

Se corrigió el primer grupo de expectativas incompatibles:

- La configuración se comprueba como presupuesto USD 0, modo `cap` y umbral 0.
- Atlas/Fal 3D deben devolver `ZERO_COST_POLICY` sin GLB ni archivo de procedencia;
  añadir claves ficticias no habilita el transporte. Las pruebas de Blender y
  los contratos de recursos se conservan.
- En la fase 3, las expectativas de ejecución comercial de Google Music/Veo se
  sustituyeron por casos que exigen bloqueo antes del SDK y la preparación de
  imágenes, incluyendo duraciones extremas, referencias ausentes y alternativas
  de backend. No se certifican las antiguas coerciones/extracciones de sus APIs.
- Las pruebas puras de identidad, capacidades, registro, estilos y manifiestos
  siguen activas. No se desactiva la política ni se omiten estos contratos para
  presentar la ampliación como aprobada.

Otros módulos heredados todavía esperan rutas comerciales y necesitan revisión
explícita. No se ha vuelto a ejecutar ni aprobado la totalidad de `make test`.

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
