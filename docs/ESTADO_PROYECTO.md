# Estado consolidado de OPENMONTAGE-IA

Actualizado: 12 de noviembre de 2026.

## Alcance y fase actual

- Aplicación local de costo operativo objetivo USD 0; sin APIs de pago, tarjetas,
  pruebas temporales ni dependencia de suscripciones.
- Contenido para todas las redes sociales objetivo. Español primero, inglés después.
- **Fase autorizada: investigación, documentación, descarga e inventario.** No realizar
  inferencia, instalación de motores ni publicación de contenido en esta fase.
- Calidad y velocidad comerciales son metas; falta validación física y comparación.
- Hardware de prueba confirmado: i7-12650H, 16 GB RAM, RTX 4060 Laptop, 8.188 MiB VRAM.
  No confundirlo con la RTX 4080 mencionada inicialmente. Otros equipos son posibles.

## Qué está hecho y qué no

| Elemento | Estado y límite |
|---|---|
| ComfyUI portable en Windows | Inició servidor y reconoció CUDA; no se ha validado generación |
| Política de costo cero | Guardas y selectores en rama de trabajo; no certifican todo el sistema ni al director LLM |
| Adaptador local Wan | Implementado y probado con fixtures/servidores simulados; falta ejecución física con pesos |
| Comprobadores de archivos | Verifican estructura, tamaño y SHA según opciones; no cargan modelos |
| Catálogo original | 375 archivos únicos en 20 grupos; conservar su referencia histórica |
| Comparación de discos | 367/375 encontrados por ruta y tamaño; 8 faltantes identificados en los inventarios originales |
| Descargas adicionales | Comunicadas al usuario; sin inventario actualizado ni SHA local posterior |
| Agentes y campañas | [Requisitos documentados](AUTOMATIZACION_AGENTES.md); autonomía integral pendiente |
| Publicación en redes | Adaptadores, permisos y pruebas pendientes; ninguna publicación realizada |

Los conteos anteriores pertenecen a los inventarios aportados, no al estado actual de
las descargas en curso. No afirmar que todos los pesos están completos, íntegros o
instalados. No hay acceso directo desde el entorno de documentación a los discos D:.

## Dos discos, una letra de unidad

| Disco | Serie de volumen | Letra al conectarse | Situación comunicada |
|---|---|---|---|
| ADATA | A2A732C6 | D: | Destino de nuevas descargas; conectarlo por separado |
| Seagate Basic | F479B55E | D: | Sin espacio disponible para nuevas descargas |

ADATA: 114 archivos en el inventario original. Seagate Basic: 63.655, incluidos muchos
archivos de Python/ComfyUI. Ambos informes incluyen un error de lectura en
`System Volume Information`; esto no demuestra corrupción de modelos.
No sumar archivos de programa como si fueran modelos. No identificar un disco solo
por D:, pues ambos usan esa letra en momentos diferentes.

Movimientos confirmados por salida de PowerShell del usuario:

- ADATA: nueve componentes LTX-2.5 reubicados desde el almacén a las categorías ComfyUI:
  dos transformadores, dos escaladores latentes, duration head, encoder Gemma4-12B
  y tres VAEs. Verificación de tamaño del movimiento, no SHA ni inferencia.
- Seagate: `gemma_3_12B_it_fp4_mixed.safetensors` trasladado de `checkpoints` a
  `text_encoders` (9.447.702.218 bytes). No duplicar su descarga.

## Ocho ausencias detectadas y posteriormente comunicadas para descarga

