# Sustitución de video de pago: Wan 2.2 local

## Alcance actual

Objetivo activo: sustituir la generación de video mediante nodos ComfyUI con
créditos por ejecución local, sin perder la meta de calidad y velocidad.
No se considera terminado hasta producir y evaluar video real en GPU.

Equipo indicado por el propietario: Intel Core i7 de 12.ª generación y NVIDIA
RTX 4080. Pendientes de comprobar: modelo exacto, VRAM, controlador, RAM y sistema
operativo. No se reutilizan especificaciones de otros proyectos.

## Sustituto incorporado

Herramienta: `comfyui_wan_local`. Hereda los constructores de los flujos Wan 2.2
14B FP8 de OpenMontage, con las LoRAs LightX2V de cuatro pasos. Admite texto a
video e imagen local a video. Mantiene la semilla cero como valor válido.

La licencia del repositorio oficial Wan 2.2 es Apache 2.0:
https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt
Antes del despliegue se verificarán también las licencias y versiones de los
pesos y LoRAs exactos descargados; no se deducen solo de la licencia del código.

## Reglas de ejecución

- ComfyUI debe estar en la misma PC mediante HTTP en una dirección loopback.
  `localhost` se normaliza a `127.0.0.1` sin resolver DNS.
- Se respetan `COMFYUI_VIDEO_SERVER_URL` y `COMFYUI_SERVER_URL`, pero se rechazan
  servidores públicos y LAN en este adaptador. No se usan proxies del entorno
  ni se siguen redirecciones.
- Solo se aceptan `wan22-t2v-4step.json` y `wan22-i2v-4step.json`. Se fija su
  contenido revisado mediante huellas de JSON canónico, compatibles con CRLF.
- Se pueden variar texto, dimensiones, cantidad de fotogramas, semilla y nombres
  de entrada/salida. Modelos, LoRAs, nodos, enlaces e instrucciones extra se
  rechazan si difieren de las plantillas revisadas.
- Dimensiones en múltiplos de 16 y cantidad de fotogramas `4n+1`.
- La referencia de imagen debe ser un archivo local. Salida MP4.
- No acepta flujos personalizados, familias con créditos, URLs de referencia
  ni reanudación de trabajos cuya procedencia no se ha verificado.
- Si faltan modelos, devuelve el error y las instrucciones existentes; no
  sustituye automáticamente el video por imágenes ni cambia de proveedor.

La herramienta se descubre mediante el registro normal. Las producciones reales
deben seguir un manifiesto de `pipeline_defs/`, sus etapas y sus aprobaciones;
estas pruebas no constituyen una producción ni autorización para omitirlas.

## Pruebas reproducibles

```bash
python -m pytest tests/tools/test_zero_cost_policy.py tests/tools/test_comfyui_wan_local.py tests/tools/test_base_tool_dependencies.py -q
```

Las pruebas de integración levantan un servidor HTTP **emulado** en loopback:
comprueban consulta de modelos, envío del grafo, consulta de estado, subida de
imagen y descarga de un archivo de prueba. Ese archivo es un marcador binario
explícito, no un video generado por IA. También se prueban rechazo de nodos y
modelos alterados, servidores externos, redirecciones y entradas no permitidas.

## Qué falta para cerrar este objetivo

1. Comprobar GPU y controlador en la PC indicada.
2. Instalar y verificar las versiones de ComfyUI, modelos y LoRAs locales.
3. Producir muestras reales T2V e I2V a través del pipeline, registrando semilla,
   dimensiones, fotogramas, duración, pico de VRAM y tiempo de extremo a extremo.
4. Comparar esas muestras con una demostración comercial concreta y la misma
   promesa de entrega. Calidad de movimiento, coherencia y velocidad siguen
   pendientes de medición; los tests HTTP no prueban esas propiedades.

El perfil de recursos procede de los flujos originales y es orientativo, no
una medición en la RTX 4080 del propietario. El cliente no puede garantizar que
un servidor ComfyUI modificado maliciosamente ejecute lo que declara: se requiere
una instalación local confiable. Esta barrera tampoco aísla código externo al
adaptador ni supervisa el tráfico del proceso ComfyUI en el sistema operativo.
