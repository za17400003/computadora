@echo off
REM FP-153-156: Verificación rápida de implementación Fase 5
REM ══════════════════════════════════════════════════════════════════

echo.
echo 🔍 FP-153-156 QUICK VERIFICATION — Fase 5 (Abril 28)
echo ══════════════════════════════════════════════════════════════════
echo.

REM Verificar archivos creados
echo 📂 Verificando archivos creados...
set MISSING=0

if not exist computadora\utilidad\auto_instalar_deps.py (
    echo ❌ auto_instalar_deps.py FALTA
    set /a MISSING+=1
) else (
    echo ✅ auto_instalar_deps.py
)

if not exist computadora\geometria\teseracto_4d.py (
    echo ❌ teseracto_4d.py FALTA
    set /a MISSING+=1
) else (
    echo ✅ teseracto_4d.py
)

if not exist computadora\geometria\ferrofluido.py (
    echo ❌ ferrofluido.py FALTA
    set /a MISSING+=1
) else (
    echo ✅ ferrofluido.py
)

if not exist computadora\interfaz\animador_orbe_4d.py (
    echo ❌ animador_orbe_4d.py FALTA
    set /a MISSING+=1
) else (
    echo ✅ animador_orbe_4d.py
)

if not exist .audit\FP-154_NIGREDO_TESERACTO_4D.md (
    echo ❌ FP-154_NIGREDO_TESERACTO_4D.md FALTA
    set /a MISSING+=1
) else (
    echo ✅ FP-154_NIGREDO_TESERACTO_4D.md
)

if not exist _docs\FP-156_INTEGRACION_ORBE_4D.md (
    echo ❌ FP-156_INTEGRACION_ORBE_4D.md FALTA
    set /a MISSING+=1
) else (
    echo ✅ FP-156_INTEGRACION_ORBE_4D.md
)

if not exist tests\test_auto_install_deps.py (
    echo ❌ test_auto_install_deps.py FALTA
    set /a MISSING+=1
) else (
    echo ✅ test_auto_install_deps.py
)

if not exist CHANGELOG_FASE5.md (
    echo ❌ CHANGELOG_FASE5.md FALTA
    set /a MISSING+=1
) else (
    echo ✅ CHANGELOG_FASE5.md
)

echo.

if %MISSING% equ 0 (
    echo ✅ TODOS LOS ARCHIVOS PRESENTES
) else (
    echo ⚠️  %MISSING% archivo(s) FALTANTE(S)
)

REM Ejecutar tests
echo.
echo 🧪 Ejecutando test suite...
python tests\test_auto_install_deps.py
if errorlevel 1 (
    echo.
    echo ❌ TESTS FALLARON — No ejecutar boot aún
    goto end
)

echo.
echo ✅ VERIFICACIÓN COMPLETA — Sistema listo para:
echo    1. Integración en ventana_principal.py
echo    2. Testing completo en boot
echo.
echo Próximos pasos:
echo   - Leer _docs/FP-156_INTEGRACION_ORBE_4D.md para integración
echo   - Ejecutar .\iniciar_computadora_verificado.bat para boot
echo.

:end
pause
