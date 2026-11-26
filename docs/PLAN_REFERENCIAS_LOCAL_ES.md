# Plan compartido desde referencias

#145 reutiliza el `scene_plan` canónico y los marcadores temporales existentes.
No instala ReelMimic ni inicia otro director/agentes/inferencia.

`studio_project_edit(action=command)` → operación `reference_plan`: enviar
`revision`, `input_edl_sha256` actual y `plan` válido según scene_plan. Metadata
incluye `reference_contract=studio-reference-plan-v1`, evidencia con fuente/SHA,
SHA del recibo, intervalo, hasta12fotogramas con PTS/SHA y cobertura
`partial_sampled_images_only`. `scene_refs` enlaza IDs de escenas a recibos;
`scene_notes` enlaza los marcadores existentes como comentarios del usuario.
El reloj de comentarios es el montaje; no se interpreta como PTS de referencia.

Comparaciones opcionales declaran el mismo SHA de origen y **el mismo instante**
`reference_source_pts` antes/después; el antes debe estar en la evidencia
declarada. Hashes asociados no verifican por sí solos contenido o calidad: el
contrato informa `declared_hash_bindings_not_redecoded`. Conservar el recibo y
sus imágenes devueltos por `frame_sampler(strategy=evidence)` como artefactos;
no tratar el plan como análisis visual completo ni aprobación automática.

Se guardan fingerprints por escena y sus referencias/notas/comparaciones:
`changed_ids`, `unchanged_ids`, `removed_ids`. Revisar los modificados; ningún
elemento se aprueba por similitud. Cambiar una nota invalida sus escenas
asociadas. Datos y plan comparten deshacer/rehacer/reapertura del editor.

9 pruebas nuevas aprobadas. API real sobre copia portuguesa reutilizó el recibo
#122 de9,5–11,5s y3PTS ya extraídos, sin nueva decodificación/ASR; cambiar escena
uno conservó escena dos sin cambios. Undo/redo/save/reopen exactos. Contrato
inicial y uso por agente acreditados; no nuevo diseñador visual de storyboard,
generación automática integral ni evaluación semántica de semejanza.
