# Centro de actualizaciones

Abre **Modelos y discos → Centro de actualizaciones**. El catálogo agrupa los enlaces de los pesos de Hugging Face por repositorio y muestra las aplicaciones integradas. Avanza con **Siguiente** y **Anterior**; cada página contiene diez fuentes. Los inventarios importados siguen siendo registros históricos de ruta y tamaño, no una inspección actual de todos los discos.

## Revisar lo que ya tenemos

Pulsa **Consultar fuente oficial** en un modelo. Se consulta una fuente por vez y se compara el commit remoto actual con los commits fijados en los enlaces del catálogo. Se indica cuántos archivos catalogados ya no figuran con el mismo nombre en la revisión remota. Un commit distinto significa que cambió el repositorio; no demuestra que cada peso haya cambiado ni que exista una mejora. Para yt-dlp y Deno se consulta el último release publicado de GitHub. Esa consulta no ejecuta el programa local y mantiene su versión como «desconocida»; usa los botones de versión descritos más abajo para comprobarla explícitamente. Las demás aplicaciones quedan para revisión manual de su fuente oficial.

Antes de actualizar, verifica qué fichero está realmente instalado, su hash, arquitectura y dependencias, términos de uso y compatibilidad con el workflow. Conserva la versión que funciona mientras pruebas otra copia. Consultar fuentes no ejecuta instaladores, no descarga pesos y no modifica la configuración. La descarga de candidatos es una acción separada y explícita, descrita más abajo. La consulta requiere Internet; los fallos de red o límites de la fuente se muestran como errores de esa consulta.

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


### Descargar o reanudar un candidato separado

En un plan con SHA-256, pulsa **Descargar/reanudar candidato separado**. Es una
acción explícita: preparar o comparar el plan no inicia descargas. Se vuelve a
comprobar el commit y el hash elegido, el destino y el espacio para una copia
completa. Solo se admite un trabajo a la vez y candidatos de hasta 100 GB.
El peso instalado y la configuración no se sustituyen.

El panel muestra estado y bytes; **Cancelar descarga** conserva el parcial.
Si hubo una interrupción, vuelve a pulsar descargar para reanudar la misma
revisión: se comprueba el parcial y se exige que el servidor responda al rango
exacto solicitado. Si el servidor ignora el rango, se conserva el parcial y se
informa del error, sin concatenar la respuesta completa. Un parcial corrupto
requiere **Descartar solo el parcial** antes de empezar de nuevo; esa acción
solo borra el `.part` de un trabajo fallido o cancelado, nunca el modelo
original ni un candidato ya terminado.

El candidato se escribe primero con extensión `.part`. Antes de finalizar se
comprueban el tamaño y SHA-256 completos, incluida una lectura local final.
Si ya hay un archivo en la ruta final, solo se acepta si coincide; nunca se
sobrescribe. En discos con enlaces duros la finalización no duplica el peso;
en otros sistemas, como exFAT, se necesita espacio para copiar el candidato
completo además del parcial. Si no cabe, el parcial queda guardado para
reintentar. Un error o cancelación durante esa copia elimina únicamente la
copia final incompleta creada por el propio trabajo.

**Ver descargas de este candidato** recupera controles tras recargar el panel.
El historial local conserva los últimos veinte trabajos tras reiniciar el
servidor; los parciales siguen en disco y la reanudación inicia un nuevo
trabajo explícito, como se detalla más abajo. La cancelación puede esperar al timeout de una
lectura de red (30 segundos) o al final de la comprobación local en curso.

La descarga requiere Internet. El transporte usa HTTPS sin credenciales,
no introduce claves, tarjetas ni servicios de inferencia. Sigue redirecciones
solo a `huggingface.co`, `cdn-lfs.huggingface.co`, `cdn-lfs-us-1.hf.co`,
`cdn-lfs-eu-1.hf.co` y `cas-bridge.xethub.hf.co`; otros destinos producen un
error explícito. Los modelos privados o que requieran autorización pueden
necesitar el flujo de descarga oficial externo; este módulo no sortea ese
acceso. La descarga y el hash no aprueban licencia comercial, compatibilidad
ni calidad y no instalan dependencias ni activan el modelo.

