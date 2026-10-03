@echo off
REM ── Debug script para Computadora ──
REM Si la interfaz no aparece, ejecuta este script para ver qué está pasando

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ═══════════════════════════════════════════════════════════
echo  COMPUTADORA - DEBUG
echo ═══════════════════════════════════════════════════════════
echo.

REM ── 1. Verificar Python ──
echo [1] Verificando Python...
where python
if errorlevel 1 (
    echo    [ERROR] Python no encontrado
    exit /b 1
)
echo.

REM ── 2. Verificar versión ──
echo [2] Versión de Python...
.venv\Scripts\python.exe --version
echo.

REM ── 3. Verificar si PyQt6 funciona ──
echo [3] Probando PyQt6...
.venv\Scripts\python.exe -c "import PyQt6; print('[OK] PyQt6 importable')"
if errorlevel 1 (
    echo    [ERROR] PyQt6 no se puede importar
)
echo.

REM ── 4. Ver si computadora module existe ──
echo [4] Buscando módulo computadora...
if exist "computadora\__main__.py" (
    echo    [OK] computadora/__main__.py encontrado
) else (
    echo    [ERROR] computadora/__main__.py NO encontrado
)
echo.

REM ── 5. Intentar ejecutar con output ──
echo [5] Intentando ejecutar COMPUTADORA (con output directo)...
echo    (Si ves errores abajo, esos son los problemas)
echo.
.venv\Scripts\python.exe -m computadora

REM ── 6. Mostrar logs ──
echo.
echo ═══════════════════════════════════════════════════════════
echo  LOGS GENERADOS:
echo ═══════════════════════════════════════════════════════════
if exist ".logs" (
    dir .logs /b /od
    echo.
    echo Último log:
    for /f %%f in ('dir /b /od .logs\*.log') do set LASTLOG=.logs\%%f
    if defined LASTLOG (
        echo.
        echo [CONTENIDO - Últimas 30 líneas]
        type "!LASTLOG!" | findstr /R "^" | tail -30
    )
) else (
    echo [INFO] No hay logs aún (.logs no existe)
)

echo.
pause
