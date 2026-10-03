@echo off
REM Test simple: Verificar que el batch detecta admin correctamente
REM Este script NO relanza nada, solo verifica e informa

echo [TEST] Verificando permisos de administrador...
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo ✗ NO ERES ADMIN — Este es el mensaje que deberías ver si ejecutas sin permisos
    echo.
    echo Solución: Haz clic derecho en computadora_boot.bat y selecciona "Ejecutar como administrador"
    pause
    exit /b 1
)

echo ✓ ERES ADMIN — Sistema puede continuar normalmente
echo.
echo Flujo correcto:
echo   1. Verificación admin: ✓
echo   2. Verificación deps:  [SIGUIENTE]
echo   3. Ejecutar Python:    [SIGUIENTE]
echo.
pause
exit /b 0
