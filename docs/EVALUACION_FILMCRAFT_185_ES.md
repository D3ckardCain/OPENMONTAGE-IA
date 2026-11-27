# Evaluación FilmCraft Edit/MCP (#185)

Fecha de revisión: 2026-11-27. Revisión estática de fuentes oficiales fijadas; no se instalaron paquetes, no se descargó el editor y no se ejecutó ni generó contenido.

## Fuentes y versiones

| Componente | Referencia examinada | Licencia / estado |
|---|---|---|
| FilmCraft MCP | [`kanishk-gangwar/filmcraft-mcp` @ `2a67c359b52b1166035b34b79a40b0044199c322`](https://github.com/kanishk-gangwar/filmcraft-mcp/tree/2a67c359b52b1166035b34b79a40b0044199c322) | MIT declarado en `LICENSE`; `package.json` version `0.2.0`, Node `>=18`, MCP SDK `^1.32.2`, Zod `^4.6.7`. El README no fija una release del MCP.
| FilmCraft | Última release oficial consultada [`v0.20.1`](https://github.com/storytold/filmcraft/releases/tag/v0.20.1), publicada 2026-11-12; código principal observado en [`7b8e522d63f2e2c1617dea4939feb48e769d6f2f`](https://github.com/storytold/filmcraft/tree/7b8e522d63f2e2c1617dea4939feb48e769d6f2f) | Código dual MIT o Apache-2.0 (`LICENSE-MIT`, `LICENSE-APACHE`). La licencia de marcas de ArtCraft está separada; los recursos y fuentes tienen avisos propios. La licencia del código no concede automáticamente derechos sobre marcas, medios ni fuentes.

El README de MCP aún dice que sus pasos se probaron con FilmCraft `v0.17.1`; no se debe presentar esa afirmación como validación de `v0.20.1`. El README actual sí describe Windows, macOS y Linux, Node 18+, y requiere `filmcraft-cli`; en Windows señala la instalación MSI en `%LOCALAPPDATA%\Programs\ArtCraft\FilmCraft\filmcraft-cli.exe`. La app gráfica es opcional para abrir/revisar proyectos o conectar el puente vivo. La release `v0.20.1` ofrece artefacto Windows x64 portable ZIP de **113,447,048 bytes**, SHA256 publicado `bfb00e2089df5f13e6f76aab117a4572a8d005d009c5818989688b140a502710`, y MSI de **93,388,800 bytes**, SHA256 publicado `165c0f333d995ced16c0b0ebc0b29cc9b7ad358bc812c705659d78e59aa25449`. Los datos provienen de metadatos oficiales de release; esta evaluación no descargó ni volvió a calcular esos archivos.

## Qué aporta y qué ya existe

FilmCraft MCP ofrece wrappers de nivel editor con tiempos en segundos, comandos genéricos/batch y persistencia por llamada a `.fcproj`. La herramienta también documenta revisión de cortes/congelados/negros, selección de tomas y exportación OTIO/XML. El CLI anuncia más de 650 comandos. Son capacidades del producto ajeno, no evidencia de compatibilidad o estabilidad en esta máquina.

## Auditoría acotada del código MCP

Además del README/manifest se leyó `src/index.ts`, `src/cli.ts` y `src/app.ts` en el commit fijado. `execFile` lanza el CLI sin shell; los tiempos tipados de wrappers se convierten a ticks. `run_command` admite cualquier `id`/parámetros y guarda por defecto, `run_batch` ejecuta IDs genéricos, y `ffmpeg_run` acepta argumentos crudos añadiendo `-y`. Las rutas se normalizan a absolutas, pero el MCP no aplica un allowlist de raíz de proyecto. El proceso hijo hereda el entorno; el timeout de ejecución genérica no tiene límite por defecto. El puente vivo usa token/puerto y abre otra ventana cuando `launch=true`; desconectar MCP no cierra la app.

Esto hace viable reutilizar sus wrappers tipados como referencia, pero integrar el MCP directamente sin capa OPENMONTAGE aumentaría el alcance de escritura y ejecución. Cualquier puente futuro debe imponer allowlist local de comandos/rutas, revisión e identidad, deadlines, copia/recovery y recibo; `readOnlyHint` o una descripción de herramienta no reemplazan enforcement.

OPENMONTAGE ya comparte proyecto EDL, revisión optimista, historial/deshacer, edición por Studio/agente, previsualización/exportación FFmpeg y QA local acotada. #174 ya cubre rampas, keyframes de capas, color, audio y transiciones en los alcances registrados. Por tanto, instalar un segundo editor/renderer duplicaría la superficie de edición y no conectaría automáticamente el MCP al puente local de OPENMONTAGE.

La diferencia más concreta es intercambio: `.fcproj` es JSON con esquema versionado (actualmente `schema_version: 18`); no es nuestra EDL ni un intercambio sin pérdidas. La documentación upstream dice que ciertos títulos no sobreviven a FCP7 XML y que en OTIO se guardan como metadata propia. El CLI MCP y el puente GUI también tienen semánticas de guardado distintas. No escribir directamente `.fcproj`, no editarlo mientras esté abierto en FilmCraft y no asumir que un lock de archivo coordina la caché de otra aplicación.

El camino `npx`/npm del MCP necesita paquetes disponibles y conectividad en la preparación inicial; solo podría operar después sin red si runtime, CLI y dependencias ya estuvieran instalados. No hay coste obligatorio por uso indicado para estos componentes, pero Windows offline, primera instalación y compatibilidad local no están acreditados aquí. Se excluye cualquier modelo/servicio de pago y no se inicia una instalación.

## Decisión y trabajo reutilizable

**No adoptar el editor ni el MCP completo ahora.** No se encontró una carencia que justifique un segundo EDL, renderer o proceso GUI, y el MCP está pensado para Claude Code, no para nuestro puente nativo. Reutilizar únicamente patrones/criterios compatibles con las entregas existentes:

1. Extender E06 con un adaptador OTIO opcional y explícito, si un destino real lo requiere: exportar primero una copia, fijar versión/timebase, validar IDs/rutas y producir un informe de campos omitidos; importar solo como candidato separado. Criterio: round-trip de fixture neutral preserva clips/tiempos/orden dentro de tolerancia declarada, informa títulos/efectos no soportados y nunca reemplaza el original.
2. Extender E10 con el patrón de comandos tipados, identidad de proyecto y revisión requerida; mantener enforcement local del allowlist, no ejecutar `run_command` genérico sin contrato. Criterio: fixture de comando desconocido/ruta externa/revisión obsoleta rechazada sin escritura y una acción válida produce el mismo recibo por Studio/agente.
3. Reutilizar ideas de `check-render` solamente donde no dupliquen QA existente; distinguir mediciones (duración, decodificación, audio presente) de heurísticas (negro/congelado) e intención editorial. Criterio: falsos positivos intencionales conservados y evidencia con medio/hash/intervalo; no decidir cortes automáticamente por score.

Las tres propuestas son ampliaciones de **E06/E10/QA existente**, no nuevos grupos de backlog. Antes de cualquier piloto posterior: confirmar necesidad concreta de intercambio, fijar artefacto y sumas oficiales, auditar licencia de dependencias/recursos del paquete y usar una copia de proyecto con ownership único. No se recomienda traer marcas/fonts/media de upstream sin revisar sus licencias específicas.

## Límites y validación de esta evaluación

- Revisados metadatos, `README`, `LICENSE`, `package.json`, `src/index.ts`, `src/cli.ts`, `src/app.ts`, release assets y documentación de proyecto/puente de los repositorios oficiales indicados.
- Versiones fijadas arriba; el SHA de release procede del metadato oficial y no fue recalculado porque no hubo descarga.
- Prueba local documental: verificar enlaces anclados, longitudes/checksums declarados, versiones, licencias, ausencia de lenguaje que afirme instalación/compatibilidad ejecutada y referencia a E06/E10 sin duplicar grupos.
- No se inspeccionaron instalaciones locales de FilmCraft, no se compiló, no se inició CLI/MCP/GUI, no se hizo import/export/render y no se evaluó rendimiento o compatibilidad audiovisual.
- Costo $0; configuraciones, proyectos, `.venv`, ComfyUI y PR #2 sin cambios. PR #2 permanece draft y sin merge.

## Referencias oficiales

- [FilmCraft MCP, revisión fijada](https://github.com/kanishk-gangwar/filmcraft-mcp/tree/2a67c359b52b1166035b34b79a40b0044199c322)
- [Licencia MIT del MCP](https://github.com/kanishk-gangwar/filmcraft-mcp/blob/2a67c359b52b1166035b34b79a40b0044199c322/LICENSE)
- [Dependencias y engines del MCP](https://github.com/kanishk-gangwar/filmcraft-mcp/blob/2a67c359b52b1166035b34b79a40b0044199c322/package.json)
- [README del MCP](https://github.com/kanishk-gangwar/filmcraft-mcp/blob/2a67c359b52b1166035b34b79a40b0044199c322/README.md)
- [Release FilmCraft v0.20.1 y hashes](https://github.com/storytold/filmcraft/releases/tag/v0.20.1)
- [FilmCraft: licencia MIT](https://github.com/storytold/filmcraft/blob/7b8e522d63f2e2c1617dea4939feb48e769d6f2f/LICENSE-MIT) · [Apache-2.0](https://github.com/storytold/filmcraft/blob/7b8e522d63f2e2c1617dea4939feb48e769d6f2f/LICENSE-APACHE)
- [Licencia separada de marcas](https://github.com/storytold/filmcraft/blob/7b8e522d63f2e2c1617dea4939feb48e769d6f2f/docs/brand/LICENSE-brand.txt)
- [Formato `.fcproj` y compatibilidad](https://github.com/storytold/filmcraft/blob/7b8e522d63f2e2c1617dea4939feb48e769d6f2f/docs/project-files.md) · [protocolo de control](https://github.com/storytold/filmcraft/blob/7b8e522d63f2e2c1617dea4939feb48e769d6f2f/docs/control-protocol.md)

