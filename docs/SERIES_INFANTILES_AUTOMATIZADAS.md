# Series infantiles automatizadas
Actualizado: 2026-11-13.

## Alcance autorizado y estado
Diseño preparatorio; no se ha instalado, probado ni integrado esta cadena.
Sin generación ni renders en esta fase. Costo operativo objetivo USD 0, local,
sin tarjetas, trials ni APIs de pago. No se promete automatización integral ya disponible.
Preparar series diferentes para 2–4, 5–7 y 8–12 años. Evaluar 2D, 3D y mixto con
la misma escena de muestra antes de escoger, cuando el usuario autorice producción.
No confundir tres públicos con tres estilos necesariamente aprobados.

## Reutilización sin trabajo manual por episodio
Cada serie tendrá biblia propia, identidad visual, protagonistas, voces por idioma,
escenarios y biblioteca de acciones versionados. Los personajes se preparan una vez,
incluyendo vistas, proporciones, colores, articulación, expresiones y bocas.
No regenerar al protagonista desde cero en cada plano.
La preparación inicial requiere desarrollo y revisión; no es un proceso resuelto
con la descarga de modelos. El objetivo del usuario es dirigir y aprobar, no editar
diariamente en aplicaciones.

## Biblioteca inicial propuesta (todavía sin clips)
| Familia | Acciones |
|---|---|
| Reposo y atención | idle, mirar a un objetivo, escuchar, parpadear |
| Locomoción | caminar, correr, girar, detenerse |
| Interacción | saludar, señalar, tomar, sostener, entregar |
| Postura | sentarse, levantarse, agacharse |
| Emoción | alegría, sorpresa, tristeza suave, duda |
| Diálogo | hablar, escuchar y turnarse, con labios sincronizados |

Estos nombres son requisitos, no identificadores de acciones ya existentes.
Cada acción necesita rig compatible, versión, duración nativa, rango de velocidad,
bucle/no bucle, desplazamiento raíz, contactos con suelo/objetos, capas corporales,
condiciones de entrada/salida y licencia/procedencia.
Separar acciones de locomoción, gestos, mirada y boca para combinarlas sin sobrescribir
todas las articulaciones. Adaptar animales y personajes no humanoides por separado.
No asumir que un mismo clip se puede transferir sin ajustes a cualquier personaje.

## Guion a movimiento: contrato propuesto
Cada intervención enlazará personaje, texto, idioma, audio y duración medida.
Cada acción enlazará personaje/rig, clip y versión, inicio/fin, objetivo, trayectoria,
objeto si aplica y transición. Referencias inexistentes deben dar error visible.
Programar gestos según la voz obtenida; no acelerar voz o animación arbitrariamente
para forzar duraciones. El doblaje inglés requiere recalcular tiempos y bocas.
Usar variantes compatibles para evitar repetición mecánica, conservando estilo.
Los casos sin cobertura deben quedar pendientes de un recurso nuevo, nunca
sustituirse silenciosamente por planos estáticos.

## Herramientas candidatas y descargas comunicadas
| Herramienta | Función y límite | Estado |
|---|---|---|
| Krita 5.3.4.1 portable | Dibujos y capas; no es director automático | Enlace comunicado; descarga local sin verificar |
| Blender 4.5.15 portable | Escenas, rigs, cámaras, scripting y render | Enlace comunicado; sin prueba local |
| Rigify | Generación de controles; no crea por sí solo actuación o modelo | Incluido en Blender 4.5; no duplicar descarga |
| Rhubarb Lip Sync 1.14.0 Windows | Audio a tiempos de boca; requiere adaptador | Enlace comunicado; sin prueba local |
| Qwen / modelos de imagen existentes | Guion, bocetos y recursos de apoyo | Integración y calidad pendientes |
| Qwen TTS / Kokoro | Voces candidatas ES/EN | Voz, licencia e integridad por comprobar |
| ACE-Step / MOSS | Música y efectos candidatos | Sin integración probada |

Rhubarb: usar reconocedor phonetic para español y pocketSphinx como candidato inglés;
su modo fonético puede ser menos preciso. El mapeo de formas de boca a controles 3D
o dibujos 2D todavía no está implementado. No automatiza expresiones faciales completas.
Conservar avisos de licencia de herramientas y auditar por separado cada personaje,
clip, música, voz y recurso externo. No usar personajes comerciales ajenos como identidad.

### Descargas de referencia
- Krita: https://download.kde.org/stable/krita/5.3.4.1/krita-x64-5.3.4.1.zip
- Blender: https://mirror.blender.org/release/Blender4.5/blender-4.5.15-windows-x64.zip
- Rhubarb: https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Windows.zip
Destino de archivo: D:\OPENMONTAJE-IA\DESCARGAS_SOFTWARE\, subcarpetas Krita,
Blender y Rhubarb-Lip-Sync respectivamente. Los enlaces no prueban integridad local.
No se ha identificado otra descarga obligatoria en esta fase.

## Integración futura y calidad
Auditar primero los recursos y herramientas de character-animation existentes;
reutilizar contratos y persistencia sin construir un orquestador paralelo.
Leer manifiestos y directores antes de cualquier producción y elegir runtime
según disponibilidad comprobada. Blender es candidato de animación/render, no
sustitución automática de un runtime aprobado en una producción.
Criterios de muestra: identidad estable, actuación legible, labios ES/EN,
contactos y agarres coherentes, ausencia de interpenetraciones, sonido inteligible,
encuadre para plataforma y continuidad entre planos. Revisiones automáticas
detectan fallos técnicos; no demuestran atractivo infantil ni sustituyen evaluación
editorial y opinión de familias sobre los pilotos.
El contenido para cada edad debe evitar instrucciones peligrosas imitables y adecuar
lenguaje, intensidad emocional y complejidad narrativa.

## Trabajo restante, en orden
1. Inventariar rigs/acciones existentes y contrastarlos con esta biblioteca propuesta.
2. Definir contratos y adaptadores de voz, boca, rig y escena.
3. Preparar un personaje y una escena comparables en los tres estilos.
4. Cuando se autorice: validar una cadena completa local antes de producir en lote.
5. Comprobar repetibilidad entre episodios y aprobar identidad por serie.
La publicación automática y su política de revisión quedan pendientes.
