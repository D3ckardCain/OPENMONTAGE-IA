# BgRemove local, E01 — #110

Entrega independiente de #107/#109, reutiliza la evaluación #94 y la herramienta
`bg_remove` existente. Versión0.2.0, runtimeLOCAL. No se instala rembg, no se
descargan/cargan pesos ni se procesan imágenes reales durante esta entrega.

## Contrato de ejecución

La llamada exige project_id,input_path,output_path,model,model_path,model_sha256
y license_review. Entrada/salida pertenecen al proyecto existente, dentro de
assets/source_images/thumbnails. La salida es un **PNG nuevo**, no el original
ni un archivo existente. No se elige cache, modelo o ruta por defecto.

Solo modelos explícitos u2net,u2net_human_seg,isnet-general-use. BRIA y cualquier
proveedor remoto/desconocido fallan antes de inferencia. Parámetros adicionales
desconocidos, matting no booleano y colores inválidos producen error.

license_review debe contener status reviewed, commercial_use yes,
requires_paid_agreement false, license_id,license_url,source_url,revision y
model_sha256 coincidente con la huella esperada del ONNX. Rechaza revisión
ausente,NC/desconocida/acuerdo pagado,huella de otro recurso y ramas flotantes.
Las referencias son HTTPS sin credenciales; no se visitan para ejecutar el tool.

**Es una declaración revisada del operador, no verificación jurídica externa**.
No escribir reviewed/yes por conveniencia: verificar el peso, conversión y uso
concreto antes de prepararla. MIT del wrapper no licencia el modelo. Esta entrega
no declara elegible ningún peso real ni autoriza BRIA comercial.

Ejemplo de forma del contrato, con placeholders **no ejecutables**:

```json
{
  "project_id":"PROYECTO_EXISTENTE",
  "input_path":"assets/original.png",
  "output_path":"assets/cutout-candidato.png",
  "model":"u2net",
  "model_path":"RUTA_ABSOLUTA_DEL_ONNX_REVISADO",
  "model_sha256":"SHA256_REAL_64_HEX",
  "license_review":{
    "status":"reviewed",
    "commercial_use":"yes",
    "requires_paid_agreement":false,
    "license_id":"LICENCIA_REVISADA_DEL_ARTEFACTO",
    "license_url":"https://FUENTE_FIJADA/LICENCIA",
    "source_url":"https://FUENTE_FIJADA/ARTEFACTO",
    "revision":"VERSION_O_REVISION_REVISADA",
    "model_sha256":"SHA256_REAL_64_HEX"
  },
  "alpha_matting":false
}
```

Un caso con licencia/uso desconocidos permanece bloqueado; no rellenar ese
ejemplo automáticamente desde el nombre de la carpeta o el badge de rembg.
La falta de fichero local no provoca descarga, migración de cache ni cambio a
otro modelo/proveedor. No se desactiva integridad como forma de recuperarse.

## Reutilización y ausencia de descarga implícita

Se reutilizan las sesiones de rembg para normalización/predicción. En lugar de
`new_session`, la clase seleccionada se deriva localmente con download_models
reemplazado por retorno del archivo **ya verificado**. No se llama al hook
upstream de descarga ni se cambian caches/variables globales del proceso.
CPUExecutionProvider explícito,2hilos intra/1inter; proveedor inesperado falla,
sin cambio silencioso de GPU/CPU o fallback cloud.

Contrato contrastado con fuentes fijadas en
[61fca30e68a34082da41bbe6197f07bee0a7d36b](https://github.com/danielgatis/rembg/tree/61fca30e68a34082da41bbe6197f07bee0a7d36b):
BaseSession llama a download_models antes de crear ORT; U2netSession,
U2netHumanSegSession y DisSession corresponden a los tres nombres admitidos.
Una versión instalada incompatible da error, no otro camino de carga.
Esto controla los hooks conocidos de esos proveedores, no es sandbox genérico
para ejecutar código arbitrario/no confiable de otros paquetes.

## Integridad, salida y procedencia

- SHA256 usa el lector acotado existente de Studio. Cache64entradas por ruta,
  device/inode/tamaño/mtime/ctime; misma identidad reutiliza el hash, modificación
  invalida. Una discrepancia bloquea antes de crear sesión.
- Preflight antes de proveedor y revalidación después de procesar, antes de
  escribir. Cambio de entrada/peso, salida aparecida o ruta alterada impiden
  publicar el resultado. Creación exclusiva xb evita sobrescribir una carrera.
- Resultado sin alpha falla; no se inventa máscara. Un fondo explícito de seis
  dígitos compone RGB; sin fondo se conserva imagen con alpha. No hay only_mask,
  lote o matting temporal de vídeo implementados por estas opciones.
- ToolResult devuelve entrada/salida/modelo con hashes,parámetros,dimensiones,
  modo,versión observada rembg y referencias de licencia vinculadas. El ledger
  del proyecto/agente puede conservar ese recibo; no se añade otro registro.
- Excepciones son resultados estructurados error_code. Si una escritura propia
  falla, no se publica artifact de éxito; un archivo parcial propio se identifica
  como unapproved_output, sin borrar originales o archivos ajenos.

El estado pasa a unavailable si faltan paquetes, o degraded si están presentes
pero falta el preflight por llamada. Importar rembg no declara un peso preparado.
No se instalan paquetes para cambiar ese estado. La API anterior que solo enviaba
input_path ahora recibe un error claro; debe proporcionar el contrato explícito.

## Pruebas y límites

**24 casos focalizados aprobados**, incluida la regresión de selección actualizada
al nuevo contrato:14fallos previos a inferencia,selección local sin factory/cache,
reutilización/invalidez de hashes,carreras de salida,cambios de entrada/peso,
fallo de proveedor,alpha ausente y composición/dimensiones. Píxeles8×8 y archivo
ONNX ficticio en directorios temporales, clases rembg/ORT simuladas. No hubo
segmentación real ni validación de calidad/compatibilidad de una instalación.

No se repiten muestra portuguesa,ASR,prueba española o suites aprobadas. Esta
entrega no implementa cola/cancelación/timeout para el proveedor síncrono; E05
y revisión visual de pelo/bordes/transparencias siguen pendientes. Tampoco añade
el comparador visual de E02. El tool continúa experimental.

Activación agrupada con #109/45b8609 y #108 según el
[plan único pendiente](ACTIVACION_AGRUPADA_STUDIO_ES.md). No se reinicia Studio,
no se invoca el tool con pesos reales ni se cambia configuración de ComfyUI.
