@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python scripts\setup_local_studio.py %*
) else (
  py -3.11 scripts\setup_local_studio.py %*
)
set "setup_result=%errorlevel%"
if not "%setup_result%"=="0" (
  echo.
  echo No se completo la preparacion. Revisa el error anterior.
  echo Manual: docs\INSTALACION_WINDOWS_C_ES.md
  pause
)
exit /b %setup_result%
