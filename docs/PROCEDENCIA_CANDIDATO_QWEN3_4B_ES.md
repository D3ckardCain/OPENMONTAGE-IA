# Procedencia del candidato Qwen3_4B y contraste oficial (#82)

## URL y revisión registradas

Se encontró evidencia adicional en el flujo NTFS **Zone.Identifier**, de306bytes,
del candidato de E:. Su `HostUrl` registra exactamente:

```text
https://huggingface.co/Comfy-Org/flux2-klein-4B/resolve/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965/split_files/text_encoders/qwen_3_4b.safetensors
```

La revisión registrada es **5b3abca5c0dc1ecd4eaf3340868d09063fc1c965**.
Coincide con el enlace fijado anteriormente; ya no se deduce solo del nombre de
la carpeta. ZoneId3 indica origen Internet; el referente es chatgpt.com y se ha
omitido su URL privada del informe público.

Este registro identifica la URL de origen anotada por Windows/navegador, pero
no autentica los bytes recibidos. Es metadato mutable y no conserva una respuesta
HTTP/ETag/cadena de redirecciones completa. No se encontró recibo local Hugging Face
en la inspección anterior del directorio. El flujo Zone.Identifier es separado:
no se suma a los8GB al calcular Get-FileHash del archivo principal.

## Misma revisión, metadatos oficiales

Se consultó únicamente JSON público de la
[revisión exacta en Hugging Face](https://huggingface.co/api/models/Comfy-Org/flux2-klein-4B/tree/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965/split_files/text_encoders).
No se solicitó el endpoint resolve ni se descargaron pesos.

| Dato | Oficial de esa revisión | Candidato, resultado ya calculado |
|---|---|---|
| Tamaño | 8044982048 bytes | 8044982048 bytes: coincide |
| SHA256 | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` | `6cbad3f9d28e15e86d3ddb1842cd51653ad236c92e9a2204bd4415241af22f53`: difiere |

El SHA oficial procede de `lfs.oid`; no se confundió con el Git blob SHA1
`8eb608c38dfe7461d3a72a8c3c1c5db10da90ee0` ni con `xetHash`.
El hash local se reutilizó del recibo PowerShell anterior, tras comprobar que
tamaño/mtime/ctime/dispositivo/inode siguen iguales. No se releyeron los8GB.

## Otras variantes oficiales contrastadas

Se fijaron las revisiones devueltas por los metadatos: Flux-2-Klein-4B5b3abca5,
Z-Image-Turbo6fc90a3b y Z-Image94d47a46. Las tres publican el mismo BF16 de8GB y
el mismo SHA6c671498…. Las otras variantes listadas son:

| Variante oficial | Bytes | SHA256 |
|---|---:|---|
| qwen_3_4b_fp4_flux2 | 3848213998 | `3eab03a77adb0ee5304a4e677d5c10ac22f9049c1d7c894adca4f8bb39206ca8` |
| qwen_3_4b_fp4_mixed | 3479416193 | `7ca32dcf07dfe7692945d80fff86e3a74cb83c6206b9b223ac6836b939bb85d6` |
| qwen_3_4b_fp8_mixed | 5631994051 | `72450b19758172c5a7273cf7de729d1c17e7f434a104a00167624cba94f68f15` |

Ninguna coincide por tamaño/hash con el candidato de8GB/398tensores BF16.
Fuentes: [metadatos Flux](https://huggingface.co/api/models/Comfy-Org/flux2-klein-4B?blobs=true),
[Z-Image-Turbo](https://huggingface.co/api/models/Comfy-Org/z_image_turbo?blobs=true),
[Z-Image](https://huggingface.co/api/models/Comfy-Org/z_image?blobs=true).
El JSON adjunto conserva revisiones completas, archivos y huellas por repositorio.

También se consultó [Qwen/Qwen3-4B](https://huggingface.co/api/models/Qwen/Qwen3-4B?blobs=true),
revisión1cfa9a7208912126459214e8b04321603b3df60c: distribuye tres shards, no este
archivo unificado. No se comparan sus hashes como si una conversión fuera
byte-equivalente, ni se reconstruye el modelo para intentar demostrarlo.

Se reutilizaron44 revisiones SHA fijas del informe anterior:34 entradas con el
archivo presente, todas con6c671498…; ninguna con el nuevo hash6cbad3f9….
Una búsqueda web literal de este último no devolvió resultados; no demuestra
ausencia global ni descarta conversiones comunitarias no consultadas.

## Conclusión y límites

**La URL/revisión registrada es la prevista, pero el candidato no coincide con
el artefacto publicado en esa revisión. No se ha identificado otra variante
legítima entre las fuentes oficiales contrastadas.** La estructura BF16 válida
no acredita identidad, procedencia autenticada ni compatibilidad de ejecución.
No se identifica la causa de la discrepancia ni se declara corrupción.

Se registró la conclusión en #82 sin proponer otra descarga. Solo se leyeron
metadatos locales/ADS y JSON oficial; no pesos, nuevos hashes completos, descargas
de modelos, movimientos, borrados, reparaciones, inferencias o cambios de ComfyUI.
No se accedió a D:, que sigue desconectado. Evidencia:
`PROCEDENCIA_CANDIDATO_QWEN3_4B_20261124.json`. PR#2 en borrador,costo$0.
