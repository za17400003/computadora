@echo off
title Enciclopedia de los 7 Metales
cd /d "%~dp0"
cd ..

REM Si se pide cifrar/descifrar, ejecutar directamente
if "%~1"=="--cifrar" (
    .venv\Scripts\python.exe ENCICLOPEDIA\servidor_enciclopedia.py --cifrar
    pause
    exit /b
)
if "%~1"=="--descifrar" (
    .venv\Scripts\python.exe ENCICLOPEDIA\servidor_enciclopedia.py --descifrar
    pause
    exit /b
)

REM Matar procesos zombie en puerto 8080 antes de iniciar
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM Fase 1: Pedir contraseña (la cadena de Gevurá)
set GRIMORIO_AUTH_ONLY=1
.venv\Scripts\python.exe ENCICLOPEDIA\servidor_enciclopedia.py
set GRIMORIO_AUTH_ONLY=
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   Acceso denegado.
    timeout /t 3 >nul
    exit /b 1
)

REM Fase 2: Contraseña aceptada — lanzar servidor OCULTO (sin ventana de terminal)
echo   Iniciando servidor de la Enciclopedia en segundo plano...
start "" /B .venv\Scripts\pythonw.exe ENCICLOPEDIA\servidor_enciclopedia.py --servir
echo   La Enciclopedia se abrio en tu navegador.
echo   Esta ventana se cerrara en 3 segundos...
timeout /t 3 >nul
exit /b 0
