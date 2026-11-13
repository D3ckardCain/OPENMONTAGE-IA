# MuseTalk 1.5: sustitución de máscara facial
Revisión: 2026-11-13. Estado: diseño por inspección estática; sin implementación,
inferencia, instalación ni validación visual.

## Problema
MuseTalk permite uso comercial de su modelo, pero remite a licencias propias de
sus auxiliares. La licencia MIT del código face-parsing no basta por sí sola
para cerrar la procedencia comercial del checkpoint 79999_iter.pth.
Su entrenamiento usa CelebAMask-HQ, con condiciones no comerciales. La consulta
upstream sobre permisos de los pesos sigue sin respuesta del autor observada:
https://github.com/zllrunning/face-parsing.PyTorch/issues/47
No se concluye automáticamente que todo peso entrenado herede la licencia de datos.
Estado: pendiente de aclaración; no cadena comercial aprobada.

## Evidencia de código
MuseTalk inspeccionado en 0a89dec45a0192b824e3cf4daf96c239440c5ed8:
- musetalk/utils/preprocessing.py obtiene 68 puntos faciales desde
  results.pred_instances.keypoints[0][23:91], con DWPose PTH.
  Actualmente devuelve cajas e imágenes, descartando esos puntos.
- musetalk/utils/face_parsing/__init__.py carga 79999_iter.pth y ResNet18.
- musetalk/utils/blending.py llama al parser para construir la máscara y luego
  usa una imagen gris, recorte y suavizado para componer el rostro.
  Las rutas normal y de preparación para tiempo real deben adaptarse.
- scripts/inference.py instancia FaceParsing; sustituir solo el archivo de pesos
  o la última función de blending no elimina esa carga.
Fuentes:
https://github.com/TMElyralab/MuseTalk/blob/0a89dec45a0192b824e3cf4daf96c239440c5ed8/musetalk/utils/preprocessing.py
https://github.com/TMElyralab/MuseTalk/blob/0a89dec45a0192b824e3cf4daf96c239440c5ed8/musetalk/utils/blending.py

## Alternativa propuesta sin nuevos pesos
Construir una máscara geométrica de región de habla desde los puntos DWPose ya
calculados. Conservar confianza, coordenadas flotantes, cara seleccionada y
transformación entre fotograma, recorte facial y recorte expandido.
Verificar el mapa de índices de boca contra los metadatos de la configuración;
no asumir que cualquier modelo de 68 puntos tiene el mismo orden.

1. Conservar los landmarks y sus confianzas en el artefacto de preprocesamiento.
2. Construir polígono de labios con margen proporcional a cara y apertura; evaluar
   la cobertura de mejillas/mentón para no cortar el movimiento generado.
3. Limitar región y suavizar bordes; proteger ojos y nariz.
4. Suavizar temporalmente por identidad de personaje, reiniciando en cortes.
5. Rechazar frames con landmarks insuficientes, perfil extremo, oclusiones,
   ambigüedad de identidad o geometría inválida. No continuar silenciosamente con
   una máscara de otra cara.
6. Reemplazar instanciación del parser en generación normal, realtime y demo,
   además de las dos rutas de composición. Invalidar cachés de máscaras antiguas.

No es segmentación semántica y puede fallar con manos ante la boca, barbas,
perfiles y movimiento de mentón. No prometer equivalencia de calidad.
No añadir SAM2 como dependencia automática: distinguir boca/piel/objeto oclusor
requiere adaptación y pruebas, no solo segmentación genérica.

## Descargas y límites
No se necesita descargar otro checkpoint para investigar esta alternativa.
Conservar 79999_iter.pth y ResNet18 si ya se descargaron, sin borrarlos.
La revisión NO certifica DWPose, S3FD, Whisper o VAE como cadena íntegra, ni
resuelve por sí sola los términos de todos los datos/auxiliares.
Si se elimina por completo el parser, revisar si ResNet18 deja de ser necesario.
S3FD continúa siendo usado por el preprocesamiento actual.

## Pruebas futuras necesarias
Cuando el usuario autorice implementación/inferencia: primero máscaras sintéticas
(coordenadas, clipping y ausencia de NaN); después diálogo ES/EN de un personaje,
perfiles, boca abierta, barba, manos/objetos, dos personajes y cambios de plano.
Comprobar identidad, halos, nariz/ojos intactos y continuidad. Los tests geométricos
no sustituyen la evaluación visual. No declarar sustitución lista hasta entonces.
