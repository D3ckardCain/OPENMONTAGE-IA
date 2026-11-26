# Preparación regional Chatterbox y CosyVoice3 — #96/#157

26-11-2026. [Resultados e inventario](PREPARACION_VOCES_96_157_RESULTADOS.json).
Solo metadata, archivos terminados verificados una vez y auxiliares mínimos.
Sin síntesis, carga de pesos, inferencias, eliminación de variantes ni cambios
en `.venv`/ComfyUI. Costo$0. #96 conserva su evaluación cerrada: esta preparación
no vuelve a declarar esa evaluación pendiente ni acredita calidad de voz.

**Actualización posterior a bcde8f9:** FDM terminó también decoder V3 y tokenizer
es-MX. Verificados una vez: decoder1056381804bytes/SHA oficial correcto,
2488tensores, cabecera317048bytes y offsets válidos; tokenizer69989bytes/Git blob
oficial correcto. Ambos perfiles ahora pueden reutilizar las mismas rutas C:
sin duplicar contenido. El tokenizer base D: y ve.pt siguen conservados; es-ES
continúa .fdmdownload y no se lee. Los estados de cola iniciales inferiores son
históricos. **Recursos verificados no levantan el bloqueo de loader/runtime.**

## Chatterbox: variantes explícitas y recursos reutilizados

| Perfil | Revisión oficial | T3/bytes/SHA256 |
|---|---|---|
| es-MX/es-419 | [27e595b](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-es-mx-latam/tree/27e595bf2fe7be0533ca299d9afafcde08b7cca7) | t3_es_mx_latam.safetensors /2143990280 /`c66c4517f11c2b35a56e28615c0689deb864cbc411e329552223bbd0a6a063f8` |
| es-ES | [7262b36](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-es-es/tree/7262b364e3222ba9446c9289e7485eadc47ed902) | t3_es_es.safetensors /2143990264 /`d85844b13ea8cb45e95b8d84a55bcfeccb2d743035cf304ee3d778fc6be39546` |

Las descargas en C:/OPENMONTAJE-IA/DESCARGAS_MODELOS se consultaron también
en FDM mediante SQLite **solo lectura**, filtrando URLs públicas. Tamaño de un
.fdmdownload preasignado no demuestra finalización. T3 es-MX terminó durante
el trabajo: SHA256 oficial aprobado una sola vez,2,22s; cabecera33280bytes,
292tensores/offsets y tamaños válidos, sin Torch ni pesos cargados. es-ES y
decoder V3 seguían sin finalizar en la última comprobación de cola. No tocarlos.

