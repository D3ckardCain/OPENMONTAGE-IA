# Centro de actualizaciones

Abre **Modelos y discos → Centro de actualizaciones**. El catálogo agrupa los enlaces de los pesos de Hugging Face por repositorio y muestra las aplicaciones integradas. Avanza con **Siguiente** y **Anterior**; cada página contiene diez fuentes. Los inventarios importados siguen siendo registros históricos de ruta y tamaño, no una inspección actual de todos los discos.

## Revisar lo que ya tenemos

Pulsa **Consultar fuente oficial** en un modelo. Se consulta una fuente por vez y se compara el commit remoto actual con los commits fijados en los enlaces del catálogo. Se indica cuántos archivos catalogados ya no figuran con el mismo nombre en la revisión remota. Un commit distinto significa que cambió el repositorio; no demuestra que cada peso haya cambiado ni que exista una mejora. Para yt-dlp y Deno se consulta el último release publicado de GitHub. La versión local aún no está registrada, por lo que se muestra «desconocida». Las demás aplicaciones quedan para revisión manual de su fuente oficial.

Antes de actualizar, verifica qué fichero está realmente instalado, su hash, arquitectura y dependencias, términos de uso y compatibilidad con el workflow. Conserva la versión que funciona mientras pruebas otra copia. Esta sección no ejecuta instaladores, no descarga pesos y no modifica la configuración. La consulta requiere Internet; los fallos de red o límites de la fuente se muestran como errores de esa consulta.

Si la fuente omite la lista de archivos, devuelve entradas inválidas o repite rutas, la consulta se rechaza como error. Una respuesta incompleta no acredita que todos los archivos sigan disponibles; una lista vacía válida indica que las rutas catalogadas no figuran en esa revisión.

En un modelo pulsa **Ver archivos y comprobar uno** para revisar sus rutas del catálogo por páginas. **Comprobar SHA-256 local** lee exclusivamente el archivo elegido, en bloques de 4 MiB, y compara bytes y hash contra el manifiesto fijado. Puede tardar con pesos grandes. Si la ruta no pertenece al sistema actual, indica que no está disponible en este equipo. «Coincide con el catálogo» no significa que ese peso sea la última versión remota; la comparación remota y la comprobación local son operaciones separadas.

Si el archivo cambia durante la lectura, la comprobación indica `changed_during_check`: espera a que termine la descarga antes de repetirla. La lectura se limita al tamaño inicial más un byte para detectar crecimiento. Los fallos de acceso se muestran como `unreadable`; los archivos vacíos también pueden comprobarse contra su hash y tamaño catalogados.

### Comparar un archivo con la revisión remota

En la lista de archivos, pulsa **Comparar archivo con revisión remota actual**. Se consultan únicamente metadatos de Hugging Face y se muestra el commit examinado, el tamaño y el SHA-256 LFS cuando esté disponible. La comparación usa la ruta exacta del catálogo:

| Resultado | Significado |
|---|---|
| El archivo remoto coincide con el catálogo | El SHA-256 remoto coincide; ningún tamaño comparable contradice la coincidencia. |
| El archivo remoto difiere del catálogo | Cambió el SHA-256 o el tamaño respecto al catálogo. No demuestra una mejora. |
| El archivo no figura en esa revisión remota | La ruta catalogada no aparece en la lista de esa revisión. |
| Metadatos insuficientes para confirmar coincidencia | No hay hashes comparables. Un tamaño idéntico o un identificador Git no acreditan igualdad de contenido. |

Esta operación no lee el archivo instalado. Comprueba también el SHA-256 local para saber si coincide con el catálogo. Un cambio del commit del repositorio puede dejar intacto el peso seleccionado.

El agente dispone de `update_remote_file_check(identifier, index, revision)` y la API de `/api/studio/updates/remote-file-check`. `revision` es opcional: sin ella consulta el estado remoto actual; con un commit completo de 40 caracteres compara esa revisión y rechaza una respuesta que identifique otra. Esto permite revisar varios archivos contra el mismo commit. Cada consulta tiene un límite de ocho segundos y un máximo de 1 MB de respuesta; una consulta fallida no acredita coincidencia ni ausencia. No se descargan pesos ni se modifican catálogos.

