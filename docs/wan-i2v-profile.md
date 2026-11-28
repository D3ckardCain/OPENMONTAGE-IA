# WAN 2.2 imagen a video

El selector «Perfiles de video WAN» del Estudio incluye
`wan22-14b-i2v-4step`. Seleccionarlo guarda configuración; no inicia trabajos.
El adaptador utiliza el workflow API existente `wan22-i2v-4step.json` y su
nodo de salida 108. Requiere los pesos I2V high/low noise y las dos LoRA I2V
que enumera el catálogo. No sustituye archivos T2V ni descarga pesos.

En una llamada de producción autorizada al adaptador WAN, incluye `text` y
`server_image`. Este último es el nombre de una imagen ya cargada en el servidor
ComfyUI seleccionado, por ejemplo `source.png`, no una ruta Windows ni una URL.
El Estudio incluye un cargador local de PNG/JPEG de hasta 8 MB y 16 millones
de píxeles. Valida que la imagen se pueda decodificar, guarda el original por
hash en el proyecto y muestra una vista previa. Las imágenes repetidas se
reutilizan; una entrada inválida no reemplaza la anterior.

Durante la ejecución autorizada del adaptador, `project_id` permite usar la
imagen preparada del proyecto si no se especifica `server_image`. Se verifica
su hash, se transfiere al servidor configurado y se registra el nombre devuelto
por ComfyUI. La reanudación con `resume_prompt_id` utiliza ese mismo nombre,
sin subir otra copia ni enviar otro trabajo. Cambiar imagen o servidor impide
reanudar ese registro. Preparar la imagen desde el formulario no inicia inferencia.

La transferencia y la reanudación están probadas con un cliente simulado;
queda pendiente la generación real desde la app.

Los parámetros opcionales `negative_prompt`, `width`, `height`, `frames`, `seed`
y `fps` se enlazan con los nodos I2V correspondientes. El perfil conserva los
cuatro pasos y la división high/low del workflow original. Ancho y alto requieren
múltiplos de 32; cuadros requieren la forma 4n+1.

La prueba manual del usuario confirma ejecución de WAN 14B I2V en su instalación,
pero no confirma que este workflow API concreto con LoRA de cuatro pasos haya
producido un video. La validación de código usa pruebas sin GPU ni servidor.
No se cambia el workflow que está generándose actualmente en el ordenador.

## Agentes

El agente dispone de `project_source_image`, sin parámetros, para consultar
exclusivamente la imagen de su proyecto. Su contexto inicial incluye esa ficha;
el contrato del adaptador explica `project_id` y `server_image`. El selector de
perfiles del agente admite I2V y se comprueba contra el catálogo en las pruebas.
La elección creativa y la autorización de producción siguen las etapas existentes.
El formulario rechaza reemplazar la imagen mientras ese proyecto tenga agentes
activos; consultar su imagen sigue permitido. No se ejecutaron agentes con
Ollama ni inferencias reales para validar esta conexión de contratos.

## Prueba de integración del recorrido del agente

`test_agent_to_real_adapter_bridge_with_simulated_server` atraviesa el despacho
real del agente, el esquema de entrada, el adaptador registrado `model_wan`, la
preparación de imagen, los enlaces del workflow I2V, la validación de nodos y el
registro de salida. Solo se simulan el servidor ComfyUI y la disponibilidad de
pesos: no hay Ollama, GPU ni video real. El archivo de salida contiene bytes de
prueba y no demuestra decodificación ni calidad visual.

La verificación conjunta del puente I2V, adaptadores, estudio, imágenes, perfiles
e informes completó 74 pruebas. El siguiente control sobre hardware sigue siendo
la ejecución real desde la app, cuando no interfiera con la prueba del usuario.

## Recuperación de trabajos largos

Después de enviar un trabajo, el adaptador guarda su identificador en
`comfy-wan-job.json` dentro de la carpeta de salida. Si falla la espera o la
recuperación de archivos, registra `recovery_required` y conserva ese identificador.
Este estado no implica que el servidor siga generando ni que haya cancelado.

Para recuperar se usa el mismo `output_dir`, parámetros y `resume_prompt_id`.
El adaptador comprueba identidad, servidor y workflow; no vuelve a enviar el
trabajo. Repetir una ejecución sin identificador sobre una carpeta que ya contiene
un registro se rechaza antes de subir imágenes. Para una prueba nueva se utiliza
otra carpeta de salida. También se conserva el identificador si falla la descarga
por un problema de disco, de modo que pueda intentarse recuperar la salida.

Estas comprobaciones no cubren una caída entre la aceptación de POST /prompt y
la escritura de su identificador: ese caso requiere consultar la cola/historial
antes de repetir. Tampoco prueban generación real. La batería conjunta de este
cambio completó 75 pruebas sin GPU.

## Consultar registros desde el panel y los agentes

Dentro de una producción, «Consultar registros del proyecto» muestra los
identificadores, carpetas de salida y errores de los trabajos registrados por
la app. La ruta GET `/api/studio/comfy-jobs/{pid}` y la herramienta del agente
`project_comfy_jobs` leen solo archivos locales del proyecto. No consultan la
cola, no descargan medios y no ejecutan recuperación automática. Los trabajos
manuales de ComfyUI no se incorporan a esta lista por sí solos.

El estado mostrado corresponde al registro local y puede diferir del servidor.
Los registros corruptos generan avisos sin impedir consultar los demás. No se
siguen enlaces simbólicos; se limita el recorrido a 1000 carpetas y 100 trabajos,
con aviso si la lista puede estar incompleta. La batería conjunta suma 77 pruebas.
