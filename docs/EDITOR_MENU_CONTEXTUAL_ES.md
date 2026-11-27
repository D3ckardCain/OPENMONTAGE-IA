# Menús contextuales del editor

El editor muestra menús propios al usar clic derecho en clips, subtítulos, títulos, capas, fuentes importadas, el visor y zonas vacías de las pistas. Los menús reutilizan controles y comandos ya existentes del editor; abrirlos no edita el montaje.

Las acciones de clip respetan la selección y las capacidades anunciadas por el servidor. Dividir solo se habilita cuando el cursor deja material a ambos lados; las operaciones que afectan una selección bloqueada se deshabilitan. El elemento bloqueado no ofrece propiedades editables. La pista de audio ofrece quitar audio, mientras que las pistas de vídeo ofrecen conservar el hueco o cerrar el hueco si el backend admite esa operación.

`Shift+F10` y la tecla de menú contextual abren el menú del elemento enfocado. Flechas arriba/abajo, Inicio y Fin recorren acciones habilitadas; Escape cierra y devuelve el foco al elemento; clic exterior cierra el menú. El menú se limita al viewport. Los formularios nativos de la biblioteca y sus controles conservan su menú del navegador.

Verificación focalizada:

```powershell
$node = 'D:\OPENMONTAJE-IA\HERRAMIENTAS\NodeJS\22.23.5\node-v22.23.5-win-x64\node.exe'
& $node --check backlot\ui\editor-context-menu.js
& $node --check backlot\ui\editor.js
& $node --test tests\js\editor-context-menu.test.mjs
```

Los tests cubren las acciones por tipo, motivos de deshabilitación, apertura sin mutación, foco y teclado, cierre exterior y límites de posición en ventanas pequeñas y anchas. No prueban una escritura de proyecto contra el backend ni sustituyen la inspección interactiva de la instancia Studio; la activación visual en 4750 debe registrarse por separado.
