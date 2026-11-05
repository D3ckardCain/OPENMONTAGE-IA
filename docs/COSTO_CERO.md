# OPENMONTAGE-IA: política de costo cero

## Objetivo

Sin pagos de software, suscripciones, APIs, tarjetas ni pruebas temporales para
funciones esenciales. Hardware y almacenamiento se dimensionan para este
proyecto; electricidad solar disponible. La calidad y velocidad de las
demostraciones originales son objetivos de aceptación que requieren mediciones;
esta protección de costos no demuestra todavía esa equivalencia.

## Primera protección implementada

- Presupuesto predeterminado: USD 0, modo `cap`, umbral por operación USD 0.
- La frontera `BaseTool.execute()` rechaza herramientas API, híbridas y de
  runtime desconocido antes de caché, instrumentación o ejecución del proveedor.
- Los selectores híbridos pueden dirigir llamadas; cada proveedor elegido pasa
  de nuevo por el bloqueo, también en llamadas anidadas y reintentos.
- Operaciones locales requieren estimación numérica, finita y exactamente cero.
  Una estimación desconocida o fallida bloquea la ejecución.
- Los proveedores bloqueados aparecen como no disponibles, con motivo visible,
  y no se ofrecen como opciones de configuración mediante claves de API.
- ComfyUI queda bloqueado provisionalmente: un servidor local puede ejecutar
  Partner Nodes que consumen créditos. Hay que validar flujos y nodos locales
  antes de habilitarlo. Esto también bloquea sus flujos locales por ahora.
- La política no se desactiva al añadir credenciales ni al aumentar el presupuesto.

Se bloquean también APIs gratuitas en esta primera fase: aún no se han validado
sus condiciones ni su independencia de cuotas o cambios de planes.

## Uso y verificación

No se necesitan claves comerciales. Instalar herramientas y modelos locales
según sus instrucciones; los modelos pueden requerir descargas iniciales.
El menú de proveedores muestra solo disponibilidad permitida por la política.
Si falta capacidad local, debe informarse el bloqueo: no reducir la calidad ni
cambiar video por imágenes para aparentar que se cumplió la producción.

Prueba sin GPU, modelos, red ni llamadas a proveedores:

```bash
python -m unittest discover -s tests/tools -p test_zero_cost_policy.py -v
```

Requiere las dependencias habituales de configuración (`pydantic` y `pyyaml`).

## Alcance y pendientes

Es una barrera de aplicación, no un aislamiento de red del sistema operativo.
Se apoya en los contratos de las herramientas locales y no intercepta scripts
ajenos a BaseTool, SDKs invocados directamente, procesos externos, código de un
agente ni todas las extensiones futuras. No equivale aún a una garantía de
aislamiento de todo el sistema.

Pendiente: auditar rutas locales y procesos externos, validar flujos ComfyUI,
integrar dirección mediante un agente local y revisar licencias individuales de
motores, modelos, voces y material. Cambiar la configuración `llm.provider` por
sí solo no implementa ese agente.

Después se compararán resultados locales con referencias concretas, midiendo
resolución, duración, consistencia, movimiento, audio y tiempo total de producción.
