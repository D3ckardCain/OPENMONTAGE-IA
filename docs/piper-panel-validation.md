# Validación del panel Piper y activación agrupada (#111)

Fecha: 2026-11-25. Código: `dfb8e15ad5bbfeace9c16105f238a688955221f6`.

Este informe conserva la prueba inicial, cuando VCTK antiguo estaba bloqueado.
La sustitución autorizada posterior y su validación están en
[PIPER_VCTK_RETRAIN_ES.md](PIPER_VCTK_RETRAIN_ES.md); sus resultados actualizan
el estado de VCTK, sin repetir las cuatro combinaciones españolas aquí aprobadas.

## Activación pendiente

El servidor 4750, PID 89172, responde salud pero informa `restart_required=true`:
resident `a68d1acb6b9aea6288bc57aa38beb20399647f53139b001b0d5ebff157df58a4`,
disk `87537bbe00c469a9f1dce503700f9296fa6c326551966a3df639667d3519253e`.
La cola está pausada, sin elementos, `worker_active=false`,
`local_task_active=false`; tampoco hay registros JSON de trabajos en ejecución.

Se preparó una única activación de #108, #109 (`45b8609`), #110 y #111.
La política de la sesión rechazó el comando de detener/iniciar Studio antes de
ejecutarlo. No se probó otro método para eludirla y 4750 permanece intacto.

Paso manual: en la consola que ejecuta Studio, pulsar Ctrl+C y esperar su salida.
Si no termina, cerrar únicamente esa consola de Studio. Después, desde PowerShell:

```powershell
Set-Location -LiteralPath C:\OPENMONTAGE-IA
& .\.venv\Scripts\python.exe -B -m backlot serve --port 4750
```

Tras arrancar, recargar el panel. Falta verificar identidad coherente, API y
preescucha en **4750**; no se confunde con la prueba aislada descrita abajo.
Las configuraciones existentes de aplicaciones/settings se compararon antes y
después y permanecen idénticas. ComfyUI y sus entornos no fueron modificados.

## Prueba real de interacción y reproducción

Servidor aislado 4751, misma copia/código y proyecto QA `edit-635e36b5107a`.
Chrome instalado, Playwright existente, sin instalaciones. Se abrieron Audio y
Voces locales Piper, se consultaron/selectaron voz y hablante, se pulsó Crear
preescucha y se reprodujo cada WAV hasta `ended=true`.

| Voz | Hablante | Duración WAV | Frecuencia |
|---|---|---:|---:|
| Davefx | 0 | 2.426485 s | 22050 Hz |
| Carlfm | 0 | 2.128000 s | 16000 Hz |
| Sharvard | M=0 | 2.078186 s | 22050 Hz |
| Sharvard | F=1 | 2.321995 s | 22050 Hz |

Texto sintético: «Esta es una prueba breve de voz local.» Síntesis CPU real,
con red bloqueada. Reproducción HTML con `readyState=4`, duración y posición
final concordantes, sin error multimedia. Sin errores JS ni HTTP en las rutas
probadas. Selector Sharvard ofrece M=0/F=1 y conserva atribuciones CC BY 3.0 /
HiFiTTS CC BY 4.0. VCTK ofrece 109 hablantes y el botón permanece deshabilitado
con explicación de su base Lessac. Capturas inspeccionadas en 1920×1080:
selector, atribución, audio y controles visibles mediante desplazamiento interno.

Esto prueba interacción, síntesis y decodificación/reproducción del navegador;
no acredita escucha humana, inteligibilidad ni calidad perceptual. Los WAV y
recibos permanecen solo en el proyecto QA. Evidencia local adicional:
`.runtime/piper/browser-results.json`, `panel-spanish.png`, `panel-vctk.png`.

Reproducción opt-in: `scripts/validate_studio_piper_ui.cjs` recibe URL loopback e
ID de proyecto de prueba; requiere Playwright/Chrome existentes mediante
`PLAYWRIGHT_MODULE` y `CHROME_EXE`. Crea cuatro preescuchas nuevas, no instala
dependencias, no modifica proyectos originales y no reinicia servidores.

## VCTK reentrenado: referencia identificada, sin descargar pesos

Revisión oficial fijada: `5ec43b186ef915a195d3ddbcfd9916e76c503c3f`.
[Artefacto ONNX oficial](https://huggingface.co/rhasspy/piper-voices/resolve/5ec43b186ef915a195d3ddbcfd9916e76c503c3f/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx)
identificado mediante metadatos LFS oficiales y HEAD (sin GET del modelo):

- Tamaño: **76972979 bytes**.
- SHA256 LFS oficial: `fc3d92d266b1a6c03af2a38215e0eee430ca7fb360f641d7c3dcb17c7670c0f3`.
- Commit del artefacto: `42301ec547bc2939386cf0ae9f9050ca05b1d3af`.
- [Tarjeta de esa revisión](https://huggingface.co/rhasspy/piper-voices/blob/5ec43b186ef915a195d3ddbcfd9916e76c503c3f/en/en_GB/vctk/medium/MODEL_CARD):
  HiFiTTS reader 92, Cori Samuel; MRD/SDP; Piper >=1.5; VCTK 0.92 mic1,
  109 hablantes, 22050 Hz; dataset CC BY 4.0. Mantener atribución de ambas bases.
- Tarjeta descargada como documento: 581 bytes, SHA256 calculado
  `ab7216e9aba1f493781c47fabab1078eeae2ea2b1ec29e41653249b007b959c0`.
- JSON de configuración de esa revisión: 8061 bytes, Piper 1.5.0,
  SHA256 calculado `8cc5a7678bf893c35cb6fde5d0812fb7e2b63e1eef54db250afd525277471f2d`.

El ETag HEAD usa identidad Xet y **no** se interpreta como SHA256 LFS.
El hash oficial identifica el artefacto remoto; no es una verificación de sus
bytes locales, pues aún no se dispone de una copia reentrenada comprobada.
En las carpetas de modelos/descargas y modelos de ComfyUI consultadas en D:
solo se encontró VCTK antiguo (76952753 bytes). E: contiene actualmente un
instalador de red (`RTK_NIC_DRIVER_INSTALLER.sfx.exe`), no `OPENMONTAJE-IA`.
F: sí presenta `OPENMONTAJE-IA`, pero su consulta quedó sin completar; no se
interpreta la demora como ausencia del artefacto ni se fuerza acceso al disco.
No se propone reemplazar automáticamente ONNX ni su JSON: primero hay que
localizar/comprobar el conjunto completo, mantener atribuciones y probarlo.
La copia antigua se conserva y continúa bloqueada. Sin descargas de pesos.
