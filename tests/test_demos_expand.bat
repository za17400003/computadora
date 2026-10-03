@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo TEST: DEMOS EXPANDIDAS DE COMPUTADORA
echo ═══════════════════════════════════════════════════════════════════════════════
echo.

REM Verificar que Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está disponible en PATH
    pause
    exit /b 1
)

echo Arrancando test de demostraciones expandidas...
echo.
echo Las tres demostraciones se ejecutarán automáticamente:
echo - Demo 0 (Emet):     2 segundos
echo - Demo 1 (Maljut):   65 segundos
echo - Demo 2 (Gevurá):   130 segundos
echo.
echo Tiempo total estimado: ~3 minutos
echo.

python ..\scripts\demos\demo_expandido_manual.py

pause
