# Parámetros y unidades FreeCAD sin geometría

Seguimiento #30/#3. `freecad_units` conecta la API nativa `FreeCAD.Units.Quantity` con `execute_tool` y `POST /api/studio/applications/freecad/units`. Usa exclusivamente el Python incluido junto a FreeCAD.pyd en la instalación registrada. No instala paquetes, modifica `.venv`, ComfyUI, preferencias, PATH global ni documentos existentes.

Entrada de ejemplo: `{"project_id":"mi-proyecto","source_unit":"in","target_unit":"mm","values":[1,2]}`. Resultado numérico: `[25.4,50.8]`. El agente debe leer este documento y las instrucciones de la etapa antes de usar el puente de herramientas. El catálogo informa la conexión en `numeric_tools` sin convertirla en una certificación de generación CAD.

Se admiten dimensiones compatibles: longitud (mm/cm/m/in/ft), área (mm^2/cm^2/m^2/in^2), volumen (mm^3/cm^3/m^3/in^3), ángulos (deg/rad), masa (g/kg), tiempo (s/min/h), fuerza (N/kN), presión (Pa/kPa/MPa). No se aceptan expresiones o unidades arbitrarias, temperatura con desplazamientos, scripts, archivos ni conversiones entre dimensiones distintas. Máximo 1000 valores finitos de magnitud 1e12 y petición canónica de 65536 bytes.

El proceso usa `-I -B`, shell desactivado, timeout 45 s y salida JSON acotada. Variables heredadas de otros Python/Qt/GIS/FreeCAD se descartan solo en el hijo. `FREECAD_USER_HOME`, `FREECAD_USER_DATA` y `FREECAD_USER_TEMP` apuntan a directorios temporales existentes; el worker comprueba que `FreeCAD.ConfigGet('UserAppData')` corresponde al perfil temporal. No importa FreeCADGui; verifica que no haya GUI ni documentos antes y después. Bloquea sockets Python. Solo realiza aritmética de unidades, sin capas, geometría o inferencia.

La respuesta mantiene unidades explícitas, dimensión, versión real, error de ida/vuelta en la unidad de origen y hashes SHA256 del payload y worker, proyecto y fecha UTC. El error inverso acredita consistencia numérica; no certifica un diseño físico, tolerancias de fabricación, exactitud de medidas ni equivalencias de unidades no admitidas.

Fuentes oficiales: [Quantity](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Quantity.md), [API getValueAs](https://freecad.github.io/API/dc/d69/classBase_1_1QuantityPy.html), [FreeCAD embebido sin GUI](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Embedding_FreeCAD.md), [variables de configuración portable](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Start_up_and_Configuration.md).

Pruebas CI usan procesos simulados y comprueban aislamiento, unidades, errores, origen HTTP y despacho LocalAgent. `OPENMONTAGE_FREECAD_NATIVE_QA=1` activa comprobaciones sintéticas en FreeCAD real; sin la instalación preparada se omiten. La preparación de escenas CAD y evaluación visual continúan como fases diferentes.
