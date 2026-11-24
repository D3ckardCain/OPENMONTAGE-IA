# Pascal Editor: evaluación #69

24-11-2026 UTC. `pascalorg/editor@89deb6ac627643994f052a9e3bc9ca18310d447f`,
CLI/MCP1.1.6. Lectura estática, sin npx/setup/doctor, descargar runtime o crear escena.

## Decisión y contraste

Interés concreto: escena semántica edificio/nivel/pared/abertura/habitación y puente
MCP local, no otro generador o sustituto de CAD. Blender/Archimesh y FreeCAD ya
preparados, Three.jsWorld y normalización de assets existentes. Código
`tools/graphics/blender_world.py` y `lib/freecad_runtime.py`/`freecad_units` no
equivale a IFC interoperable ni precisión constructiva certificada. E06 intercambio
neutral y E10 MCP cubren el piloto; añadir solo semántica/unidades/validación faltante.
Preservar rutas y herramientas aprobadas; no generar geometría para evaluar.

## Fuentes y requisitos

[README](https://github.com/pascalorg/editor/blob/89deb6ac627643994f052a9e3bc9ca18310d447f/README.md),
[CLI package](https://github.com/pascalorg/editor/blob/89deb6ac627643994f052a9e3bc9ca18310d447f/packages/cli/package.json),
[CLI manual](https://github.com/pascalorg/editor/blob/89deb6ac627643994f052a9e3bc9ca18310d447f/packages/cli/README.md):
Node^22.23.4 o ^24.22.1 o >=26.12.1, no simplemente Node22+. No repetir Node#26
ni actualizarlo aquí; compatibilidad específica se comprobaría en otra fase.
Editor ReactThreeFiber/WebGPU; soporte GPU/navegador efectivo y memoria no probados.
CLI guarda proyectos en SQLite, runtime web aparte. Primer npx interactivo puede
instalar globalmente, configurar y descargar: no es comprobación sin efectos.

[MCP service](https://github.com/pascalorg/editor/blob/89deb6ac627643994f052a9e3bc9ca18310d447f/packages/cli/src/mcp-service.ts)
incluido en CLI crea servicio/token local; no requiere runtime web descargado.
Un servicio comparte escena activa: un cliente agente activo, PASCAL_HOME/procesos
separados si se requiere independencia. No activar dos conectores por plugin+manual.
Token privado, identidad/version y ownership de PID no se publican ni se mezclan con
sesión alojada. MCP que puede escribir no se considera diagnóstico de solo lectura.

[IFC converter](https://github.com/pascalorg/editor/blob/89deb6ac627643994f052a9e3bc9ca18310d447f/packages/ifc-converter/README.md)
convierte bytes a nodos/IDs/stats, con WebIFC WASM local configurable. Algunos
elementos quedan imported-mesh, no paramétricos completos; ciertos pisos/habitaciones
se derivan geométricamente. Mantener IDs/propiedades/origen y errores de conversión;
no reconstrucción BIM perfecta ni ingeniería/colisiones certificadas por importación.

## Licencias, $0 y offline

[MIT](https://github.com/pascalorg/editor/blob/89deb6ac627643994f052a9e3bc9ca18310d447f/LICENSE)
de código: conservar avisos, revisar por paquete/modelos3D/fuentes/plugins/WASM.
Pascal Next es preview alojado, experiencia no incluida íntegramente en release
abierto. Medios de demo tienen CC-BY4 separado según README, no MIT ni contenido
original nuestro; no descargarlos/copiar escenas. Hosted/Architect consume créditos
y queda excluido, sin cuenta/clave/trial.

Local puede ser $0 sin hosted. Primer arranque editor descarga runtime por versión,
verificado contra digest del paquete; --runtime archive también verifica, directorio
local se instala tal cual y requiere procedencia propia. Techo140MiB de smoke
upstream no mide uso RAM/GPU. Offline exige CLI/runtime/assets/fuentes/plugins/WASM
presentes y egreso bloqueado; MCP local sin web no prueba editor completo offline.
No herramientas/servicios creados ni actualizaciones ejecutadas.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Escena arquitectónica E06 | JSON sintético con unidades/ejes/niveles/IDs/relaciones/aberturas y provenance; round-trip a contrato Blender/FreeCAD reporta pérdida, no crea geometría |
| P1 | Cliente MCP E01/E10 | Fake service con version/token/home/escena activa; cliente2 o PID ajeno rechazado, cambio de proyecto no afecta otro, lectura primero sin hosted |
| P1 | Persistencia y reversión E05/E06 | Copia candidata, diff/undo, revisión obsoleta, SQLite/asset referenciado y recuperación coherentes en mocks; original intocable |
| P2 | Perfil IFC | Fixtures de datos con unsupported/imported-mesh y tolerancias/unidades; IFC GUID conservado, inferencia de habitación marcada derivada |
| P2 | Piloto físico futuro | Runtime/hash y Node efectivos, WebGPU/recursos/licencias cerrados antes de prueba; no sustituir render ni atribuir Next al open source |

Bloqueos: requisitos/runtime/recursos y fidelidad IFC no validados; no impiden
contratos de datos independientes. Sin CAD real, mapas, renders o contenido nuevo;
ComfyUI, GitHub Dark y configuraciones conservados.
