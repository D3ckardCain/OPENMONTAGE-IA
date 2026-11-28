# Borrador de publicación local (#169)

La herramienta `local_publish_plan` persiste un plan versionado en `<proyecto>/publication/plans/`. El plan se vincula a una ruta relativa y al SHA-256 del medio dentro del proyecto. Exige destino remoto por ID, visibilidad solicitada y zona IANA por salida; genera un `request_id` determinista por destino.

No copia el medio ni envía solicitudes. Cada archivo queda marcado `status=draft`, `execution=local_plan_only`, `remote_submission=false` y `remote_status=not_submitted`. Un plan no equivale a autorización ni a publicación.

La creación usa un temporal local y un enlace exclusivo en el mismo volumen para evitar sobrescribir. Repetir el mismo ID/revisión y contenido reutiliza el borrador; cambiar datos exige nueva revisión. Se rechazan credenciales como campos, rutas fuera del proyecto, IDs ambiguos/vacíos, destinos duplicados, visibilidad ausente, zonas desconocidas, offsets incompatibles con la zona/DST y fechas pasadas (que podrían publicar inmediatamente en proveedores).

Limitaciones: TikTok queda fuera del borrador conectado; Meta/YouTube aún requieren cuentas, permisos y sus propios adaptadores. En Windows, el soporte de zonas IANA depende de que haya una base de zonas disponible en el runtime. Si falta, el plan falla claramente; no se añade ni instala `tzdata` aquí. El sistema aún no proporciona aprobación versionada ni escritor remoto. Un futuro adaptador debe exigir aprobación separada del hash del plan y reconciliar resultados inciertos antes de reintentar.

Prueba focalizada: `pytest tests/tools/test_local_publish_plan.py -q` (fixture sintético; sin red ni cuenta).
