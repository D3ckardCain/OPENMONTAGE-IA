# Automatización local de vídeos con agentes

Actualizado: 12 de noviembre de 2026. **Diseño y requisitos; no implementado ni validado de extremo a extremo.**

## Objetivo acordado

Recibir una orden de campaña, por ejemplo: «Crear 48 vídeos sobre versículos bíblicos,
con movimiento real, música y narración en español e inglés; distribuirlos semanalmente
en las plataformas seleccionadas». Español es el idioma principal, inglés el segundo.
Las demás lenguas se añadirán según soporte y pruebas. El alcance incluye todas las
redes sociales objetivo; cada integración de publicación requiere su propia evaluación.

Costo operativo objetivo: USD 0. Sin tarjetas, pruebas temporales, suscripciones ni
APIs de inferencia de pago. Hardware y almacenamiento propios; electricidad solar.
La calidad y velocidad de las demostraciones comerciales son objetivos exigidos,
pendientes de medir con el hardware de producción. No se declaran alcanzados.

## Roles previstos

| Rol | Trabajo | Resultado revisable |
|---|---|---|
| Planificador | Divide campaña, idiomas, temas, calendario y formatos | Plan de campaña |
| Guionista | Redacta guion y comprueba fuentes/citas | Guion y referencias |
| Director | Planifica escenas, movimiento y motores locales permitidos | Plan de escenas |
| Productor | Solicita imágenes, clips, voces y música | Archivos y procedencia |
| Editor | Monta, sincroniza, mezcla y subtitula | Edición y exportaciones |
| Revisor | Evalúa audio, texto, coherencia y variedad; solicita correcciones | Informe por vídeo |
| Publicador | Gestiona calendario y adaptadores oficiales por plataforma | Estado y referencia de publicación |

Son responsabilidades lógicas; no son siete modelos que deban descargarse.
Un mismo LLM local, candidato Qwen3-8B, podría atender varios roles por turnos.
La suficiencia de ese modelo como director autónomo está pendiente de evaluación.
Los modelos visuales, de voz, música y transcripción son herramientas separadas.
La evaluación automática tampoco garantiza exactitud editorial, bíblica o estética.

## Producción y calendario

| Modo | Producción | Publicación |
|---|---|---|
| Anticipado | Generar los 48 antes de iniciar la campaña | Según calendario |
| Semanal | Generar el siguiente antes de su fecha | Según calendario |
| Reserva, recomendado | Mantener varios vídeos terminados y reponerlos | Según calendario |

Cantidad, número de versiones por idioma, frecuencia por plataforma, zona horaria y
fecha de inicio deben ser campos independientes. «48 vídeos en dos idiomas» puede
significar 48 versiones bilingües o 96 archivos separados; no asumirlo al ejecutar.
En la laptop RTX 4060 de 8 GB, planificar una tarea GPU pesada por turno; no prometer
que todos los candidatos caben o que alcanzan el ritmo requerido. Otros nodos podrían
trabajar en paralelo una vez implementados, medidos y autorizados.

## Integración con la aplicación existente

OpenMontage ya contiene manifiestos de pipeline, herramientas, revisión y checkpoints.
Esto no demuestra que exista un director local permanente, una cola de campañas o un
publicador autónomo. Respetar `AGENT_GUIDE.md`, `pipeline_defs/`, los contratos de
`lib/checkpoint.py` y el registro de herramientas. No introducir un flujo alternativo
que eluda las etapas de producción. El componente de calendario debe gestionar estado,
reanudación y herramientas; las decisiones creativas siguen los directores de etapa.

La autonomía futura debe registrar una política de autorización de campaña explícita
y acotada. No desactivar globalmente los puntos de aprobación ni interpretar una
conversación de diseño como autorización para publicar en cuentas reales. En la fase
actual no hay autorización para producir ni publicar: se documenta y descarga.

## Requisitos pendientes de implementación

1. Director LLM local, plantillas de roles y selección de herramientas de costo cero.
2. Cola persistente por campaña/vídeo/idioma/etapa, prioridades y exclusión de GPU.
3. Reanudación después de reinicios; reintentos limitados y conservación de resultados.
4. Identificadores estables por publicación; reconciliar estados inciertos antes de
   reintentar para evitar duplicados. No regenerar ni republicar todo tras un fallo.
5. Revisión de guiones, citas bíblicas, licencias de traducciones y música, duración,
   legibilidad de subtítulos, sincronización, variedad y coherencia audiovisual.
6. Adaptadores oficiales por plataforma: permisos, cuotas, formatos, etiquetas de IA,
   programación y elegibilidad. No asumir que todas ofrecen publicación gratuita
   equivalente ni recurrir a servicios de pago o evasión de límites.
7. Avisos ante permisos vencidos, bloqueo de cuenta, resultados dudosos o agotamiento
   de reserva; pausa por campaña, cancelación y registro de acciones.
8. Prueba física de un vídeo, sus idiomas y formatos; después una campaña pequeña
   recuperable antes de ampliar a 48 y activar publicaciones reales.

## Publicación, monetización y contenido con IA

Crear con IA no equivale automáticamente a rechazo. Publicar, ser recomendado y
monetizar son resultados diferentes. El contenido repetitivo producido en masa con
poco valor original puede ser inelegible para monetización o infringir reglas de spam.
Las escenas, voces o personas realistas generadas pueden requerir divulgación de IA.
No basta variar el versículo en una plantilla idéntica; aportar explicación y escenas
con valor propio. La automatización debe preservar esa variedad y autenticidad.

La licencia de un motor no concede derechos sobre biblias, música, imágenes o voces
de terceros ni asegura monetización. Seleccionar traducciones con permisos adecuados.
Las plataformas pueden cambiar condiciones: revisar nuevamente antes de implementar
cada publicador y antes de activar campañas. No se garantiza autonomía absoluta.

Fuentes oficiales consultadas el 12 de noviembre de 2026:

- [Monetización de YouTube](https://support.google.com/youtube/answer/1311392).
- [Respuesta de YouTube sobre contenido con IA](https://support.google.com/youtube/thread/356734251?hl=en).
- [Normas de spam de YouTube](https://support.google.com/youtube/answer/2801973).
- [Contenido generado con IA en TikTok](https://support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content).
- [Etiquetado y normas de Meta](https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/).

## Criterio de aceptación

Demostrar producción, recuperación tras fallo y publicación autorizada sin duplicados,
con todos los archivos presentes y los costos externos en cero. Registrar hardware,
versiones, tiempos reales, memoria, revisión por idioma y límites de cada plataforma.
La mera descarga de pesos no completa ninguno de estos criterios.
