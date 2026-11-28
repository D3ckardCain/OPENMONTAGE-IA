# Idioma declarado de subtítulos — #109, E04

Siguiente entrega tras confirmación humana de la muestra portuguesa #107.
No se repite esa muestra, ASR, escucha, render ni suites previamente aprobadas.
**La prueba española continúa pendiente** y #107 permanece abierto por ella.

## Qué cambia

El exportador seleccionable mov_text tenía `language=spa` fijo. Ahora toma
`edit_decisions.subtitle_style.language`, compartido por Studio y el agente.
La operación `subtitle_style` conserva size/position/mode y acepta language
opcional. Declarar lengua no detecta, traduce, transcribe o reescribe los cues.

En Subtítulos, elegir **Idioma declarado de subtítulos** y aplicar estilo.
Nuevo capability `subtitle_language` evita presentar ese control como disponible
en un backend anterior. El aviso de identidad #105 debe señalar código pendiente
de activación; no se reinicia automáticamente el servidor.

Valores de esta entrega: und(sin determinar),spa,por,eng,fra,deu,ita,jpn,kor,zho,
rus,ara,hin. Son etiquetas admitidas por este selector/contrato, no una promesa
de ASR/TTS/traducción para esas lenguas. No aceptar códigos libres, argumentos,
dos letras o valores desconocidos: error explícito y rollback.

Ejemplo de comando del agente por la herramienta/API existentes:

```json
{"operation":"subtitle_style","revision":12,"size":32,"position":"bottom","mode":"soft","language":"por"}
```

## Compatibilidad y persistencia

- Proyectos nuevos: language und; no declarar español por defecto.
- EDL antiguo sin language: no migrar ni modificar en lectura/render. Se conserva
  **solo por compatibilidad histórica** la etiqueta spa anterior en un futuro
  soft export; el selector muestra «Sin declarar: etiqueta heredada spa; confirmar».
  No significa lengua detectada. Para corregirla hay que declarar explícitamente.
- Un comando antiguo sin language conserva la declaración ya guardada; si no
  había ninguna, mantiene ese estado heredado. No borra por omitir el parámetro.
- Undo/redo/guardar/reabrir comparten el estado normal del EDL. La lengua forma
  parte de su identidad de render; cambiarla invalida el resultado anterior para
  futuras exportaciones, sin borrar el archivo.
- Burn conserva la declaración en el proyecto pero no crea pista seleccionable
  ni metadato de idioma de subtítulos donde no existe esa pista. SRT no transporta
  por sí solo una declaración de lengua; el campo no traduce su contenido.

## Validación focalizada nueva

**16 pruebas pytest aprobadas**: contrato/API del agente,persistencia/undo/reopen,
ausencia de traducción,herencia/rollback,códigos inválidos y ensamblado real del
comando del worker con exportación simulada explícita. Incluye1wrapper de2casos
Node del selector y **3 muxes FFmpeg sintéticos nuevos de0.4s** (64×64 negro,
texto de prueba), cuyos tags por/eng/und se leen con FFprobe. Estos contenedores
no usan la muestra portuguesa ni certifican UX/AV de una producción real.

La prueba heredada mantiene spa sin modificar el proyecto. No se repiten suites
aprobadas. Sintaxis Python/JS revisada; sin dependencias nuevas, inferencias,
pesos, configuraciones o cambios ComfyUI.

Activación del nuevo capability/código en Studio abierto **pendiente**: no se
reinicia ni se afirma que editar disco cambie el proceso residente. #109 queda
abierto para esa activación; PR#2 permanece en borrador, sin merge.
