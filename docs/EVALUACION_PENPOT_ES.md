# Penpot: evaluación #59

24-11-2026 UTC. Release oficial2.19.4 resuelta a
`1177a817ed10f95d3df5ce33d0aa67eba16f863b`. HEAD develop consultado por separado:
`df3445cfb30b673397d578c34ff5082e80ddb1cd`. Análisis del código de la release;
documentación web consultada en esta fecha es mutable, no equivale al snapshot.
Sin instalar contenedores/MCP/plugins ni crear diseños o contenido.

## Decisión y contraste

Penpot aporta prototipos compartidos, componentes/variantes, tokens y layouts
Grid/Flex. Es opcional para diseño, no sustituye Studio ni convierte automáticamente
un diseño en aplicación funcional. Primero formalizar tokens de GitHub Dark y
pruebas accesibles en el código actual; se puede especificar intercambio sin servidor.
Agrupar con Taste/Impeccable y Diagram Design; no mantener tres sistemas de tokens.

Existente: `backlot/ui/studio.css`/HTML/JS, fixtures Playwright, visual-style y
componentes del compositor. Esas piezas no son una herramienta colaborativa de
prototipado, pero resuelven la UI ejecutable y su validación. SVG/CSS exportado no
preserva por sí solo lógica API, permisos, cancelación ni accesibilidad del panel.
No portar apariencia de Penpot ni modificar GitHub Dark por adoptar la herramienta.

## Fuentes y requisitos

[README](https://github.com/penpot/penpot/blob/1177a817ed10f95d3df5ce33d0aa67eba16f863b/README.md),
[Compose](https://github.com/penpot/penpot/blob/1177a817ed10f95d3df5ce33d0aa67eba16f863b/docker/images/docker-compose.yaml):
frontend/backend/exporter, PostgreSQL15 y Valkey8.1, MCP/admin y Mailpit en el
ejemplo. Compose de este tag usa PENPOT_VERSION default2.18: no basta descargarlo
para afirmar2.19.4 instalado. Fijar versión/digest de cada imagen futura y comprobar
publicación, compatibilidad y persistencia; documentación advierte desfase de imágenes.
DB y assets necesitan respaldo conjunto y secreto estable, no borrar volúmenes.

[Docker oficial](https://help.penpot.app/technical-guide/getting-started/docker/)
requiere Docker/Compose. En Windows, capacidad de contenedores Linux/virtualización
y recursos quedan por verificar, sin instalarlos. Los
[ajustes recomendados](https://help.penpot.app/technical-guide/getting-started/recommended-settings/)
citan4CPU/16GB para miles de usuarios y crecimiento de disco dependiente de archivos:
no son mínimo probado para esta laptop ni garantía de coexistencia con modelos.

[MCP en la release](https://github.com/penpot/penpot/blob/1177a817ed10f95d3df5ce33d0aa67eba16f863b/mcp/README.md)
requiere servidor y plugin abierto/pestaña activa. Node>=20 declarado, servidor
package1.0.0 con pnpm12.16.1; compatibilidad efectiva del gestor se debe verificar,
no deducirla del floor Node del paquete. StreamableHTTP local /mcp sustituye SSE.
El plugin permite ejecutar código sobre su API de diseño; no es conector solo lectura.
La [guía actual MCP](https://help.penpot.app/mcp/) distingue remoto/local y capacidades
de lectura/modificación. No instalar helpers globales ni reducir seguridad del navegador.
Modelo local débil puede producir código inválido; vision y corrección no certificadas.

## Licencias, $0 y offline

[LICENSE](https://github.com/penpot/penpot/blob/1177a817ed10f95d3df5ce33d0aa67eba16f863b/LICENSE)
MPL2.0: conservar avisos y obligaciones de fuente de archivos cubiertos al distribuir
modificaciones; no es MIT ni licencia de todos los assets exportados. Revisar
subcomponentes: package del servidor MCP declara MIT, no extender esa declaración
a Penpot completo. Plugins, iconos, fuentes y plantillas requieren avisos propios;
no se copió código ni se interpreta export como cesión de cualquier recurso.

Autoalojado comunitario puede tener costo de API/licencia $0 sin Enterprise;
infraestructura, almacenamiento y recursos siguen siendo requisitos. No usar cloud
como sustituto gratuito ni aceptar tarjetas/trials. Compose leído activa telemetría
con PENPOT_TELEMETRY_ENABLED=true; la configuración final debe desactivarla y
comprobar ausencia de egreso, sin cambiar nada en esta fase.

[Configuración actual](https://help.penpot.app/technical-guide/configuration/)
documenta proxies externos de fuentes/plantillas y enable-air-gapped-conf para
deshabilitarlos. Una instancia local sola no acredita offline. Precargar imágenes,
fuentes y assets permitidos, alojar plugin/MCP local y probar con red bloqueada;
no confundir proxy local con ausencia de tráfico externo. No cuenta OAuth externa
ni email remoto necesarios para el perfil mínimo de prueba propuesto.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Tokens neutrales de Studio junto a #45/#58/#60 | Colores/espaciados/foco/tipografía/estados desde CSS actual, identificadores estables; import/export reversible sin cambiar apariencia |
| P2 | Contrato de prototipo | Mapeo componentes/tokens/SVG hacia UI; lógica y accesibilidad quedan en código; cambios no aplicados automáticamente |
| P3 | Perfil autoalojado mínimo | Versiones/digests/avisos/volúmenes/backup, puertos locales y recursos medidos; sin imágenes latest, sin ee ni fuentes/telemetría externas |
| P3 | MCP acotado | Lectura de archivo de fixture antes de habilitar edición; scope de documento, diff, backup y recuperación; no código arbitrario sin revisión |
| P3 | Prueba offline/restore futura | Reiniciar/restaurar DB+assets conserva IDs/variantes; export local con acentos y fuentes presentes; egreso cero registrado |

Bloqueos: infraestructura/recursos y cierre offline no verificados, despliegue
innecesario para corregir UI. Tokens y contratos son independientes y ejecutables
en una fase posterior. Ningún diseño, cuenta, servicio o configuración se creó aquí.
