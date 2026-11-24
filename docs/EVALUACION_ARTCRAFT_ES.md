# ArtCraft — evaluación #49

24-11-2026 UTC. [Snapshot de571bb2](https://github.com/storytold/artcraft/tree/de571bb2f8351ade6c742d41caea81f11f595801),
HEAD consultado. No se instaló, compiló, abrió sesión ni generó contenido. Versiones:
`artcraft-native`0.1.0 y frontend0.0.1; no son una versión comercial unificada.

## Decisión y comparación

Interesa el modelo de composición y transferencia de escenas, no el catálogo cloud.
Priorizar un contrato neutral de capas/cámara/poses que sirva a Blender/Krita/Three.js
existentes. No instalar otro estudio ni cambiar GitHub Dark, proveedor o ComfyUI.

| Área | Existente en OPENMONTAGE | Aporte evaluable |
|---|---|---|
| Capas2D | Krita registrado e inspección KRA; composición/overlays y artefactos de escena | Interacción de capas/transformaciones y preparación visual; registro KRA no equivale a pintar/editar. Reusar archivos locales, no importar recursos de demostración |
| Escena3D | BlenderWorld, ThreejsWorld, planes de escena y herramientas de rig/poses | Layout de objetos/cámara compartible y edición visual reproducible. No reemplazar Blender por otro renderer ni afirmar exportación lossless sin mapa de ejes/unidades |
| Pose/cámara | Contratos y herramientas de animación existentes | Intercambio de jerarquía, pose y referencia con IDs estables; controles visuales son distintos de generar un personaje |
| Generación | Adaptadores locales/ComfyUI, modelos elegidos y presupuesto0 | No se encontró ruta ComfyUI en los paths del árbol revisado; proveedor ArtCraft/FAL/Midjourney no es backend local gratuito |
| Persistencia | JSON/checkpoints/hashes y procedencia por proyecto | PageSceneStore/adapter pueden orientar un formato de escena, pero almacenamiento de UI/servicio no sustituye el expediente local ni garantiza round-trip |

Fuentes: [README](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/README.md),
[PageSceneStore](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/frontend/libs/components/pagescene/src/lib/PageSceneStore.ts),
[adapter](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/frontend/libs/components/pagescene/src/lib/adapter.ts),
[proveedores](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/artcraft-native/src/backend/providers/mod.rs).
Locales: `tools/graphics/{blender_world,threejs_world}.py`, `lib/krita_document.py`,
`lib/scene_batch.py`, esquemas `scene_plan`, `rig_plan`, `pose_library`.

## Arquitecturas y dependencias: evitar una conclusión por el README

El árbol contiene la aplicación Rust/Tauri con frontend TypeScript/Nx/Vite y una
aplicación distinta `artcraft-native` egui/eframe0.36. El workspace incluye ambas
y tiene default-member Tauri. No atribuir a egui todas las funciones del editor3D
web heredado, ni asumir que el escritorio completo carece de webview: su paquete
nativo incluye wry para login Midjourney.

[_docs/dev_setup.md](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/_docs/dev_setup.md)
cita Rust, npm/Node, TauriCLI2.10 y scripts Windows; menciona Node24.13 probado y un
mínimo20+ del launcher Unix. No es una prueba de compatibilidad con el Node actual.
[Cargo.toml](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/Cargo.toml)
y [paquete nativo](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/artcraft-native/Cargo.toml)
incluyen Tokio/reqwest, codecs, audio y librerías de UI/archivos. La elección de
superficie determina dependencias; no se preparó toolchain ni se ejecutaron launchers.

## Licencias, recursos y costo $0

Código a elección [MIT](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/LICENSE-MIT)
o [Apache2.0](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/LICENSE-APACHE).
Conservar avisos y cambios si se reutiliza código; OPENMONTAGE mantiene AGPLv3.
[NOTICE](https://github.com/storytold/artcraft/blob/de571bb2f8351ade6c742d41caea81f11f595801/NOTICE)
es decisivo: marcas/logo ArtCraft no están incluidos; enumera terceros zlib,
MIT/Apache, CC-BY4 y fuentes OFL. También excluye expresamente sonidos Nintendo,
memes, skyboxes de terceros, una animación MMD y renders Mixamo. No copiar esos
assets ni asumir permiso porque están en el repositorio.

Generación mediante proveedores externos requiere sus cuentas/condiciones; no se
ha demostrado costo0. El módulo nativo revisado enumera ArtCraft/Midjourney/FAL y
explica que vídeo se envía a ArtCraft en esa ruta. Excluir esas llamadas y servicios
del alcance local; no usar sesiones/cookies ni suscripciones como sustituto de API.
Las licencias de modelos/recursos se revisan aparte; no se heredan del código abierto.

## Offline y persistencia

Manipular una escena con recursos locales puede ser una función offline futura;
la operación integral del producto con login, biblioteca, descarga y generación
remota no está acreditada offline. Se debe separar importar, editar, guardar,
previsualizar y generar. Portar solo datos/algoritmos elegibles con recursos propios,
sin llamadas de cuenta, catálogos cloud o telemetría requerida. No se verificó un
modo local completo ni un adaptador listo para nuestro ComfyUI.

## Tareas futuras con aceptación

| Prioridad | Tarea | Aceptación |
|---|---|---|
| P0 | Selección de componente y derechos | Fijar archivos/superficie exactos, licencia/NOTICE y dependencias; excluir assets no cubiertos y rutas cloud; ninguna conexión obligatoria de cuenta |
| P0 | Contrato neutral de escena | Capas, IDs, transforms, jerarquía, cámara, ejes/unidades y referencias con hash; round-trip JSON sintético detecta pérdidas, no modifica originales |
| P1 | Puente Blender/Krita | Reusar rutas guardadas y formatos compatibles; pruebas de datos/validadores simulados, sin crear geometría o pintar; informes de incompatibilidad explícitos |
| P1 | Edición reversible y procedencia | Candidato separado, revisión y undo/redo/snapshots; rutas confinadas y cambios por usuario/agente distinguibles; fallos de guardado y versiones obsoletas cubiertos |
| P2 | Aislamiento offline | Plan de test con red denegada y assets sintéticos propios, sin login/modelos nuevos; medir UI/GPU/render solo en otra fase autorizada |

Bloqueos de adopción: dependencias cloud no sustituidas, derechos de assets y formato
de intercambio por definir. No bloquean concluir esta evaluación. No se afirma
calidad, compatibilidad gráfica o paridad entre las dos aplicaciones upstream.
