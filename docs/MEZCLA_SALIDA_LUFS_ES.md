# Mezcla final y objetivo LUFS en Studio

El formulario **Mezcla de salida** del editor manual comparte el comando reversible
`audio_mix` con el agente. Acepta ganancia lineal de mezcla entre 0 y 4, el
interruptor de normalización y un objetivo LUFS entre −40 y −5. Si no se envía un
campo, el comando conserva el valor actual; en un proyecto nuevo los valores iniciales
son ganancia 1, normalización desactivada y objetivo −16 LUFS.

El objetivo solo altera el grafo de exportación cuando la normalización está activa.
La exportación pasa la mezcla por el filtro `loudnorm` disponible en el AudioMixer
existente, después aplica el limitador final. Guardar el objetivo no promete que el
archivo resultante alcance exactamente ese valor: códec, duración y contenido pueden
afectar la lectura. Usa **Medir mezcla final guardada** sobre el render vigente para
medir LUFS integrados, true peak y cobertura. Esta medición no renderiza ni sustituye
la revisión auditiva.

La operación se guarda en la EDL del proyecto, participa en deshacer/rehacer y deja
obsoleta la previsualización anterior cuando cambia el resultado. Los medios originales
no se modifican. Los límites de este panel siguen siendo locales y no son una
recomendación universal por plataforma.
