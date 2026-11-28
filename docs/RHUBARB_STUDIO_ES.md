# Rhubarb en Studio

Studio registra Rhubarb como aplicación CLI mediante el mecanismo existente de Aplicaciones. Guarda la ruta de `rhubarb.exe` o `rhubarb`, conservando la carpeta `res/sphinx` distribuida junto al ejecutable. FFprobe se configura mediante las herramientas de medios de Studio. El diagnóstico usa la ruta registrada y también admite un ejecutable disponible en PATH cuando falta configuración explícita.

## Herramientas del agente

El registro descubre `rhubarb_doctor` y `rhubarb_lip_sync` en la capacidad `character_animation`. Ambas son herramientas locales de costo cero. El agente consulta `list_tools`, lee `tool_info` y las instrucciones de su etapa antes de usar `execute_tool`.

El diagnóstico se ejecuta con

```json
{"name":"rhubarb_doctor","inputs":{}}
```

Devuelve la versión nativa, las huellas SHA256 del ejecutable y sus recursos y la disponibilidad de FFprobe. Su consulta nativa utiliza únicamente `--version`. La disponibilidad del diagnóstico significa que el agente puede consultar el estado de la instalación. Los errores de instalación se devuelven en `success=false` y `error`.

La llamada de análisis, para una etapa de producción autorizada posteriormente, tiene esta forma

```json
{
  "name":"rhubarb_lip_sync",
  "inputs":{
    "project_id":"mi-proyecto",
    "audio_path":"assets/audio/dialogo.wav",
    "language":"es",
    "output_path":"assets/audio/dialogo-mouth-cues.json",
    "timeout_seconds":300
  }
}
```

El agente debe usar el identificador de su proyecto. Las entradas y el informe se resuelven dentro de él, incluyendo enlaces simbólicos. El JSON de salida se publica en una ruta nueva de `assets/`, `artifacts/` o `workspaces/`. Una ruta ocupada produce un error para conservar el resultado anterior. La publicación final utiliza un enlace de archivo atómico y requiere un sistema de archivos que lo admita, como NTFS.

## Idiomas y formatos

La documentación oficial asigna PocketSphinx al diálogo inglés y el reconocedor fonético a otros idiomas. El segundo reconoce sonidos y sílabas con independencia del idioma, con precisión generalmente menor. El adaptador usa PocketSphinx para códigos `en` y `eng` y fonético para los demás. `recognizer` permite elegir explícitamente `phonetic` o `pocketSphinx`; se rechaza PocketSphinx para un idioma declarado diferente del inglés. [Documentación oficial de reconocedores](https://github.com/DanielSWolf/rhubarb-lip-sync/tree/v1.14.0#recognizers).

Se admiten WAV y Ogg Vorbis. El campo opcional `dialog_path` permite aportar un texto ASCII o UTF-8 conforme a la opción oficial `--dialogFile`. Ese texto puede ayudar al reconocimiento de palabras. El JSON nativo contiene intervalos en segundos y formas A–F, con G, H y X adicionales. Estas formas requieren dibujos o un rig correspondiente para convertirse en animación. [Opciones y formatos oficiales](https://github.com/DanielSWolf/rhubarb-lip-sync/tree/v1.14.0#command-line-options).

El idioma es declarado por el usuario. La selección fonética permite procesar grabaciones de otros idiomas, pero la precisión por idioma, acento o voz requiere evaluación adicional con material autorizado.

## Salida y procedencia

Se reutiliza `AudioProbe` para comprobar el medio. El proceso nativo recibe copias temporales de las entradas para que los hashes registrados correspondan a los bytes analizados. El informe conserva `metadata`, `mouthCues`, la versión del generador y `provenance` con rutas relativas, tamaños, hashes de audio y texto, idioma, reconocedor, huellas del ejecutable y recursos y momento de creación UTC. También registra la duración de FFprobe y la huella del JSON nativo. `metadata.soundFile` se normaliza a la ruta del audio original dentro del proyecto.

Los intervalos se validan como números finitos y ordenados, sin superposición y dentro de la duración informada. Las claves admiten las nueve formas documentadas. El agente recibe un resumen, una vista previa de diez claves y la ruta y huella del informe completo, para respetar su límite de transporte. `animation_generated=false` indica el alcance del resultado.

Los archivos de audio se limitan a 512 MiB y los textos a un millón de bytes. El tiempo predeterminado es 300 segundos y admite entre 1 y 3600. Un cambio del ejecutable o sus recursos durante el proceso invalida la publicación. Los errores distinguen instalación, recursos, FFprobe, entradas, tiempo agotado, fallo nativo, salida inválida, cambio del runtime y destino ocupado mediante prefijos `RHUBARB_*`.

## Validación realizada

Las pruebas utilizan archivos sintéticos y un proceso nativo simulado, con el adaptador, el registro y el puente del agente reales. Cubren selección de reconocedor, procedencia, controles de salida, errores, rutas de proyecto y publicación concurrente. La comprobación nativa real se limita al diagnóstico de versión y recursos. El análisis de grabaciones reales, la precisión de la sincronización y su aplicación a un rig quedan pendientes de validación.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/tools -p test_rhubarb_integration.py -v
```