API: `POST /api/studio/updates/downloads`, con `identifier`, `index`, `revision`
y `expected_sha256` del plan. Consulta el trabajo con `GET .../downloads/{id}`;
`POST .../{id}/cancel` y `POST .../{id}/discard-partial` reciben `{}`. La lista
por modelo, índice y revisión está en `GET .../downloads`. Los agentes disponen
de `update_download_candidate`, `update_download_status` y
`update_download_cancel`; iniciar requiere una petición explícita de descarga.

Validación: 167 pruebas locales de descargas, centro, estudio e instrucciones
aprobadas; sintaxis JavaScript y diff correctos. Las descargas se simulan con
archivos pequeños: no se descargaron pesos del usuario. Se probaron reanudación,
interrupciones, cancelación, rangos ignorados, contenido incorrecto, conservación
del original, finalización sin enlaces duros y descarte explícito. La nueva
regresión visual usa un transporte simulado. Conectividad real a los servidores
de modelos, rendimiento de descarga y GPU siguen sin validación aquí.


### Recuperación después de reiniciar el estudio

El estado se guarda de forma atómica en el historial local, con un máximo de
veinte trabajos y 128 KB de datos. Los cambios de estado se guardan inmediatamente;
el progreso se registra como máximo una vez por segundo. Una advertencia visible
indica si no se pudo guardar o recuperar el historial. No se borran parciales
cuando sale un registro antiguo del historial.

Al volver a abrir **Ver descargas de este candidato**, un trabajo que quedó en
cola, comprobando, descargando o verificando aparece como **interrumpido**.
Una descarga que terminó antes del reinicio aparece como dato histórico pendiente
de nueva comprobación: los bytes registrados no certifican el estado actual del
disco. Ningún trabajo se reanuda automáticamente ni se abre una conexión de red
solo por cargar el historial.

Pulsa **Reanudar trabajo guardado** para comprobar otra vez modelo, commit,
SHA-256 y ruta y crear un nuevo trabajo. Si cambió la ruta del catálogo, se exige
preparar un plan nuevo; tampoco se permite descartar un parcial en una ruta
que no coincida con la guardada. Se comprueba el parcial real antes de reanudar;
si el candidato final ya existe, se verifica su hash en lugar de sustituirlo.

La API añade `POST .../downloads/{id}/resume` con `{}` y el agente
`update_download_resume(job_id)`, siempre mediante una petición explícita.
Consultar el historial funciona offline; reanudar o descartar sigue necesitando
metadatos remotos para comprobar el plan. Los registros inválidos se omiten con
advertencia y nunca se usan como rutas libres ni como autorización de instalación.

Validación: 174 pruebas locales de descargas, centro, estudio e instrucciones
aprobadas; sintaxis JavaScript y diff correctos. Incluye recuperación sin red,
estados históricos, reanudación explícita, cambio de ruta, límite y fallo de
guardado y escritura de progreso limitada. La regresión visual comprueba que
el trabajo recuperado espera al botón. Se usan archivos y transferencias simulados;
no se descargaron modelos reales. La CI del incremento anterior quedó aprobada.

### Revisar impacto en familias y adaptadores

En la lista de archivos pulsa **Revisar impacto del archivo**. Funciona sin
Internet: relaciona la fuente por repositorio y ruta remota exactos, incluyendo
copias previstas en otras carpetas y familias que comparten esa dependencia.
Dos archivos con el mismo nombre pero distinta ruta remota no se equiparan.
La API es `/api/studio/updates/impact` y el agente usa
`update_impact(identifier, index)`.

El informe muestra familia, motor nativo o ComfyUI, dependencias declaradas,
configuración actual declarada del adaptador y archivos acompañantes del
catálogo. Se muestran como máximo veinte acompañantes por familia, junto al
recuento completo. Una familia puede necesitar configuraciones, tokenizadores,
VAE o encoders de la misma distribución: actualizar un peso aislado no demuestra
que el conjunto siga siendo compatible.

Es un mapa del catálogo, no un seguimiento del uso real dentro de cada grafo.
No lee los pesos, ejecuta modelos, consulta servidores ni instala dependencias.
Tampoco certifica que una ruta configurada exista o sea el modelo utilizado en
una producción. Si no encuentra familias vinculadas, muestra esa ausencia sin
considerarla aprobación de compatibilidad. La activación del candidato y una
muestra real siguen pendientes; este informe no modifica la configuración.

