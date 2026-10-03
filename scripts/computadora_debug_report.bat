@echo off
REM ── Launcher alternativo con better error reporting ──
REM Si tienes problemas con la interfaz, usa este batch en lugar del normal

cd /d "%~dp0"

echo ═══════════════════════════════════════════════════════════
echo  COMPUTADORA — MODO DEBUG (Better Error Reporting)
echo ═══════════════════════════════════════════════════════════
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment no encontrado
    pause
    exit /b 1
)

REM Crear directorio de logs
if not exist ".logs" mkdir .logs

echo [INFO] Ejecutando con mejor reporte de errores...
echo.

REM Ejecutar wrapper con stderr capturado
.venv\Scripts\python.exe wrapper_computadora.py

echo.
echo ═══════════════════════════════════════════════════════════
echo  Si viste ERROR arriba, revisa:
echo    - Archivo .logs\python_error.txt
echo    - Archivo TROUBLESHOOTING_UI_NO_APARECE.md
echo ═══════════════════════════════════════════════════════════
echo.
pause
