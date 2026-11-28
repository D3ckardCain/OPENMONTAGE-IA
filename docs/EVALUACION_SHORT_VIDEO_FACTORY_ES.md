# Short Video Factory — evaluación #84

24-11-2026, #3. Identificación candidata por nombre/captura, no identidad visual certificada. [YILS-LIN/short-video-factory](https://github.com/YILS-LIN/short-video-factory/tree/4e58116fd98cac2526e134237b57db8f01aed79f), package **1.4.1**; README/README.en, LICENSE, package.json y src/lib/batch.ts revisados estáticamente.

AGPL-3.0 del código: conservar avisos/código correspondiente y evaluar obligación de oferta de fuente a usuarios de versiones modificadas por red. No copiar código a Studio asumiendo MIT; ideas/contratos pueden estudiarse sin importar implementación. Footage, fuentes, modelos, FFmpeg y servicios no heredan AGPL ni derechos de reutilización por aparecer en la app.

Windows/macOS/Linux declarados; app Electron con source **Node>=22.17.0/pnpm>=10.12.4** (packageManager10.12.4). `preinstall` usa npx y `postinstall` script propio: no ejecutar. FFmpeg/recursos empaquetados y dependencias deben comprobarse por plataforma. RAM/VRAM/disco no certificados para nuestra laptop: lotes y codecs/concurrencia determinan carga; no extrapolar un preset.

Aunque anuncia localización de datos, texto usa interfaz OpenAI-compatible y voz **EdgeTTS online**. No prueba Ollama compatible extremo a extremo ni audio offline. Créditos cloud/promociones no son operación permanente$0. Render con assets locales puede ser local si todos los recursos están preparados; metadatos/proveedores de red son otra ruta. No instalar Electron/servicios ni sustituir voz existente por Edge.

## Comparación

MoneyPrinterTurbo#62 y E03/E04/E05/E06 ya cubren lotes, asociación guion/recursos y variantes. El batch helper no acredita durabilidad, cancelación de backend ni reanudación completa de todos los exportadores. Studio/director/recibos y TTS/ASR existentes siguen siendo base; no otra UI/director ni descargador.

| Grupo | Carencia acotada y aceptación futura |
|---|---|
| E06 | Preset versionado separa intención (ratio, estilo, duración, voz) de paths/secretos y herramienta concreta. Fixture JSON migra versión conocida y rechaza desconocida, recurso sin derechos o referencia ausente. Guion/footage/voz/cues enlazados por IDs/hash. |
| E05 | Matriz de variantes con parámetros/dependencias y estado individual. Mock de fallo en variante2 conserva variante1, permite reanudar sin repetirla; cambiar voz/guion invalida solo derivados. Cancelación no promociona parcial. |
| E04/E03 | Español con palabras/cues íntegros y selección candidata trazable; preset vertical no prueba seguimiento facial. Separar inferencia simulada de llamada real. |
| B04/B07 | Reutilización de código AGPL, paquetes Windows, proveedores y derechos pendientes; ninguna dependencia cloud obligatoria aceptada. |

No necesidad de nuevo grupo: se precisa aceptación de E05/E06. Calidad española, render, memoria y compatibilidad Ollama quedan sin probar. Evaluación completada sin instalar, modelos, inferencia, contenido ni cambios de configuración.
