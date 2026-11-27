# Plan ejecutable del agente

Los paquetes `proposal_packet` previos conservan su compatibilidad. Para activar dependencias por etapa, añade a `metadata`:

```json
{"executable_plan_contract":"studio-plan-dag-v1"}
```

Con ese contrato, cada etapa de `production_plan.stages` debe declarar:
`id` estable, `depends_on` (IDs anteriores o posteriores del mismo plan),
`inputs`, `outputs` y `acceptance_criteria`. El agente valida IDs únicos,
dependencias existentes, ausencia de autociclos y orden acíclico antes de guardar
el artefacto. Un paquete inválido no reemplaza la última propuesta guardada.

El plan expresa contratos y orden topológico; todavía no es un scheduler ni
ejecuta herramientas. Tres conceptos mínimos ya los exige el esquema existente;
este cambio no crea previews visuales, no selecciona una propuesta por el usuario
y no acredita una vista real en Studio. Voz/avatar, disponibilidad de runtime,
memoria y derechos siguen sujetos a diagnósticos separados. Pruebas actuales son
fixtures sintéticas, sin inferencia, síntesis, render o cambios de proyecto real.
