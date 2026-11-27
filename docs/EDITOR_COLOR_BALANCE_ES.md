# Temperatura y tinte SDR por clip (#174)

El panel **Color del clip · SDR** admite temperatura creativa (−1 frío, +1 cálido) y tinte (−1 verde, +1 magenta). Los valores viajan en el comando `clip_color`, se guardan en la edición compartida y pasan por el mismo filtro FFmpeg que previsualización, comparación y exportación. Bypass conserva los valores; deshacer/rehacer y guardar/reabrir usan el historial existente.

No es balance de blancos calibrado, lectura RAW, corrección HDR ni garantía colorimétrica. Son desplazamientos RGB aproximados con `colorbalance` sobre SDR. Curvas disponibles por separado; selectores HSL, LUT y scopes calibrados siguen fuera de alcance. No se cambian fuentes originales ni se añaden binarios.

Pruebas focalizadas añadidas: orientación del signo frío/cálido y verde/magenta, rango/NaN/tipos inválidos, mismo grafo en preview/export, comando del agente, bypass y persistencia. No hay muestra real nueva ni validación visual/audiovisual en Studio 4750; la activación queda agrupada con el reinicio manual futuro.


### Matiz HSL global

La ampliación añade `hue_degrees` (−180…180, 0 sin cambio) al comando reversible `clip_color`. FFmpeg aplica `hue=H=…` después de los controles SDR existentes; preview y export comparten el filtro, y bypass conserva el valor para restaurarlo. El capability `clip_color_hsl_hue` oculta el campo en un panel nuevo frente a un backend anterior y evita que un panel antiguo envíe el campo. Es un giro global de matiz, no selección por rangos, máscara, scopes calibrados ni LUT. El contrato de render pasa a `clip-sdr-color-v2` para invalidar derivados de clips con color activo. Sin procesamiento ni render de contenido.
