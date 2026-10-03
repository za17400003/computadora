@echo off
REM ── Launcher para Computadora sin bloqueo ──
REM Este script se ejecuta desde el shortcut del desktop
REM Abre COMPUTADORA en una ventana separada sin bloquear

cd /d "%~dp0"

REM Crear directorio de logs si no existe
if not exist ".logs" mkdir .logs

REM Obtener timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a-%%b)

REM Ejecutar en ventana separada (start /B = sin activar, start = con foco)
start "Computadora" cmd /k "call computadora_boot.bat"

exit /b 0
