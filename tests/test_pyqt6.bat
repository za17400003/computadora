@echo off
REM ── Prueba de PyQt6 para verificar interfaz gráfica ──
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ═══════════════════════════════════════════════════════════
echo  TEST PYQT6 - Verificar si interfaz gráfica funciona
echo ═══════════════════════════════════════════════════════════
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment no encontrado
    pause
    exit /b 1
)

echo Ejecutando test_pyqt6.py...
echo.

.venv\Scripts\python.exe test_pyqt6.py

if errorlevel 1 (
    echo.
    echo [ERROR] PyQt6 no funciona correctamente
    echo.
    echo Soluciones posibles:
    echo  1. Reinstalar PyQt6: pip install --upgrade PyQt6
    echo  2. Verificar Visual C++ redistributables instalados
    echo  3. Revisar logs en: .logs\
    echo.
)

pause
