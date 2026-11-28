# MagiHuman Base corregido; Wan VACE pendiente de High

Seguimiento de #3, 26 de noviembre de 2026. Este cambio posterior corrige el estado histórico del inventario final; no vuelve a ejecutar ese inventario.

## MagiHuman Base

El índice de Base en F: ya corresponde a sus **7 fragmentos y 331 tensores**, no a los 13 de Distill. Revisión oficial: `GAIR/daVinci-MagiHuman@7fe95e50c11bd92bdadf94cd51dbec18427f8e0c`.

- Tamaño del índice: **27.480 bytes**.
- Git blob oficial: `09d2c7682f035305a65c1a0d040dbec884fc532b`.
- SHA256 calculado del JSON: `a5477affadbef4271e33c75a7b648a3f983b0e4409ca72e202ea31499d07cbce`. No se presenta como un SHA256 publicado oficialmente.
- [Archivo oficial fijado](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model.safetensors.index.json).

La descarga pequeña falló con `WinError 10013` antes de cambiar archivos. Sin cambiar permisos, se recuperaron los bytes del índice desde las cabeceras existentes y se comprobó **identidad exacta con el Git blob oficial y su tamaño antes de sustituirlo**. No se aceptó una aproximación del índice ni se eludió la restricción de red.

Los siete hashes previos se reutilizaron tras confirmar volumen, identidad, tamaño y fechas. Solo se leyeron **36.992 bytes de cabeceras**, con longitud acotada antes de leer JSON. Se comprobó asignación exacta de claves a fragmentos, tipos/formas/offsets, ausencia de solapamientos y suma de **30.642.008.128 bytes de tensores**. Se verificó el JSON escrito. No se cargó el modelo ni se rehasheó o modificó ningún fragmento.

El índice Distill anterior permanece como evidencia privada en `.runtime/qa/full-downloads/magihuman-base-index-before-distill.json`. La caché del índice corregido se actualizó; los resultados negativos anteriores permanecen en el informe histórico. [Evidencia detallada](MAGIHUMAN_BASE_INDICE_CORREGIDO_20261126.json).

## Wan VACE

Se comprobaron los metadatos de las 10 rutas ya verificadas de Wan sin leer pesos. Ambos archivos llamados High y Low contienen el **Low oficial**: SHA256 `0bf791adfb8330d451d2f5c03577b2a8fb780453f8ef05e23a8fa91f27a2134d`. Se conservan ambos.

No hay una copia High correcta en el inventario verificado. Falta el siguiente contenido, no un nombre de archivo:

- Revisión: `alibaba-pai/Wan2.2-VACE-Fun-A14B@4438caabbfdd7437bbb0283d86cb200d1b7223ba`.
- Archivo: `high_noise_model/diffusion_pytorch_model.safetensors`.
- Tamaño: **34.675.325.000 bytes**.
- SHA256 oficial: `66c61b736c5674deeeef17861e494d3652cc9b1463a9656bf18c2c72d2c5f007`.
- [Fuente oficial fijada](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/high_noise_model/diffusion_pytorch_model.safetensors).
- Destino nuevo preparado, sin sobrescritura: `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\high_noise_model\diffusion_pytorch_model.official-4438caab.safetensors`.

No se inició una descarga grande tras el fallo de acceso de red observado ni se borró/movió el Low situado bajo High. La recuperación del High queda pendiente de disponibilidad de descarga; no se declara conjunto funcional. [Evidencia reutilizada](WAN_VACE_VARIANTES_PENDIENTES_20261126.json).

Tras corregir el índice, quedan **9 rutas discrepantes / 8 referencias únicas sin copia correcta** del inventario histórico. No se han recalculado duplicados globales ni repetido pruebas. Studio, descargas, configuraciones, entornos y ComfyUI se conservan.