Ambos árboles oficiales declaran el mismo decoder V3 safetensors1056381804bytes,
SHA256`4a46190f3dccc2230fbb3488a930bccc925862ee68f2662433dfcfe93ce6c2cb`.
El tokenizer tiene el mismo Git blob`d27fb3f2fd38ca39b7bbfbf83a13b3c617e551df`.
Se encontró ese tokenizer ya disponible en D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/
ResembleAI--chatterbox y se verificó una vez (69989bytes). También ve.pt5698626bytes
coincide con SHA256`4b16d836bc598509860f6fa068165a8bb5e9ac84f05582dfcf278a5a372879f1`
de la [base fijada](https://huggingface.co/ResembleAI/chatterbox/tree/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18).
Los dos perfiles reutilizan esas rutas verificadas; no se copiaron ni descargaron
otra vez. Registro privado en voice_resources y caché por identidad de archivo,
sin hashes automáticos al consultar API. No se usó conds.pt como voz propia.

El s3gen.pt V2 existente en D: no tiene la identidad oficial del V3: **no renombrar
ni sustituir**. Cuando termine el V3, verificarlo una vez y compartir contenido;
no descargar además su alternativa .pt ni otro decoder por cada idioma.

## Bloqueo real del loader y aislamiento

El [código oficial fijado ab55923](https://github.com/resemble-ai/chatterbox/tree/ab55923c27757c90cfcc407baa57dc25a7d25217)
es MIT/0.1.7, pero su mtl_tts.from_local carga ve.pt y s3gen.pt mediante Torch y
no usa el decoder V3 safetensors solicitado. No basta pasar el filename regional.
El [Space oficial, revisión0d2648c](https://huggingface.co/spaces/ResembleAI/Chatterbox-Multilingual-TTS-es-mx-latam/tree/0d2648c4c1637eccfa8d45c7e192a0ad8d5b1fca)
incluye una ruta V3 diferente y carga .pt con strict=False. Se leyó su código;
**no se ejecutó, instaló ni vendorizó**. En el árbol/README observado no figura
licencia separada del código del Space; no inferir permiso de redistribución
de ese fork por la ficha MIT de los pesos. Tampoco usar sus muestras demo como
referencias autorizadas propias. Compatibilidad/atribuciones del loader siguen
por acreditar antes de instalarlo o cargar pesos.

Se compararon únicamente las cabeceras de T3 base/regional: ambos292tensores,
embeddings texto2454×1024 y habla8194×1024. No se volvió a hashear la base ni se
cargaron pesos. La compatibilidad de esas formas no demuestra compatibilidad
S3Gen end-to-end. Siguiente implementación acotada: adaptar el loader MIT
existente para rutas T3/decoder explícitas y safetensors, exigir carga estricta
de claves/formas (solo excepciones documentadas para buffers derivados), recursos
locales y Perth, y cualificar dependencias Windows en el entorno aislado.
No hace falta copiar el fork del Space para plantear esa adaptación propia;
si se reutiliza su código, su licencia/atribuciones deben revisarse igualmente.
No se instala una combinación de versiones contradictorias ni se afirma que la
mera coincidencia de vocabularios resuelva ese trabajo.

La ficha de ambos pesos regionales declara MIT; el upstream MIT y
[Perth MIT](https://github.com/resemble-ai/Perth/blob/master/LICENSE) tienen
alcances separados. Perth conserva su watermark; no se elimina. El blob de
licencia Perth consultado fue4dfc4991c7c565ea00520f520238b8018dcd4715.
Upstream0.1.7 fija Torch/torchaudio2.6 y Transformers5.2; el Space declara
Python3.10/Torch2.8/Transformers4.46.3. Ninguno acredita por sí solo Windows
ni permite trasladar esas dependencias al entorno Qwen existente sin conflicto.

Se preparó `.runtime/chatterbox/venv`, Python3.11.9 **solo para diagnóstico aislado**,
sin pip/dependencias de inferencia. No declarar runtime TTS instalado/operativo.
Diagnóstico real no importa Torch, Transformers o Chatterbox. El worker aislado
rechaza la solicitud regional claramente antes de importar Torch: no cae en
V2, inglés, Turbo ni otro modelo. La instalación de dependencias queda aplazada
por loader/recursos aún no elegibles, evitando una pila incompatible por inercia.

API compartida GET `/api/studio/editor/chatterbox/profiles`, acción del agente
`studio_project_edit(action=chatterbox_profiles)` y panel Audio de preparación.
Ambas variantes figuran **no disponibles para síntesis**. No hay preescucha falsa
ni controles de expresividad que este backend todavía no pueda ejecutar.

## CosyVoice3: evitar otra descarga completa

Modelo fijado a [29e01c4](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/tree/29e01c4e8d000f4bcd70751be16fa94bf3d85a18).
En C: campplus.onnx28303423bytes terminó y coincide con
`a6ac6a63997761ae2997373e2ee1c47040854b4b759ea41ec48e4e42df0f4d73`,
verificado una vez. Los otros cuatro pesos de la tanda seguían en cola: no se
leyeron ni alteraron. Nueve auxiliares oficiales,4,2MB aproximadamente, preparados
en C: sin sobrescribir y comprobados contra Git blob oficial: JSON raíz,
cosyvoice3.yaml, README y cinco archivos de configuración/tokenizador BlankEN.
config.json no se confunde con configuration.json; YAML guardado como texto,
no ejecutado por HyperPyYAML.

Después, la búsqueda de compañeros existentes encontró en **D:** el conjunto
CosyVoice3 catalogado completo: seis pesos estándar con tamaños oficiales y
auxiliares, además de alternativas antiguas conservadas. Es **candidato local**,
no verificación SHA ni carga/compatibilidad acreditadas. No se volvieron a leer
gigabytes ya existentes ni se recomiendan más descargas de pesos. Antes de
reanudar cualquier descarga redundante, priorizar ese conjunto y verificar solo
los archivos necesarios cuyo resultado válido no exista. No se canceló ni
modificó la cola FDM del usuario.

El [loader fijado074ca6d](https://github.com/QwenAudio/CosyVoice/tree/074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc)
instancia Qwen2ForCausalLM.from_pretrained sobre CosyVoice-BlankEN antes de
llm.pt: también requiere su model.safetensors988097824bytes en esta ruta normal.
Ya hay candidato de ese tamaño en D:, no descargar otra copia por omisión.
No confundir esta necesidad del loader con otra variante RL.

El diagnóstico nativo ahora exige solo el backend estándar y BlankEN; excluye
llm.rl.pt, flow.decoder.estimator.fp32.onnx y speech_tokenizer_v3.batch.onnx de
requisitos acumulativos. Las copias alternativas existentes permanecen intactas.
GET `/api/studio/editor/cosyvoice/preparation` distingue C: parcial, D: candidato
completo por tamaños y ausencia de verificación/runtime. No carga YAML ni pesos.

Código Apache2.0; ficha de pesos Apache2.0. El disclaimer académico del README
habla de contenido/ejemplos; [discusión oficial19](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/discussions/19)
sigue sin respuesta visible que aclare el alcance comercial completo. **No
afirmar NC de los pesos como hecho ni elegibilidad comercial integral resuelta**.
Derechos de referencias se revisan aparte. No se cargó el modelo mientras esto
y la compatibilidad están pendientes.

Requirements fijados: Torch/torchaudio2.3.1 y Transformers4.51.3; ONNXRuntime
CPU1.18 en Windows, extras TensorRT/DeepSpeed condicionados a Linux. No copiar
el requirements completo al entorno Qwen ni instalar Conda/TTSfrd por inercia.
Memoria8GB y calidad española requieren prueba autorizada posterior; no se
deducen de archivos presentes o idioma declarado.

## Comprobación y siguientes pasos

Ocho pruebas nuevas de preparación regional/Cosy: metadata sin lectura de pesos,
descarga parcial, identidad cambiada, reutilización compartida, guard antes de
Torch/YAML, agente y exclusión de alternativas. API/panel reales en instancia
aislada4766: perfiles bloqueados con motivo claro, tokenizer/ve reutilizados y
candidato D: informado. Sin síntesis ni cargar modelos.

Agrupar activación de estas rutas con HyperFrames; no se reinició4750. PR2
borrador, CI no repetida. Quedan descarga V3/es-ES, loader regional compatible
y licencias del código alternativo, cualificación Windows/dependencias y revisión
humana. Ninguna instalación, hash o muestra aprobados se repitieron.

### Continuación del entorno aislado (26 noviembre)

Se preparó el código MIT upstream fijado en
`ab55923c27757c90cfcc407baa57dc25a7d25217` (sin ejecutar el fork del Space).
Los wheels oficiales Torch/torchaudio2.6.0+cu124 ya existentes en la caché local
se reutilizaron mediante enlaces duros dentro del entorno Chatterbox; no se
descargó otra copia de esos binarios. El entorno solo tiene pip24.0 y
setuptools65.5.0: **la instalación de inferencia no terminó**.

El primer intento falló en el subproceso de build de antlr4 por la cadena de
certificados. Un único intento con `PIP_USE_FEATURE=truststore` heredado por
ese subproceso superó ese punto manteniendo TLS. Terminó con
`ReadTimeoutError` en files.pythonhosted.org al descargar Transformers5.2.0,
con reintentos desactivados. No se continuó reintentando ni se cambió la red.
No se cargaron pesos ni se ejecutó síntesis. El diagnóstico comprueba solo
metadatos de distribuciones del entorno aislado: versiones presentes **no**
acreditan importaciones, loader V3, memoria ni inferencia.

Dos pruebas nuevas pasan: entorno ausente y metadatos CUDA con versión local
`+cu124`, sin importar Torch. Se suman a las ocho pruebas ya registradas, que
no se repitieron. Sigue pendiente completar dependencias y acreditar una
adaptación estricta del loader MIT antes de habilitar las voces regionales.
La pila propuesta fija Perth1.0.1; el manifest upstream usa master, por lo
que esta elección también requiere comprobar compatibilidad, sin quitar la
marca de agua. No se modificaron `.venv`, ComfyUI ni el entorno Qwen.
