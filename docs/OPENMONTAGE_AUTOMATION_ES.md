# Preparación de OPENMONTAGE-IA

## Operación con agentes
El productor ejecutivo interpreta el manifiesto y coordina agentes especializados:
investigación, guion, escenas, recursos, montaje, composición y publicación.
La coordinación sigue las instrucciones del repositorio; no se introduce un
orquestador Python que tome decisiones creativas. Se conservan checkpoints,
revisiones y límites de reintentos del manifiesto. Una autorización de ejecución
completa permite avanzar por las etapas autorizadas; publicar requiere la política
explícita del proyecto. Un fallo bloquea la etapa: no se inventan resultados.

## Herramientas integradas
- `youtube_research`: búsqueda oficial por idioma declarado, duración, vistas y
  suscriptores. Clave local `YOUTUBE_API_KEY`; no se guarda en GitHub. Shorts son
  candidatos por duración. No conoce ingresos, RPM ni monetización de terceros.
- `official_uefa_live`: consultas UEFA sin caché persistente. Cobertura beta,
  no representa todas las ligas, FIFA, CONMEBOL ni carreras completas de entrenadores.
- `cultural_audio_audit`: evidencia por idioma y tramo, validada en checkpoints
  de localización desde recursos hasta publicación. El agente escucha/inspecciona;
  el validador comprueba intervalos, cobertura y decisiones pendientes. No detecta
  canciones por sí mismo. Variantes de idioma se ejecutan como proyectos separados.

## Costo y modelos
Localización usa presupuesto predeterminado cero. El agente debe elegir solamente
herramientas locales disponibles; no sustituirlas por servicios de pago.
Los pesos descargados no prueban instalación ni funcionamiento. Antes de asignar
un modelo, verificar archivos, licencia de pesos, dependencias, VRAM y una muestra
real en el equipo destino. Ningún peso ni contenido privado entra en Actions.

## Estado y límites
Se preparan contratos y conectores, no se certifica producción audiovisual completa.
Pendientes: detección acústica y separación de pistas conectadas al runtime local,
pruebas GPU Windows, interfaz de configuración, integración editorial del explorador,
conectores de fútbol restantes y prueba de un video completo. UEFA continúa como
trabajo separado; no se considera terminado. Investigar fuentes para crear guiones
originales: traducir un video ajeno y cambiar su miniatura no concede derechos.

## Validación automática
Actions ejecuta las pruebas existentes y pruebas focalizadas Linux/Windows sin
credenciales, tráfico externo ni pesos. Las pruebas reales con GPU y APIs deben
ser explícitas y separadas; las pruebas simuladas no certifican esas conexiones.