Validación: 177 pruebas locales de actualización, descargas, estudio e
instrucciones aprobadas; sintaxis JavaScript y diff correctos. Incluye fuente
compartida entre carpetas, exclusión de archivos homónimos, dependencias,
configuración sin cambios y acceso mediante API/agente sin consultar la red.
La regresión visual consulta el impacto antes de comparar con la fuente remota.
Son pruebas con manifiestos y transportes simulados, sin inferencia real.


### Comparar la versión instalada de yt-dlp y Deno

En estas dos aplicaciones hay dos acciones explícitas:

- **Ver versión local sin consulta remota** ejecuta únicamente la consulta de
  versión del archivo configurado, sin consultar GitHub.
- **Comparar versión instalada** obtiene la versión local y consulta después el
  último release oficial para comparar versiones estables.

Se requiere una ruta absoluta al ejecutable admitido en la configuración;
no se buscan alternativas en PATH ni se ejecutan instaladores. yt-dlp usa
`--ignore-config --no-plugin-dirs --version` y Deno usa `--version`, con
comprobación de actualizaciones de Deno desactivada para ese proceso. Se usa
una lista fija de argumentos, sin shell, con timeout de cinco segundos.
Consultar fuentes o abrir el catálogo sigue sin ejecutar estos comandos.

La comparación de yt-dlp interpreta fechas válidas y la de Deno compara los
componentes numéricos de una versión estable. Distingue versión coincidente,
release posterior y versión local más reciente. Prereleases, formatos
inesperados, fallo de proceso o ejecutable modificado durante la consulta
quedan sin conclusión automática. Si falla la consulta remota, conserva la
versión local y no afirma que esté actualizada. Las otras aplicaciones
continúan en revisión manual; una versión coincidente no demuestra
compatibilidad ni autoriza sustituciones.

API: `POST /api/studio/updates/application-version`, con `identifier` y
`online` opcional (por defecto `true`). El agente dispone de
`update_application_version`; `online=false` funciona sin la consulta remota.
No instala, descarga actualizaciones, activa modelos ni modifica configuración.
Cada comprobación intenta guardar un registro histórico local; su consulta se describe a continuación.

Validación: 192 pruebas locales de versiones, actualización, descargas,
estudio e instrucciones aprobadas; sintaxis JavaScript y diff correctos.
Las consultas de procesos y releases se simulan. La nueva prueba visual
verifica que cargar el catálogo no consulte versiones y que cada botón use
el modo elegido. No se ejecutaron los binarios del usuario.

Referencias: [opciones de yt-dlp](https://github.com/yt-dlp/yt-dlp#general-options)
y [consulta de versión de Deno](https://docs.deno.com/runtime/getting_started/installation/).


### Historial offline de versiones comprobadas

El botón **Ver historial de versiones** conserva y muestra las últimas veinte
comprobaciones por aplicación. Cada registro incluye fecha, versión local,
release consultado cuando lo hubo y ruta del ejecutable. Se guarda localmente
de forma atómica, con máximo de 128 KB por aplicación; no se envía a GitHub.

Consultar el historial no ejecuta yt-dlp o Deno ni consulta servicios externos.
Compara la ruta configurada y, cuando hay huella guardada, tamaño, fecha de
modificación e identidad del archivo. Informa de ruta cambiada, metadatos
cambiados, archivo no disponible o metadatos coincidentes. Esta huella no es
un hash de contenido y no certifica autenticidad ni la versión actual; todos
los resultados de la lista quedan identificados como históricos.

Si falla el guardado, la consulta nueva conserva su resultado y muestra una
advertencia. Un historial ilegible o inválido no se considera vacío ni se
sobrescribe automáticamente; una nueva consulta puede seguir funcionando sin
perder su resultado actual. La lista no depende del disco de aplicaciones
pendiente: si el ejecutable está desconectado, muestra su estado no disponible.

API: `GET /api/studio/updates/application-version-history?identifier=deno`
(o `yt-dlp`). El agente usa `update_application_version_history`. Las consultas
locales con `online=false` también quedan registradas. No se instalan ni
actualizan programas al guardar o leer esta evidencia.

Seguimiento: [Issue #4](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/4).
Validación: 197 pruebas locales de versiones, actualización, descargas, estudio
e instrucciones aprobadas; sintaxis JavaScript y diff correctos. Incluye acceso
sin procesos ni red, cambios de ejecutable y ruta, límite de veinte registros,
fallo de guardado y preservación de un historial dañado. La regresión visual
consulta el historial sin repetir la comprobación de versión. No se ejecutaron
binarios reales del usuario; CI del incremento pendiente de completar.
