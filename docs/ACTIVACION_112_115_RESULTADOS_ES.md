# Activación conjunta #112–#115 — resultados locales

Comprobación del 25 de noviembre de 2026, 23:39–23:41 UTC, después del único
reinicio manual confirmado por el usuario. No se reinició el servidor desde
el agente. Se ejecutó únicamente el plan conjunto y la inspección nueva #115,
sin repetir suites, síntesis, ASR o exportaciones ya aprobados.

## Instancia y conservación

- Puerto4750, PID123920, cargado23:38:20UTC; directorio del proceso comprobado
  mediante lectura de metadatos: `C:\OPENMONTAGE-IA`.
- SaludOK; residente=disco
  `7e9611ee0cbccc15d321f87f71027990e07c68f44d46f170cea48392910085c9`.
- UI `cdae31c80dbe454fec2f456765f58cb9935a8d9bdb4e65713bd040604ec7f86a`;
  identidad de la página coincidente, clasificador real compatible y
  `restart_required=false`. API1/editor3.0; capability `subtitle_words` presente.
- Cola vacía/pausada, worker y tarea local inactivos; cuatro registros de
  trabajos persistentes revisados, ninguno activo.
- Chrome existente, contexto aislado1920×1080. Mutaciones interceptadas antes
  de navegar: un POST sintético elegido, cero POST reales/cero inesperados.
  Sin errores JavaScript. Capturas locales examinadas, sin atribuirles escucha
  humana o validación audiovisual nueva.
- Proyecto QA revisión11 intacto, SHA256 de `manual_edit.json`
  `30085c28db90f096ec36e0615f35106f2a698c41a23bd62b3c85926d64cd62ca` antes/después.
  Settings y applications también mantienen sus SHA256.

## Resultado por entrega

| Issue | Observación local | Pendiente/límite |
|---|---|---|
| #112 | Catálogo real: cuatro voces con preview_contract=1; control Recuperar visible y aviso claro de ausencia de token en esta pestaña | No hay solicitud completada elegible del contrato nuevo. Recuperación end-to-end del mismo WAV/hash sigue pendiente; no fabricar recibos ni repetir síntesis |
| #113 | Primario computado blanco sobre #238636, contraste4.630883; Tab desde título hasta submit, foco sólido2px en los ocho controles recorridos | Iniciar/detener/aprobar ocultos sin producción seleccionada: su foco no comprobado en este recorrido. Sin matriz de viewports ni evaluación humana de accesibilidad completa |
| #114 | Dos submit pendientes producen un POST interceptado, respuesta400 simulada en cliente; Unicode/negación intactos, foco restaurado, aria-busy retirado y botón habilitado | No fue un fallo400 real del servidor; no se repitieron otros errores previamente aprobados |
| #115 | GET real y botón/tabla en el panel, con palabras guardadas y procedencia; cero escrituras del proyecto | Conversión de reloj, sin nueva alineación/medición acústica ni afirmación de sincronía perceptual |

## Inspección #115 sobre portugués guardado

Copia QA `edit-qa107-pt-5f4e1409`, revisión11, conjunto
`b015277c9508428982dd0f5695ea021e`:116palabras de ASR ya guardadas.
El control **Inspeccionar palabras en el reloj del montaje** consultó:

```text
GET /api/studio/editor/edit-qa107-pt-5f4e1409/subtitle-words?set_id=b015277c9508428982dd0f5695ea021e
```

Resultado `studio-word-clock-v1`:106ocurrencias en dos cortes/22.72s/FPS25,
cero exclusiones de palabras parciales. Las otras diez palabras quedan fuera
de los cortes existentes; no se añadieron artificialmente. La tabla presenta
las primeras100ocurrencias con su límite explícito; desplazamiento interno.
Cobertura parcial25/55.472s visible, tiempos fuente→montaje y portugués;
negaciones `não` conservadas. Origen temporal no declarado permanece explícito.

API: `source_file_rehashed=false`, modelo guardado `large-v3/local-ct2`, idioma
pt y offset0. Huellas devueltas:

- Transcripción: `8791aa5595edb5730788c9d015544b7160e809ff0a5e06e5b6185e8ed5a55bfd`.
- Palabras: `2d01540157982a215cca180f3eb582f66edb75e597fd6e314c07972951de4ea6`.
- EDL: `99c1ca875a4183baa0047e9089f4e2fbeab31afc1bf957c01dcb2a34c56acd21`.

La fuente no se certifica de nuevo por este GET. No se crearon cues/SRT ni se
exportó. La muestra portuguesa #107 ya aceptada no se volvió a validar; la
española sigue pendiente. Naturalidad de voces aplazada, coste$0, entornos y
configuración ComfyUI intactos; PR#2 permanece en borrador.

Evidencia local: `.runtime/qa/activation-112-115-live.json`,
`activation-115-live.png` y `activation-114-live.png` en esa misma carpeta.
No se publican WAV, modelos ni proyectos personales.

Registro por issue: [#112](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/112#issuecomment-7177934748),
[#113](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/113#issuecomment-7177935199),
[#114](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/114#issuecomment-7177935579),
[#115](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/115#issuecomment-7177935948).
