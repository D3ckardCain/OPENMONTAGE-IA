# Identidad y compatibilidad de Studio — #105, E01/E02

Seguimiento de #92 y de `04898cf`, sin repetir evaluaciones. El endpoint
`GET /api/studio/identity` permite al usuario y al agente consultar la misma
identidad. Solo lee código local acotado, no modelos, configuraciones o GitHub.

## Contrato

- `api_protocol:1`, `schema_version:1`; capacidades del editor conservan
  `version:3.0`, commands/render_cancel/shared_revision y añaden backend_build.
- `resident` es SHA256 de fuentes al importar el módulo, junto con PID y hora
  de carga; `disk` es la huella actual del mismo conjunto. El origen es
  `source_sha256_at_import`: **no es un commit Git ni prueba criptográfica del
  bytecode ejecutado**. Este workspace ZIP no tiene `.git`. La huella identifica
  backlot/*.py, lib/studio*.py y production_studio.py, no todo el repositorio.
- Huella por contenido y nombre relativo, sin depender solo de mtime/tamaño.
  Archivos ausentes, ilegibles o >2MB producen identidad no verificable.
  Un cambio fuera del conjunto declarado no se atribuye a esta detección.
- Capabilities se capturan al importar, no se reconstruyen desde código nuevo
  en disco por cada petición. Ambas rutas comparten identidad; las respuestas
  devuelven copias del catálogo para evitar mutaciones accidentales.
- `/studio` incorpora la huella del conjunto UI en un meta. Identidad y HTML
  usan no-store; los recursos ya tenían revalidación no-cache. El protocolo de
  compatibilidad del módulo y las capacidades deben coincidir.

## Uso y avisos

Al abrir Studio, al volver a la pestaña y con **Volver a comprobar**, se consultan
solo identidad y capacidades, con límite4s y sin reintentos. No hay polling ni
reinicio, instalación, actualización o descarga. Comprobaciones solapadas no
permiten que una respuesta anterior sustituya la más reciente.

| Caso | Resultado visible |
|---|---|
| Identidad404 | Instancia anterior al contrato: aviso de reinicio manual cuando no haya trabajos activos |
| Fuente residente diferente de disco | Reinicio manual necesario para cargar código; no se ejecuta desde el aviso |
| Página sin meta o huella UI anterior, backend compatible | Recargar la página; no pedir reinicio del servidor por un cambio solo de UI |
| Protocolo/capacidades/identidad incompatibles | Aviso de incompatibilidad y copia coherente; sin enviar cambios desde el editor |
| Timeout, error HTTP o JSON, archivo ilegible | No verificable; no afirmar backend antiguo ni inventar causa de red |
| Comprobación posterior compatible | Se retira el aviso y recuperan capacidades sin copiar ni recrear el proyecto |

El editor bloquea sus escrituras/importaciones mientras no esté verificada la
compatibilidad; las lecturas del proyecto siguen disponibles. La cancelación
de render anunciada por el backend conserva su camino existente. No es una
barrera de seguridad ni cambia permisos: otros clientes/agentes deben consultar
el contrato antes de editar; no se exige un header nuevo que rompa sus llamadas.

## Verificación focalizada y límites

Pruebas nuevas Python: identidad/capacidades/HTML no-store, fuente modificada
sin relabelar residente, recursos ignorados, archivos ausentes/ilegibles y límite.
Pruebas Node: compatibilidad, protocolos/catálogos distintos, legacy, página
vieja, errores/JSON, timeout, cancelación disponible y aviso/recheck/recuperación
con DOM sintético. No son prueba de ventana local ni reproducción audiovisual.

Se reutilizan `.venv` y el pytest ya presente en `.runtime/qa/venv` mediante
sys.path del proceso; no se instalan paquetes ni se cambian los entornos.
Pruebas Node usan el ejecutable preparado del entorno de Codex, sin tocar Node
registrado en aplicaciones. Las suites previas y capturas HTTP no se repiten.
La activación en el servidor4750 se informa por separado: no se reinicia aquí.
Un servidor legacy no adquiere esta API hasta su reinicio manual.

Resultado local de esta entrega: **4 pruebas pytest aprobadas**, incluyendo el
wrapper que ejecuta **7 casos Node nuevos**. Parseo AST de los módulos Python
modificados aprobado. No suite completa ni CI repetida. Advertencia previa de
pytest-asyncio sobre scope por defecto visible, no error ni prueba omitida.
Dos GET acotados al servidor activo: identity404 y capabilities200/version3.0
sin identidad nueva; confirma que la API nueva **no está activada** allí. No se
reinicia ni se afirma visto el aviso en su ventana. La recarga del frontend
nuevo puede mostrar el aviso legacy, pero requiere comprobación visual posterior.

No se declara resuelto el diagnóstico de cortes HTTP. Configuraciones,
proyectos/originales, ComfyUI, GitHub Dark y PR#2 en borrador se conservan.
