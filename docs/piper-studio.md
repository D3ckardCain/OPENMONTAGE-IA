# Piper local en Audio (#111)

Runtime aislado: Piper 1.8.0, Python 3.11.9, CPU; instalación binaria sin pesos.
No modifica `.venv`, ComfyUI ni sus configuraciones. Código Piper GPL-3.0-or-later;
las licencias de las voces son independientes. No redistribuimos pesos.

Configurar localmente `.backlot/studio/piper.json` con `python` (ejecutable del
entorno aislado) y `voices_root` (carpeta existente). No publicar este archivo.
Instalación reproducible en un entorno nuevo: `python -m venv <entorno>` y
`<python-aislado> -m pip install --only-binary=:all: piper-tts==1.8.0`.
La síntesis no instala ni descarga nada; verifica archivos contra el catálogo,
requiere >=1.5, bloquea sockets de red y utiliza CPU.

Audio → Voces locales Piper → Consultar voces → seleccionar voz y hablante →
escribir texto (máximo 1000 caracteres) → Crear preescucha local → escuchar.
Incorporar a biblioteca registra el WAV mediante el contrato compartido del
editor. Añadirlo a la pista usa los controles existentes, con deshacer/rehacer.
No hay proyecto privado del navegador. Cada WAV conserva un recibo JSON con
versión, hablante, duración, hashes, revisión y atribución; no sobrescribe archivos.

Agente: reutilizar `tools.audio.piper_tts.PiperTTS`, entradas `text`, `model`
(ID del catálogo), `speaker_id`, `output_path` nuevo dentro del proyecto.
Después registrar mediante `studio_project_edit`, igual que otros audios.
No se implementan clonación, traducción ni aprobación automática de calidad.

## Inventario y diferencia VCTK

Los cuatro paquetes existentes coinciden con la revisión oficial
`0ca208afc2a2ee102b1e961e72e0a7e4907be3d0` de
[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/0ca208afc2a2ee102b1e961e72e0a7e4907be3d0).
El catálogo `lib/piper_voices.json` registra tamaños, SHA256 locales y referencias.
ONNX coincide con SHA256 LFS oficial; tarjetas/configuraciones coinciden con
tamaño y Git blob SHA1 oficial. No se presenta ese SHA1 como SHA256 oficial.

Davefx: CC0 y base rdh CC0. Carlfm: dominio público, desde cero.
Sharvard: dataset CC BY 3.0 y base HiFiTTS CC BY 4.0, Cori Samuel, lector 92;
se conservan ambas atribuciones. Hablantes M=0 y F=1.

VCTK local es versión de configuración 1.0.0 y su tarjeta declara base Lessac.
Coincide con la revisión fijada, por tanto no es corrupción. Está bloqueado;
sus 109 hablantes se enumeran pero no se declaran probados ni habilitados.
La revisión oficial actual `5ec43b186ef915a195d3ddbcfd9916e76c503c3f`
contiene VCTK 1.5.0, base HiFiTTS, 76972979 bytes y SHA256
`fc3d92d266b1a6c03af2a38215e0eee430ca7fb360f641d7c3dcb17c7670c0f3`.
No se descargó ni sustituyó. Véase también la advertencia oficial de
[uso comercial](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/COMMERCIAL_USE.md).

## Evidencia y límites

Síntesis real offline, texto sintético breve: Davefx 4.261 s, Carlfm 3.616 s,
Sharvard M 4.029 s y F 3.611 s. WAV PCM creados en un proyecto QA independiente;
originales y configuraciones anteriores conservados. Los recibos guardan la
procedencia. Esto acredita ejecución por esos cuatro pares voz/hablante,
no validación auditiva de pronunciación, acentos ni calidad.

La API y controles requieren activar este código en Studio. Se agrupa con
#108–#110, sin reiniciar el servidor activo. Pruebas de contrato en proceso
no acreditan apariencia ni interacción en el panel activo anterior. Pendientes:
activación agrupada, prueba visual/preescucha humana e incorporación en el panel.
La muestra española de #107 continúa pendiente; no se repite la portuguesa.

Validacion focalizada: 7 pruebas de contrato aprobadas. Ademas, API real en
TestClient con sintesis Sharvard F (2.496 s), GET WAV RIFF, registro y reapertura
revision 1 del proyecto QA; herramienta del agente Davefx real (1.985 s).
No son mocks de sintesis. No se ejecuta de nuevo la suite completa ni CI previa.
