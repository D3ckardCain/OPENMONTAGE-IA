# Centro de actualizaciones

Abre **Modelos y discos → Centro de actualizaciones**. El catálogo agrupa los enlaces de los pesos de Hugging Face por repositorio y muestra las aplicaciones integradas. Avanza con **Siguiente** y **Anterior**; cada página contiene diez fuentes. Los inventarios importados siguen siendo registros históricos de ruta y tamaño, no una inspección actual de todos los discos.

## Revisar lo que ya tenemos

Pulsa **Consultar fuente oficial** en un modelo. Se consulta una fuente por vez y se compara el commit remoto actual con los commits fijados en los enlaces del catálogo. Se indica cuántos archivos catalogados ya no figuran con el mismo nombre en la revisión remota. Un commit distinto significa que cambió el repositorio; no demuestra que cada peso haya cambiado ni que exista una mejora. Para yt-dlp y Deno se consulta el último release publicado de GitHub. La versión local aún no está registrada, por lo que se muestra «desconocida». Las demás aplicaciones quedan para revisión manual de su fuente oficial.

Antes de actualizar, verifica qué fichero está realmente instalado, su hash, arquitectura y dependencias, términos de uso y compatibilidad con el workflow. Conserva la versión que funciona mientras pruebas otra copia. Esta sección no ejecuta instaladores, no descarga pesos y no modifica la configuración. La consulta requiere Internet; los fallos de red o límites de la fuente se muestran como errores de esa consulta.

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
