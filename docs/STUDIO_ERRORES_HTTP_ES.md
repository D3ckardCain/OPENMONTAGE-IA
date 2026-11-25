# E02: errores HTTP y conservación de formularios (#114)

Entrega independiente del reinicio, desde el backlog E02/#58. #112/#113 siguen
pendientes y se agrupan con #114 para una única activación manual futura. No
se reinició ni consultó4750; no se repitieron pruebas aprobadas de esas entregas.

## Problema observado y cambio

El lector de `studio.js` llamaba a `response.json()` incluso sobre una página
HTML de error; podía mostrar errores de parseo sin conservar el código HTTP.
Crear/settings no tenían propiedad local del envío ni protección ante dos
submits concurrentes. Sus esperas no tenían un presupuesto explícito.
Además, un error con una ruta larga sin separadores de palabra hacía crecer
el scroll horizontal a4843px en viewport1280. `#notice` ahora envuelve ese texto
dentro del panel: scrollWidth1280, sin cambiar colores ni estilos de #113.

`studio-http.js` normaliza errores en StudioHTTPError con code,status,uncertain
y texto español. Conserva400/403/409/422/500 aunque el cuerpo falle o sea HTML;
estructura campos de validación sin `[object Object]` y no muestra trazas HTML.
200 sin JSON válido es invalid_response;204 es éxito vacío explícito.
No reintenta, no reinicia, no cambia servidor/proveedor ni modifica red/OS.

`requestJSON(path,data,options)` hace GET si data es undefined y POST JSON en
otro caso. timeoutMs por defecto0 mantiene los presupuestos de operaciones
largas existentes. Crear proyecto, guardar settings y leer bootstrap usan
**30000ms explícitos**: plazo de espera del cliente para operaciones locales
de metadatos, no timeout de inferencia ni medición del rendimiento del disco.
La prueba acelera ese reloj únicamente en su fixture; no cambia el presupuesto
del producto. El plazo incluye lectura del cuerpo, no solo cabeceras.

Un timeout, pérdida de conexión o error5xx de POST no demuestra rollback ni
detención del cálculo: el aviso pide consultar estado antes de repetir. Abortar
la espera del cliente no es una orden de detener el trabajo del servidor.
El diagnóstico histórico HTTP de #92 sigue conservado; esta entrega no afirma
su causa raíz ni repara transporte TCP/USB/consola.

`studio-production-forms.js` reutiliza los dos handlers existentes y
`studio-form-request.js` posee solo el envío del formulario local. aria-busy,
botón submit temporalmente deshabilitado y WeakSet bloquean doble envío.
No resetea los valores ni deshabilita todo Studio; conserva estados disabled
previos y restaura foco tras error sin robárselo a una navegación posterior.
Si el POST ya devolvió project_id pero falla bootstrap/select, muestra
«Proyecto creado (ID)» y pide consultar Proyectos, no repetir la creación.
No implementa idempotencia nueva de creación ni reconciliación del servidor.

La integración en `studio.js` sustituye su lector común y conecta estos dos
formularios. No cambia los lectores especiales de compatibilidad, editor,
Piper/recuperación ni presupuestos de inferencias de otras operaciones.

## Pruebas focalizadas nuevas

- **26 casos Node** en `tests/js/studio-http.test.mjs`:200/204,
  400/401/403/404/409/422/500/503, campos de validación, HTML/vacío,
  desconexión, deadline incluso con transporte simulado que ignora AbortSignal,
  cuerpo que no llega, cancelación antes/después de enviar, serialización local
  y plazos inválidos. Un fetch como máximo; se diferencia incertidumbre de POST.
- **16 escenarios navegador** (8por formulario) con HTML y JS de entrada reales:
  400/403/422/500,500HTML,200vacío,red fallida y timeout. Cada doble submit
  produce un solo POST a la API sintética; texto/rutas/Unicode y foco conservados,
  botones restaurados y navegación disponible. Se verifican las rutas separadas
  en bootstrap y en el payload JSON, sin escribir configuración real.
- Casos extra: foco del botón restaurado, control previamente disabled no se
  habilita, navegación posterior conserva foco, creación ya reconocida seguida
  de fallo de refresco y posterior guardado de settings sintético satisfactorio.
  Ruta larga en error400 contenida sin desbordar la página. Sin errores JS ni
  rutas de API inesperadas.

`scripts/validate_studio_http_forms.cjs` usa Chrome/Playwright existentes y una
URL fixture127.0.0.1:4776 cuyas peticiones se interceptan completamente. API de
bootstrap/proyectos/settings ficticia; lectura de ediciones de fútbol de arranque
devuelve una lista vacía, no consulta un servicio. No abre un servidor real ni
conecta a4750. Reloj30s reducido a80ms solo en pruebas; un caso de foco usa1s.
No son solicitudes de producción, inferencia, voz ni validación del backend.

Reproducción con instalaciones existentes:

```text
node --test tests/js/studio-http.test.mjs
node scripts/validate_studio_http_forms.cjs
```

Para la segunda, proporcionar PLAYWRIGHT_MODULE y CHROME_EXE existentes. No hay
instalación automática. Informe local `.runtime/qa/studio-http-forms.json`.
Wrapper CI focalizado `tests/backlot/test_studio_http_js.py` ejecuta el contrato
Node si está disponible; no se afirma que ese wrapper/CI completa se haya
ejecutado por pasar el comando Node local. No se repiten suites aprobadas.

## Alcance y pendientes

Falta comprobar esta entrega en el panel4750 después del lote manual único.
Las operaciones largas conservan sus presupuestos previos; no se proclama que
toda petición de Studio tenga deadline nuevo ni que todos sus formularios estén
cubiertos. E02 global y su accesibilidad completa siguen abiertos. No se certifica
WCAG ni se confunde una respuesta/cabecera con la terminación del cómputo.

Configuraciones, originales, .venv, ComfyUI y GitHub Dark preservados. Coste$0,
sin instalaciones/modelos/contenido nuevo. Naturalidad/robótica de voces sigue
aplazada y PR#2 permanece en borrador, sin merge.
