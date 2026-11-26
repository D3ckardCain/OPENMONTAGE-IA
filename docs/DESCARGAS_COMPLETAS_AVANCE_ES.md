# Revisión completa de descargas — 26 noviembre 2026

Se cruzaron los cuatro inventarios guardados (base, adicionales, MADLAD y Qwen17), no solamente las tres últimas voces: 595 referencias, 49 grupos, 651 rutas físicas candidatas. Los grupos comparten archivos y no equivalen a 49 instalaciones independientes. Se localizaron 593 referencias. El inventario detallado y su avance están en `DESCARGAS_COMPLETAS_AVANCE_20261126.json`; es un corte provisional, no una certificación final.

C:, D: y F: contienen recursos. E: existe pero no contiene la raíz esperada. En F: aparecen recursos antes inventariados bajo E:. No se modificaron rutas de configuración automáticamente. La caché solo se reutiliza con identidad de volumen/archivo, tamaño y tiempos de modificación/creación coincidentes. El Qwen de #82 permanece resuelto: no se volvió a leer ni se abrió otro diagnóstico de disco.

Se excluyen temporales/incompletos y cambios de identidad antes/después de cada lectura. Se reutilizaron 150 resultados previos; el resto requiere hasta aproximadamente 1,37 TB de lectura, una sola vez por archivo. El proceso persiste cada resultado. Una cabecera válida, un hash coincidente y una prueba funcional son evidencias diferentes. La inspección PT por firma no ejecuta pickle ni acredita todos sus tensores. Las estructuras GGUF solo tienen validación de cabecera fija.

## Hallazgos concretos

- Wan2.2-Fun Control Camera: faltan `configuration.json` (1121 bytes) y `README_en.md` (17401 bytes) en la revisión `da1f119dcf5626b2fa41219ce42ac175752f3892`. No confundir el primero con `config.json`. No se sustituyó ninguna configuración.
- daVinci MagiHuman: el índice local JSON es válido pero enumera 13 fragmentos; la carpeta y el índice oficial fijado enumeran 7. El contenido difiere de la revisión `7fe95e50c11bd92bdadf94cd51dbec18427f8e0c`. Se conserva el original; esto no demuestra corrupción de los pesos. La carga queda bloqueada por índice incompatible hasta terminar la comprobación de los fragmentos.
- Dos tokenizadores Qwen grandes se contrastaron con Git blob SHA1 oficial porque no publican SHA256 LFS. Su SHA256 local queda registrado, sin presentarlo como SHA256 oficial.

## Prueba funcional nueva

MiniLM multilingüe, revisión `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, Apache-2.0: entorno aislado `.runtime/native-analysis/venv`, CPU, red bloqueada. Tres frases sintéticas españolas produjeron 3×384 valores finitos normalizados. Afinidad similar 0,8463 frente a 0,1820 para la frase ajena: comprobación funcional, no evaluación general de calidad. Se reutilizó el adaptador nativo y se registraron únicamente sus rutas nuevas. Otros ajustes permanecieron idénticos. Studio informa disponibilidad; su recibo genérico de inferencia aún no admite esta familia, por lo que la evidencia real se conserva aparte.

SigLIP: intento aislado con imagen sintética propia, CPU y red bloqueada. No terminó en el presupuesto breve; se detuvieron exclusivamente sus procesos de prueba. No se atribuye la demora al modelo, al disco ni a corrupción sin prueba. No se cargaron dos modelos a la vez.

No se modificaron `.venv`, ComfyUI ni entornos anteriores. No se repitieron síntesis, renders o CI aprobados. El proceso de hashes continúa y no debe lanzarse de nuevo mientras esté activo.
