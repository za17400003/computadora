# WI-294 — Admin Permisos Loop Infinito FIX (Abril 27, 2026)

**Problema**: Loop infinito en escalación de admin que bloqueaba inicio de COMPUTADORA  
**Causa Raíz**: `wrapper_computadora.py` intentaba relanzarse con `ShellExecuteW`, causando re-detección de no-admin  
**Solución**: Mover detección de admin al .bat (más confiable), simplificar wrapper  
**Status**: ✅ **COMPLETADO**

---

## El Problema (NIGREDO)

**Síntoma**:
```
Usuario: python iniciar_computadora.bat
↓
iniciar_computadora.bat lanza wrapper_computadora.py
↓
wrapper_computadora.py detecta "no es admin"
↓
wrapper_computadora.py relanza con ShellExecuteW
↓
Abre nueva ventana/proceso BUT no detecta admin correctamente
↓
Loop infinito: intenta relanzar nuevamente
↓
Sistema bloqueado
```

**Root Cause**: 
1. `ShellExecuteW(None, "runas", ...)` no es confiable desde Python
2. El proceso relanzado no detecta admin correctamente
3. Python intenta relanzarse nuevamente → loop

---

## La Solución (RUBEDO)

### 1. Mover Detección de Admin al Batch

**iniciar_computadora.bat** (primeras líneas):
```batch
REM FASE 1: Detectar admin ANTES de lanzar Python
net session >nul 2>&1
if errorlevel 1 (
    REM No es admin — relanzar CON admin (ONCE, con PowerShell)
    powershell -Command "Start-Process -FilePath '%0' -Verb RunAs" >nul 2>&1
    timeout /t 2 /nobreak >nul 2>&1
    exit /b 0
)
REM Si llegamos aquí, SOMOS ADMIN — continuar normalmente
```

**Por qué es mejor**:
- `net session` es la forma estándar en Windows para detectar admin
- PowerShell `.Verb RunAs` es más confiable que `ShellExecuteW`
- Se relanza UNA SOLA VEZ (no hay loop)
- El wrapper Python simplemente verifica estado (no intenta relanzarse)

### 2. Simplificar wrapper_computadora.py

**Cambio**:
- Removida función `relanzar_como_admin()`
- `es_admin()` ahora solo informa estado (lectura)
- No intenta relanzar en ningún caso

**Nueva estructura**:
```python
def main():
    admin_status = es_admin()
    print(f"Permisos: {'✓ ADMINISTRADOR' if admin_status else 'Normal'}")
    # Continuar normalmente sin intentar relanzarse
    from computadora.__main__ import main as computadora_main
    computadora_main()
```

---

## Archivo Modificado

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `iniciar_computadora.bat` | + Detección admin en FASE 1 | 5-24 |
| `wrapper_computadora.py` | - `relanzar_como_admin()`, simplificado | 1-90 |

**Total cambios**: ~15 líneas (muy limpio)

---

## Flujo Nuevo (NO Loop)

```
Usuario: iniciar_computadora.bat
    ↓
[BATCH FASE 1] net session detecta: ¿admin?
    ↓ NO
    powershell relanza con .Verb RunAs (UAC popup)
    ↓
[BATCH FASE 1 RERUN] net session detecta: ¿admin?
    ↓ SÍ
    Continúa con FASE 2+ (verificación deps, etc)
    ↓
[PYTHON] wrapper_computadora.py (simplificado)
    ↓
[PYTHON] from computadora.__main__ import main
    ↓ ✓ Ejecuta normalmente
```

**Diferencia clave**:
- Antes: Loop en Python (relanzamiento infinito)
- Ahora: Detección + relanzamiento ÚNICO en Batch, Python ejecuta directo

---

## Validación (PALINGENESIA)

**Test 1: Ejecutar como usuario normal**
```
esperado: UAC popup → relanza con admin
resultado: ✓ PASS (no hay loop)
```

**Test 2: Ejecutar ya como admin**
```
esperado: Sin popup, ejecuta directo
resultado: ✓ PASS
```

**Test 3: Cerrar durante relanzamiento**
```
esperado: Script termina limpiamente
resultado: ✓ PASS (timeout evita hang)
```

---

## Compromisos Futuros

- FP-148: Aplicar patrón "Batch checks, Python informa" a otros scripts (.bat)
- FP-149: Testing de permisos en suite de tests

---

**Firma**: ✅ WI-294 COMPLETADO  
**Causa**: Loop infinito en escalación de permisos  
**Fix**: Mover detección de admin a Batch (más confiable)  
**Impacto**: Sistema ahora arranca sin loops, escalación UAC funciona 1 sola vez  
**Testing**: Manual + visual (sin loop)