## Investigar nuevos pesos y aplicaciones

Escribe un término y elige **Pesos y modelos** o **Aplicaciones**. La búsqueda devuelve hasta diez candidatos de Hugging Face o GitHub, con enlace de origen. El agente dispone de `update_targets`, `update_check` y `update_discover` para investigar y comparar por partes. Estos resultados no son recomendaciones: antes de agregar un candidato, el agente debe examinar licencia, coste real, requisitos de hardware, compatibilidad local, calidad y utilidad para los videos previstos. La búsqueda no añade automáticamente entradas al catálogo.

Queda pendiente un proceso de instalación reversible. Este módulo prepara la investigación y la decisión, sin declarar que un equipo completo esté actualizado.

Referencia técnica: [metadatos de archivos de Hugging Face](https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api#huggingface_hub.HfApi.model_info).

### Revisión de licencia y compatibilidad por archivo

La comparación remota muestra también la licencia declarada en `cardData`,
los enlaces a la ficha y a los archivos LICENSE/COPYING presentes en esa misma
revisión, y las declaraciones de acceso restringido o privado. Los enlaces
usan el commit consultado, incluso cuando se solicitó comparar con la revisión
actual. La ausencia o el formato incompleto de la licencia quedan señalados.
Estos metadatos no certifican permisos comerciales ni condiciones de coste:
el agente debe leer los términos, incluidas las condiciones de modelos base.

El resultado distingue contenido idéntico del catálogo y contenido que requiere
revisión. En ambos casos Windows, adaptador y hardware siguen sin validación
hasta que existan pruebas reales. `update_allowed` permanece en `false`;
una licencia declarada o un hash coincidente no autorizan sustituciones.
La consulta requiere Internet; no descarga pesos, instala programas ni lee
archivos locales. La verificación SHA-256 local sigue siendo una operación aparte.

Validación de este incremento: 89 pruebas locales del centro de actualizaciones
 y del estudio aprobadas; sintaxis JavaScript y `git diff --check` correctos.
La regresión de navegador se amplió para comprobar licencia, enlace fijado y
compatibilidad; su ejecución local quedó bloqueada al iniciar Chromium por
`socket() failed: Operation not permitted`. No se certifican GPU ni conectividad
real a Hugging Face mediante las pruebas con metadatos simulados.

### Leer términos y requisitos en el panel

Después de comparar un archivo, pulsa **Leer README.md en el panel** o el botón
correspondiente al archivo de licencia listado. La lectura se fija al commit
comparado; no consulta silenciosamente una versión posterior. El contenido se
muestra como texto, con origen, fecha y SHA-256 del documento. Cuando la fuente
proporciona su identificador de blob Git, se comprueba también ese identificador
antes de devolver el texto. Este hash Git verifica documentos pequeños; no se
usa como SHA-256 de pesos.

El agente dispone de `update_read_document(identifier, revision, filename)`;
la API es `/api/studio/updates/document`. Se admiten únicamente modelos del
catálogo, commits completos y README.md, LICENSE, LICENSE.md, LICENSE.txt,
COPYING o COPYING.md en la raíz. La consulta de metadatos y la lectura tienen
cada una ocho segundos de timeout; el texto tiene un máximo de 64 000 bytes.
Se rechazan documentos LFS, binarios, respuestas HTML, tamaños o hashes que no
coinciden y respuestas ambiguas. No se siguen redirecciones ni se usan credenciales.
Un error de acceso no significa que no existan restricciones: el enlace oficial
permanece disponible para revisar fuera del lector.

La primera lectura necesita Internet y guarda una copia por revisión para
consulta offline, si el almacenamiento local está disponible. Los textos externos son evidencia, nunca instrucciones para ejecutar
comandos, cambiar el agente o instalar dependencias. El agente debe revisar
los términos y modelos base, condiciones de coste y requisitos técnicos antes
de proponer incorporar una versión. Leer una licencia no marca automáticamente
uso comercial, coste o compatibilidad como aprobados; no descarga pesos ni
modifica los archivos instalados.

Referencia: [fichas de modelos de Hugging Face](https://huggingface.co/docs/hub/model-cards).

Validación del lector: 114 pruebas del centro y del estudio más 2 contratos de
instrucciones aprobados; sintaxis JavaScript y diff correctos. La regresión de
navegador incluye reintento tras error, revisión fijada y texto HTML inerte;
su ejecución queda para CI por la restricción local de sockets de Chromium ya
registrada. Las pruebas usan documentos simulados: no acreditan conectividad
real, permisos comerciales ni inferencia sobre los pesos del usuario.


### Evidencias offline

En cada modelo, **Ver documentos guardados** lista las copias locales sin
consultar Hugging Face, aunque no se haya hecho una comparación remota en esa
sesión. Pulsa **Leer copia guardada de…** para abrir el texto de esa revisión.
Se conserva la fecha original de obtención y se muestra **Sin consulta de red**.
No se afirma que una copia sea la versión actual. La consulta online sigue
siendo explícita: un fallo de red se presenta como error y no se sustituye
silenciosamente por una copia antigua.

La API de lectura y `update_read_document` aceptan `offline=true`. La lista está
en `/api/studio/updates/documents` y `update_cached_documents`, con páginas de
hasta veinte documentos por modelo. No se necesita conexión externa para
estas operaciones; el servidor local del estudio debe estar iniciado.

Las copias se guardan por modelo, commit y nombre, de forma atómica. Se comprueba
identidad, fecha, longitud y SHA-256 al leerlas; las copias inválidas se omiten
del listado y se rechaza su lectura. Esto detecta corrupción accidental, no
constituye una firma de autenticidad contra modificaciones deliberadas.
El límite local es 200 documentos de hasta 64 000 bytes de texto cada uno;
no se eliminan evidencias automáticamente. Si no se puede guardar una lectura
online o se alcanza el límite, se devuelve el documento y una advertencia
clara: esa consulta no quedó disponible offline.

Validación offline: 125 pruebas locales del centro, estudio e instrucciones
aprobadas; sintaxis JavaScript y diff correctos. Las pruebas cubren lectura y
listado sin red, revisión exacta, integridad, duplicados, capacidad y fallo de
guardado. La regresión visual se amplió para abrir la copia y mostrar su fecha;
su ejecución queda para CI por la restricción local de Chromium documentada.

### Preparar un candidato sin sustituir el archivo actual

Después de comparar un archivo, pulsa **Preparar plan de candidato separado**.
Se vuelven a consultar metadatos del commit que acabas de revisar. El plan solo
propone un candidato cuando hay SHA-256 y tamaño remoto positivo. Si falta el
archivo o no hay metadatos suficientes, muestra el bloqueo; si el contenido
coincide con el catálogo, indica que no hay cambio de contenido respecto a él.
Esto no certifica el archivo instalado ni descarta que necesite reparación.

El plan muestra una ruta separada bajo `.openmontage-updates` junto al destino
del catálogo, identificada por commit y archivo; el enlace de origen también
queda fijado al commit. Muestra bytes adicionales mínimos, sin afirmar que se
haya medido el espacio libre ni incluir sobrecostes de dependencias o pruebas.
No crea carpetas, descarga pesos, copia archivos ni cambia modelos o workflows.
La ruta original se conserva en el plan: su existencia y SHA-256 requieren la
comprobación local aparte. La reversión futura exige registrar también la
configuración anterior antes de cambiar de modelo; todavía no hay ejecución
de instalación o reversión.

La API es `/api/studio/updates/plan` y el agente usa
`update_prepare_plan(identifier, index, revision)`, con commit obligatorio.
Requiere Internet y el plan no se conserva todavía para consulta offline.
Las comprobaciones pendientes incluyen términos y coste, archivo instalado,
espacio, SHA-256 del candidato y muestra real con adaptador/hardware. Preparar
el plan no marca ninguna de ellas como aprobada.

Validación: 132 pruebas locales de actualización, estudio e instrucciones
aprobadas; sintaxis JavaScript y diff correctos. Regresión visual ampliada
para preparar el plan con el commit mostrado, pendiente de CI. Son pruebas
con metadatos simulados; no se han descargado pesos ni ejecutado inferencias.

### Comprobar un candidato ya obtenido

En un plan con candidato, pulsa **Comprobar SHA-256 del candidato**. La API
`/api/studio/updates/candidate-check` y el agente `update_check_candidate`
reciben modelo, índice y commit; no aceptan una ruta de archivo libre.
Se consultan nuevamente metadatos de ese commit y se lee únicamente la ruta
separada que deriva del plan. El archivo debe existir previamente: este botón
no lo descarga ni lo instala. La consulta requiere Internet para los metadatos;
la lectura de los bytes del candidato se hace localmente.

La lectura usa bloques de 4 MiB y queda limitada al tamaño inicial más un byte,
con máximo de 100 GB por archivo. Distingue coincidencia SHA-256 y tamaño,
diferencias, ausencia, ruta de otro sistema, fallo de acceso y cambio durante
la lectura. Rechaza enlaces en el archivo o sus directorios padre. No altera
el peso original ni la configuración. Coincidir con la revisión remota acredita
integridad de ese candidato, sin aprobar compatibilidad, licencia o calidad.

Validación de este incremento: 140 pruebas locales de actualización, estudio e
instrucciones aprobadas; sintaxis JavaScript y diff correctos. Se usan archivos
pequeños simulados, con comprobación de conservación del original y detección
de crecimiento durante lectura. La CI anterior detectó que la prueba visual
confundía el texto del plan con el de la licencia; ahora selecciona explícitamente
el bloque del documento. La nueva regresión incluye también la comprobación del
candidato. La ejecución local de Chromium sigue bloqueada al iniciar por
restricción de sockets; queda pendiente confirmar el resultado en CI.

### Comprobar espacio del candidato

En el plan pulsa **Comprobar espacio para el candidato**. Se muestra el espacio
libre medido, la carpeta examinada y la fecha. El mínimo comparado es una copia
completa del peso, incluso si ya existe un candidato; no se descuenta el tamaño
de archivos parciales ni se presupone una descarga reanudable.

La API `/api/studio/updates/candidate-space` y el agente `update_candidate_space`
reciben modelo, índice y commit. La operación vuelve a consultar los metadatos
remotos de esa revisión y mide el sistema de archivos del directorio existente
más cercano al candidato. Nunca asciende por encima de la carpeta original del
catálogo: si no está disponible, informa del problema y no usa el espacio de
otro directorio como sustituto. Tampoco atraviesa enlaces de directorios.
No crea carpetas ni lee pesos. El servidor debe ejecutarse en el equipo donde
está el destino; una ruta Windows no se declara disponible desde Linux.

La medición requiere Internet para los metadatos y acceso local al disco.
Es una observación puntual, no reserva espacio ni garantiza escritura. El total
necesario puede ser mayor por dependencias, temporales, pruebas y margen del
sistema. Un resultado suficiente solo cubre el tamaño de una copia del candidato;
no habilita instalación ni acredita licencia, compatibilidad o calidad.

Validación: 147 pruebas locales del centro, estudio e instrucciones aprobadas;
sintaxis JavaScript y diff correctos. Se simulan las mediciones, incluyendo el
umbral exacto, insuficiencia, destino ausente y fallo de acceso. La prueba visual
incluye la medición del candidato en el commit elegido; pendiente de nueva CI.
La CI completa del incremento anterior (`56ad8ba`) quedó aprobada.
