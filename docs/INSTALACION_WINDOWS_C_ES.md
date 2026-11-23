# Copia actualizada en C:

`scripts/prepare_windows_studio.ps1` prepara el codigo completo de la rama
`feat/local-agent-research-foundation` en `C:\OPENMONTAGE-IA`. Resuelve el commit
al iniciar y descarga el ZIP de ese commit, no el de la rama principal antigua.
Requiere conexion a GitHub y Windows PowerShell 5.1 o PowerShell 7.

Se detiene si el destino existe. Extrae en una carpeta temporal propia, verifica
las rutas y archivos minimos y mueve la copia terminada al destino. Conserva
`INSTALACION_LOCAL.json` con origen, commit y SHA256 del archivo recibido.
Ese hash es una huella del archivo descargado, no una firma independiente.

`-BlenderPath` permite registrar un `blender.exe` existente sin ejecutarlo.
Los modelos y aplicaciones de D: o E: permanecen en sus ubicaciones.

Esto prepara solamente codigo: no instala Python, dependencias, modelos ni
ejecuta inferencia. El siguiente paso es crear `.venv` con Python compatible,
instalar `requirements.txt` y usar `OPENMONTAGE_ESTUDIO.cmd`. No utilizar ni
modificar el Python integrado de ComfyUI. Las dependencias requieren conexion
durante su instalacion; la disponibilidad offline posterior depende de cada
herramienta y de los recursos locales ya configurados.

Para pruebas sin red se admiten `-ArchivePath` y `-Revision` explicitos.
`tests/windows/test_prepare_windows_studio.ps1` usa archivos sinteticos en una
carpeta temporal y nunca escribe en `C:\OPENMONTAGE-IA`.
