# #108 — diagnóstico de rutas multimedia, E01

Durante #107 un disco no conectado produjo el mensaje genérico «Configura la
ruta», aunque la ruta guardada debía conservarse. Se completa solo esa diferencia
en `reference_analysis.executable`, reutilizado por `require_media` y Studio.

Se mantiene la ruta configurada como autoridad: nunca se sustituye por otra
instalación al fallar. No ejecutar una herramienta para comprobar su ubicación.

| Lectura observada | Diagnóstico |
|---|---|
| Archivo ausente y raíz/unidad no disponible | Reconectar unidad sin cambiar la ruta guardada |
| Raíz accesible, archivo ausente | Ruta no existente; configuración conservada |
| Acceso denegado al archivo/raíz | Permiso denegado no demuestra ausencia |
| Error E/S del archivo/raíz | Error conservado, no atribuir corrupción ni reparar |
| Directorio en lugar de archivo | No es archivo ejecutable |
| Ninguna ruta disponible/configurada | Mensaje de configuración anterior |

No se prueba salud del disco, versión ni ejecutabilidad binaria por stat: se
comprueba ubicación/tipo y se explica el error disponible. No instala, descarga,
repara, reconfigura ni reinicia nada.

**7 pruebas focalizadas nuevas aprobadas**, con filesystem simulado y un archivo
temporal no ejecutado; cubren fallos distintos y ausencia de fallback con ruta
configurada. No suites anteriores ni CI completa repetidas. Activación del nuevo
texto en procesos que ya importaron el módulo queda pendiente; no afirmar que
el servidor abierto haya cargado el cambio por editar su archivo en disco.

El alcance de identidad #105 no incluye reference_analysis.py: la identidad de
Studio no certifica esta activación. Se documenta esa limitación explícitamente;
no se altera el servidor durante la validación #107.
