@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m backlot studio
) else (
  python -m backlot studio
)
if errorlevel 1 (
  echo.
  echo No se pudo abrir el estudio. Revisa Python y las dependencias del proyecto.
  echo Manual: docs\ESTUDIO_PRODUCCION_ES.md
  pause
)
endlocal
