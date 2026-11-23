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

## Preparar dependencias en un entorno separado

Una vez terminada la extraccion, `PREPARAR_ESTUDIO.cmd` utiliza el Python 3.11
instalado para crear `.venv` dentro de esta copia. Si falta Python o es otra
version, muestra el error; no instala Python ni modifica ComfyUI.

Instala `requirements.txt` desde PyPI y comprueba dependencias e imports basicos
del servidor. No inicia el estudio ni modelos, no solicita credenciales y no
llama APIs de generacion. Los SDK de proveedores que figuran en los requisitos
no habilitan por si solos el uso de esos servicios. El arranque sigue siendo
`OPENMONTAGE_ESTUDIO.cmd`; este paso no certifica todas las herramientas.

`PREPARAR_ESTUDIO.cmd --check` solo informa del interprete, codigo, entorno y
huella de requisitos; no instala ni modifica archivos. Encontrar `.venv` no
significa que sus paquetes esten completos.
El diagnostico distingue requisitos cambiados desde la ultima instalacion,
entorno ausente, recibo ilegible y preparacion fallida. Un estado historico listo
se identifica como tal: consultar el recibo no vuelve a verificar los paquetes.

Para instalar sin conexion, `--wheelhouse "RUTA_DE_PAQUETES"` requiere una carpeta
con todos los wheels compatibles con Python 3.11 y la plataforma, incluidas las
dependencias transitivas. No consulta indices ni admite compilar paquetes
fuente en ese modo. Si faltan paquetes, falla y conserva el entorno para revisar.
No se incluye un lote offline de dependencias en el ZIP del codigo.

El recibo `.backlot/setup/environment.json` conserva estado, fecha y SHA256 de
los requisitos. Un fallo queda como `failed`; ejecutar de nuevo permite completar
el mismo entorno sin borrar sus archivos. Si existe `.venv` sin recibo propio,
se conserva y se detiene para evitar alterar un entorno preparado por otro medio.

Se impiden dos instalaciones simultaneas mediante `installation.lock`. Ante un
cierre forzado de Windows puede quedar ese bloqueo: comprobar primero que no
haya instalacion activa antes de quitarlo manualmente. No se elimina solo ni
se borra automaticamente un entorno con errores. El recibo no sustituye una
prueba real de arranque o inferencia, y los requisitos usan rangos de versiones:
dos instalaciones en fechas distintas pueden resolver paquetes diferentes.

La CI incluye una instalacion real en `.venv` con Python 3.11 en Windows y Linux,
seguida del arranque del servidor en loopback y consultas a salud, HTML,
JavaScript y bootstrap. Usa equipos temporales sin modelos; no demuestra el
funcionamiento de motores IA ni sustituye el arranque en el equipo del usuario.
