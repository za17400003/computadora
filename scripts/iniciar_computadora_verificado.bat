@echo off
REM FP-153: Boot script — Verifica e instala dependencias faltantes ANTES de iniciar Computadora
REM ════════════════════════════════════════════════════════════════════════════════════════════

echo.
echo 🔧 FP-153: BOOT VERIFIER — Verificando dependencias...
echo.

REM Ejecutar el auto-instalador de Python
python -m computadora.utilidad.auto_instalar_deps

if errorlevel 1 (
    echo.
    echo ⚠️  Advertencia: Algunas dependencias no se pudieron verificar.
    echo El sistema intentará continuar, pero puede haber errores.
    echo.
)

echo.
echo ✅ Verificación completada. Iniciando Computadora...
echo.

REM Iniciar Computadora
python -m computadora
