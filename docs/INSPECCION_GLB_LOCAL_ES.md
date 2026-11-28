# Inspección GLB sin cargar Blender

Mejora pequeña #117/#143: `blender_world(operation=inspect_glb, asset_path=...)`
lee solo cabecera y JSON de un GLB2 local hasta64MB; JSON hasta4MB. Omite el
payload BIN, no arranca Blender, no descarga texturas ni importa geometría.

Verifica longitud/chunks/alineación, JSON, TRS o matriz column-major, números
finitos, índices de hijos/ciclos y factores PBR declarados. Reporta escalas no
uniformes/negativas, materiales, extensiones y recursos externos sin leerlos.
SHA del JSON, no del archivo completo; no son bounds mundiales, verificación
de malla, calidad PBR ni prueba de escala real del objeto.

Fuente normativa [glTF Khronos fijado](https://github.com/KhronosGroup/glTF/tree/da88a3bbbe168cc728eddf71fa5e1915cc2c0629):
convención metros y Y arriba, sin conversión aplicada.9 pruebas nuevas con
contenedores sintéticos, sin crear un recurso3D de producción ni ejecutar el
piloto. No GLB propio encontrado en projects/assets/local_library revisados;
no se afirma ausencia en todos los discos. Importación real, escala/ejes/PBR
visuales y edición/reapertura en Blender siguen pendientes de ese recurso.
Blender4.5 continúa predeterminado;5.3 y complementos conservados.
