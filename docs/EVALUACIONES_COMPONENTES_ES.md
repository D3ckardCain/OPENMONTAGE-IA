# Evaluaciones de componentes #44–#46

24-11-2026 UTC. Se completaron una por una mediante lectura de fuentes oficiales y
código local. No son instalaciones, pruebas audiovisuales o aprobación de adopción.

| Evaluación | Qué conviene aprovechar | Qué conservar de OPENMONTAGE | Primeras tareas |
|---|---|---|---|
| [PeakCut #44](EVALUACION_PEAKCUT_ES.md) | Límites por frase, ASS opcional y buffer durable de directos | Agente Ollama, ASR español local, karaoke/reencuadre y cola existentes | Contrato trazable de candidatos y puente words; después captura acotada |
| [Taste Skill #45](EVALUACION_TASTE_SKILL_ES.md) | Comprobaciones pequeñas de accesibilidad y presupuestos de panel | GitHub Dark, densidad, HTML/JS y pytest/Playwright actuales | Contraste del botón verde, teclado, mensajes y responsive; sin hooks ni gate externo |
| [OpenReel #46](EVALUACION_OPENREEL_ES.md) | Modelo de editor multipista/undo y puente MCP acotado | Director, checkpoints, procedencia, ASR y export actuales | Intercambio de JSON, doctor MCP simulado y condiciones de licencia antes de instalar |

Los informes detallan fuentes fijadas, dependencias, licencias y aceptación por tarea.
No se copia código externo ni se cambia UI, configuración, entorno, modelo o aplicación.
Prioridad común: español original y herramientas locales ya preparadas, costo$0.

Condiciones de implementación: no duplicar ASR; no permitir descargas/fallback cloud
por defecto; respetar las aprobaciones del pipeline y las restricciones de navegador.
Un preview o proyecto JSON no acredita render. MIT raíz no cubre todas las dependencias:
GSAP/Mediabunny/FFmpeg y pesos requieren su tratamiento específico. PR#2 sigue borrador,
sin merge. Las tareas descritas siguen pendientes, aunque sus evaluaciones estén cerradas.
