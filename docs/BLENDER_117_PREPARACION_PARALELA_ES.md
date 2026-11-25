# #117: Blender reciente junto a 4.5 LTS — preparación previa a descarga

Consulta25-11-2026 UTC. Se completa la preparación documental autorizada, sin
descargar/instalar Blender ni ejecutar complementos o scripts externos.
La [ficha previa](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/117#issuecomment-7178219233)
publica enlace, tamaño, SHA256 y destino antes de cualquier descarga del binario.

## Selección y referencias oficiales

La [página oficial de descargas](https://www.blender.org/download/) y las
[versiones activas](https://www.blender.org/releases/) identifican5.3.0 como
estable reciente, publicada10-11-2026. También siguen activas5.2LTS y4.5LTS;
los índices consultados fijan5.2.5 y4.5.17, ambas del24-11-2026.

**Preparar5.3.0 portable en paralelo y conservar4.5.15LTS.** El mínimo anunciado
por Blender-Skills es5.2, pero su autor señala5.3 como entorno verificado.
No hace falta añadir además una tercera instalación5.2.5 para esta evaluación.
Reemplazar únicamente4.5 perdería el entorno validado de MolecularNodes4.5.11
y expondría el adaptador actual a cambios API conocidos.4.5.17 es una opción
posterior de mantenimiento, no una actualización aplicada aquí.

| Opción Windows x64 | Bytes exactos del índice oficial | SHA256 del manifiesto oficial | Decisión |
|---|---:|---|---|
|5.3.0 portable|425299259|3ac567a63d59d9934f7b9213bfb27ba05760e1fb366f8f55c381573ec3eabfa8|Candidato paralelo elegido|
|5.2.5LTS portable|405726688|1fad54a676c3bb08fdcb5a2ae1eaaf02f8c492af02bd5ca292bcdbb28b6bb29a|Alternativa no seleccionada|
|4.5.17LTS portable|398351060|282b9bfc14065d6341c0d70d83992f80bde09d99e0099bff260c94bbec93803d|Mantenimiento futuro, no sustituir4.5.15 ahora|

Enlaces del candidato:

- [ZIP oficial5.3.0 x64](https://download.blender.org/release/Blender5.3/blender-5.3.0-windows-x64.zip).
- [Índice oficial/tamaño](https://download.blender.org/release/Blender5.3/).
- [SHA256 oficial](https://download.blender.org/release/Blender5.3/blender-5.3.0.sha256).
- Alternativas: [índice5.2](https://download.blender.org/release/Blender5.2/),
  [SHA5.2.5](https://download.blender.org/release/Blender5.2/blender-5.2.5.sha256),
  [índice4.5](https://download.blender.org/release/Blender4.5/),
  [SHA4.5.17](https://download.blender.org/release/Blender4.5/blender-4.5.17.sha256).

Se leyeron directamente los manifiestos de download.blender.org; para5.3 se
contrastó también la misma entrada mediante el servicio oficial de mirrors.
Los errores402/403 del lector web no se interpretaron como fuente inexistente:
las consultas HTTPS de texto acotadas desde el proyecto sí respondieron.
No se hizo GET del ZIP, instalador ni modelos. El SHA256 publicado es esperado;
todavía no existe una descarga local nueva para certificarlo.

## Destinos y aislamiento previstos

```text
ZIP: D:\OPENMONTAJE-IA\DESCARGAS_SOFTWARE\Blender\blender-5.3.0-windows-x64.zip
EXE: D:\OPENMONTAJE-IA\HERRAMIENTAS\Blender\5.3.0\blender-5.3.0-windows-x64\blender.exe
Perfil: D:\OPENMONTAJE-IA\HERRAMIENTAS\Blender\5.3.0\profile
Actual: D:\OPENMONTAJE-IA\HERRAMIENTAS\Blender\4.5.15\blender-4.5.15-windows-x64\blender.exe
```

Búsqueda por nombres en herramientas/Blender, DESCARGAS_SOFTWARE y Descargas
del usuario: solo ejecutable/ZIP4.5.15; no5.3/5.2 preparado en esas ubicaciones.
No se afirma búsqueda exhaustiva de todo disco/archivo renombrado.

El futuro lanzador debe establecer `BLENDER_USER_RESOURCES` únicamente para el
proceso5.3, según el [manual5.3](https://docs.blender.org/manual/en/5.3/advanced/blender_directory_layout.html).
Preferencias/scripts/extensiones separados; no importar automáticamente4.5,
no reutilizar sus site-packages cp311 ni modificar variables globales.
Antes de habilitar complementos, respaldar las preferencias implicadas; en esta
fase no se modificaron ni se creó una copia redundante de preferencias intactas.
Bibliotecas de medios y modelos compatibles se referencian por ruta/hash;
no se duplican por instalar Blender. El ZIP original4.5 y ambos ZIP de MN se
conservan. Se medirá espacio para ZIP+extracción+perfil antes de descargar:
425MB de ZIP no equivalen al tamaño extraído ni reservan espacio.

## Compatibilidad: declaración, análisis y prueba son estados distintos

| Recurso fijado | Evidencia reutilizada/lectura actual | Resultado para5.3 |
|---|---|---|
|[EL4CTEO/blender-skills@1a1cc6c](https://github.com/EL4CTEO/blender-skills/tree/1a1cc6c49312f9f370aae86f52b7b907f29c94f6)|README y referencia API del mismo commit: mínimo5.2LTS, verificado5.3 según autor;28skills/MIT|Elegible para piloto5.3; ninguna prueba del autor se cuenta como prueba local. No instalar en ~/.agents/.claude ni ejecutar su instalador|
|Archimesh1.2.5|Manifiesto instalado y ZIP existente323488bytes: min4.2, sin máximo; GPL-2.0-or-later. [Catálogo oficial](https://extensions.blender.org/add-ons/archimesh/) indica soporte limitado|Rango declarado admite candidato, pero no prueba sus paneles/operadores en5.3. Registro en4.5 ya aprobado: no repetir. Ensayo5.3 aislado pendiente|
|MolecularNodes4.5.11 instalado|Manifiesto min4.5/max5.1, wheelscp311; GPL-3.0-or-later. [#16](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/16#issuecomment-7111768355) ya acredita carga/imports en4.5.15|Fuera del rango declarado5.3; conservar en4.5, no copiar al perfil nuevo|
|MolecularNodes520.2.0 existente|ZIP133201891bytes, manifiesto min5.2/sin máximo, wheelscp313; GPL-3.0-or-later. [Release oficial](https://github.com/BradyAJohnston/MolecularNodes/releases/tag/v520.2.0), digest23e8ddb1b7f0309b0b132f4d563586d67ed5336b01aca5d77fac054bc3b4cfee, también registrado en#16|Reutilizar ese paquete como candidato5.3, sin otra descarga. ABI/imports y compatibilidad funcional aún pendientes; no compartir las dependencias4.5|
|blender_world actual|Configuración selecciona4.5.15, runtime fija BLENDER_EEVEE_NEXT (línea379), usa scene.eevee.taa_render_samples y action.fcurves|No cambiar el ejecutable activo a5.3: el identificador EEVEE cambió oficialmente en5.0 y las acciones tienen API nueva. Hay trabajo de adaptación real pendiente|

Fuentes de cambios: [notas oficiales5.0/Python](https://developer.blender.org/docs/release_notes/5.0/python_api/)
y [tabla fijada del candidato](https://github.com/EL4CTEO/blender-skills/blob/1a1cc6c49312f9f370aae86f52b7b907f29c94f6/skills/blender-core/references/api-changes-5x.md).
No se adoptaron sus instrucciones como política del proyecto. No se ejecutó
código remoto, MCP nuevo, pruebas del candidato ni Blender.

## Requisitos, licencia y operación local

[Requisitos oficiales](https://www.blender.org/download/requirements/): CPU con
4núcleos/SSE4.2,8GBRAM mínimo/32GB recomendado, GPU2GB mínimo/8GB recomendado,
OpenGL4.3 con extensiones indicadas y Vulkan1.3 según backend. Comprobar el
Windows x64/driver concreto al ensayar5.3; la máquina ya inventariada no recibe
una certificación de rendimiento/driver por tener4.5 funcionando. No cambiar
drivers/OS como parte de esta preparación. Cycles/GPU y bibliotecas grandes
requieren su propia medición de RAM/VRAM; no se promete capacidad por versión.

[Blender binario GPL-3.0-or-later](https://www.blender.org/about/license/), con
licencias de dependencias conservadas. Skills MIT y complementos GPL mantienen
sus avisos; modelos/HDri/texturas/assets externos tienen derechos independientes.
Uso local gratuito sin suscripción/API. Red para obtener binario/metadata;
ejecución local posterior no necesita servicios de pago. Bloquear descargas
implícitas al pilotar skills; MCP es opcional y no se instala. MN puede solicitar
PDB/AFPDB: solo archivos locales en el piloto, ninguna consulta molecular real.

## Entregas siguientes y aceptación — E01/E06/E10/E11 existentes

1. **Provisión portable:** comprobar de nuevo ausencia del candidato y espacio;
   descargar una sola vez desde enlace publicado, comparar bytes/SHA256 antes
   de extraer en ruta nueva. Mantener ZIP y4.5.15; no asociaciones de .blend.
2. **Arranque/registro aislados:** versión/ABI reales y entorno documentados;
   registro y descarga cero al cargar Archimesh/MN520 desde ZIP existentes.
   No guardar preferencias4.5 ni abrir archivos originales. Fallo de ABI o de
   clases produce bloqueo explícito, no instalación pip en Studio/ComfyUI.
3. **Perfil compartido Studio/agente:** extender aplicaciones/actualizaciones
   existentes con ID, ejecutable, versión/fingerprint, capacidades por perfil y
   estado preparado/carga/automatización. Hoy Applications conserva una sola
   ruta Blender y las comprobaciones automáticas de versión solo cubren otras
   herramientas: no fingir selector multiperfil implementado por este documento.
   Selección explícita; perfil inexistente/incompatible da error, nunca fallback
   silencioso. No añadir otro centro de aplicaciones o servidor MCP.
4. **Adaptador5.x:** resolver EEVEE/acciones/samples por capacidades/versiones;
   regresiones focalizadas4.5/5.3 y rechazo de versión no admitida. Mantener
   trayectoria4.5 validada; no repetir suites aprobadas durante esta preparación.
5. **Prueba de uso posterior:** copia .blend autorizada, apertura/reapertura,
   pérdidas visibles y un QA autorizado antes de migrar proyectos. Headless no
   demuestra la escena de una ventana abierta. No geometría/render ahora.

El mantenimiento4.5.17 y la posible retirada de4.5 se decidirán por evidencia
de compatibilidad/proyectos; no se conserva una versión vieja sin justificación
ni se elimina la que aún soporta complementos actuales.

## Resultado de esta fase

Plan y [manifiesto máquina](BLENDER_117_PLAN_20261125.json) publicados antes de
descargar. Validación documental: JSON/TOML, rangos/ABI, coincidencia de checksums
oficiales y rutas; sin ejecutar pruebas ya aprobadas. Configuraciones Studio y
preferencias4.5 conservadas; no cambios en ComfyUI/.venv, Studio no reiniciado.
#112 recuperación por recibo elegible y acciones ocultas de#113 siguen pendientes.
Naturalidad de voces aplazada; coste$0 y PR#2 borrador. #117 permanece abierto:
preparar una actualización no acredita provisión, carga ni automatización5.3.