| Archivo | Destino relativo a `D:\OPENMONTAJE-IA\` | Estado actual |
|---|---|---|
| model.safetensors.index.json | DESCARGAS_MODELOS\GAIR--daVinci-MagiHuman\1080p_sr\ | Comunicado; sin nueva verificación |
| model.safetensors.index.json | DESCARGAS_MODELOS\GAIR--daVinci-MagiHuman\540p_sr\ | Comunicado; sin nueva verificación |
| model.safetensors.index.json | DESCARGAS_MODELOS\GAIR--daVinci-MagiHuman\distill\ | Comunicado; sin nueva verificación |
| gemma4_e2b_it_int8_convrot.safetensors | ComfyUI_windows_portable\ComfyUI\models\text_encoders\ | Comunicado; sin nueva verificación |
| ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors | ComfyUI_windows_portable\ComfyUI\models\loras\ | Comunicado; sin nueva verificación |
| am_echo.pt | DESCARGAS_MODELOS\hexgrad--Kokoro-82M\voices\ | Comunicado; sin nueva verificación |
| zf_xiaoxiao.pt | DESCARGAS_MODELOS\hexgrad--Kokoro-82M\voices\ | Comunicado; sin nueva verificación |
| zf_xiaoyi.pt | DESCARGAS_MODELOS\hexgrad--Kokoro-82M\voices\ | Comunicado; sin nueva verificación |

Los tres índices MagiHuman tienen el mismo nombre y tamaño, pero sus subcarpetas
identifican modelos diferentes. Un emparejamiento inicial por nombre habría contado
370 presentes: se corrigió a 367 antes del informe. No reutilizar esa comparación
insegura. Extras descargados por el usuario se conservan; no borrarlos sin identificar.

## Reglas de descarga y reutilización

Usar [la ampliación del catálogo](DESCARGAS_ADICIONALES.md) junto con
[el catálogo original](DESCARGAS_CANDIDATOS.md). Cada enlace debe apuntar al archivo,
no a una página HTML. Presentar nombre enlazado y carpeta Windows completa sin nombre
de fichero. No repetir pesos alternativos ni componentes compartidos.

Comparar SHA256 publicado para archivos LFS y Git blob SHA1 para archivos pequeños
cuando estén disponibles. Misma extensión/nombre/tamaño no prueba identidad.
El SHA remoto es una referencia: falta leer el archivo local completo para validarlo.
Conservar config, tokenizer, índices, licencias y procedencia, no solo pesos.
GATED con acceso concedido significa permiso de descarga, no licencia comercial
irrestricta. Dependencias compartidas entre discos siguen pendientes de copia/enlace
cuando se monte el entorno de ejecución.

## Siguiente secuencia de trabajo

1. Durante las descargas: mantener catálogo, referencias, destinos, duplicados y licencias.
2. Al finalizar: inventario actualizado de ADATA y Seagate, por separado y con su serie.
3. Comparación completa y validación de archivos, antes de instalar/probar motores.
4. Cuando el usuario cambie de fase: terminar un motor local y probarlo antes de otro.
5. Integrar director local, revisión, campañas y publicación según criterios documentados.

No iniciar automáticamente estos pasos futuros por actualizar la documentación.

## Selección para el encargo de 48 vídeos

La [revisión orientada a calidad](SELECCION_CALIDAD_CAMPANAS.md) propone MOSS-SoundEffect v2,
Qwen3.6 (comparar una variante), Qwen-Image-2512 y Qwen TTS CustomVoice de 1,7B como
nuevos candidatos, con fuentes y revisiones. No se han entregado sus listas finales,
no se declara descarga completada y no se han probado. Qwen-Image-2.1 y TangoFlux
quedan excluidos del flujo comercial por sus restricciones no comerciales.

## Verificación de afirmaciones y contexto

[Diseño del módulo](VERIFICACION_AFIRMACIONES.md) documentado el 13 de noviembre de 2026:
comparación de declaraciones con pruebas y contexto omitido, trazabilidad de citas,
plantilla fija ES/EN y revisión editorial. Especificación y ejemplo vacío; integración,
esquemas de ejecución, inferencia y producción pendientes. No requiere nuevas descargas
obligatorias en esta etapa.

## Series infantiles automatizadas

[Diseño de las tres series y biblioteca de movimientos](SERIES_INFANTILES_AUTOMATIZADAS.md)
documentado el 13 de noviembre de 2026. Públicos 2–4, 5–7 y 8–12; estilos 2D/3D/mixto
pendientes de comparación. Descargas comunicadas: Krita, Blender y Rhubarb; Rigify
incluido. Biblioteca propuesta, sin clips creados, integración ni inferencia probadas.
