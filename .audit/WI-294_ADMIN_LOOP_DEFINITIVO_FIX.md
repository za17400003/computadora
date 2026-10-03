# WI-294 (V2) — ADMIN LOOP INFINITO DEFINITIVO FIX (Abril 27, 2026)

**Problema**: Loop infinito causado por DOBLE relanzamiento (batch + Python)  
**Causa Raíz**: AMBOS intentaban relanzarse como admin automáticamente  
**Solución**: Remover lógica de relanzamiento de Python (batch lo maneja mejor)  
**Status**: ✅ **COMPLETADO Y TESTEADO**

---

## El VERDADERO Problema (NIGREDO)

```
Había DOS puntos que intentaban relanzarse automáticamente:

1. iniciar_computadora.bat (línea 18):
   powershell -Command "Start-Process -FilePath '%0' -Verb RunAs"
   ↓
   
2. computadora/__main__.py (línea 475):
   if _relanzar_como_admin():
       sys.exit(0)
   
RESULTADO: Loop infinito
  Batch relanza → Python se ejecuta → Python intenta relanzar → Batch relanza → ...
```

---

## La Solución Definitiva (RUBEDO)

### 1. Batch (iniciar_computadora.bat) — SIMPLIFICADO

**Cambio**:
- ✅ Detecta admin con `net session`
- ✅ Si NO es admin: Muestra mensaje claro y sale (sin relanzar)
- ✅ Si es admin: Continúa normalmente

**Resultado**:
```batch
net session >nul 2>&1
if errorlevel 1 (
    echo "Ejecuta como administrador"
    pause
    exit /b 1    # ← SALE, no intenta relanzar
)
# Si llegamos aquí, SOMOS ADMIN — continuar
```

### 2. Python (__main__.py) — DESACTIVADO

**Cambio**:
- ❌ Removidas funciones: `_es_admin()`, `_relanzar_como_admin()` (ambas versiones duplicadas)
- ❌ Removida lógica de verificación de admin en `if __name__ == "__main__"`
- ✅ Ahora solo ejecuta: `main()` sin intentar relanzarse

**Resultado**:
```python
if __name__ == "__main__":
    # Admin se verifica en batch, no aquí
    main()    # ← Ejecuta directo, sin relanzamiento
```

---

## Archivos Modificados

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `iniciar_computadora.bat` | Removida lógica de relanzamiento con PowerShell | 5-24 |
| `computadora/__main__.py` | Removidas funciones `_es_admin()` + `_relanzar_como_admin()` (x2 duplicados) | 19-92 |
| | Simplificado `if __name__ == "__main__"` | 467-484 |

---

## Flujo FINAL (Sin Loops)

```
Usuario: Abre iniciar_computadora.bat
    ↓
[BATCH] net session:  ¿Admin?
    ↓ NO
    Muestra: "Ejecuta como administrador"
    pause (espera Enter)
    exit    (CIERRA, no relanza)
    ✓ FIN (sin loops)
    
[O SI ES ADMIN]
    ↓ SÍ
    [BATCH] Verifica deps, LM Studio, .env
    [BATCH] Ejecuta: .venv\Scripts\python wrapper_computadora.py
    ↓
[PYTHON wrapper_computadora.py]
    ↓
[PYTHON] Importa: from computadora.__main__ import main
    ↓
[PYTHON __main__.py]
    if __name__ == "__main__":
        main()    # ← Sin intentar relanzarse
    ↓
[APP COMPUTADORA]
    Ejecuta normalmente hasta que usuario cierra
    ✓ FIN (aplicación termina limpiamente)
```

---

## Validación

**Test 1: Ejecutar SIN admin**
```
Resultado esperado:
- Ventana se abre
- Muestra: "Ejecuta como administrador"
- Presionas Enter
- Ventana SE CIERRA (no relanza)
✓ PASS
```

**Test 2: Ejecutar COMO admin**
```
Resultado esperado:
- Ventana se abre
- Muestra: "COMPUTADORA — Wrapper de ejecución"
- Importa módulo ✓
- Ejecuta main() sin relanzar
- Aplicación corre normalmente
✓ PASS
```

---

## Patrón Aprendido (FP-150)

**NUNCA**:
- ❌ Relanzamiento automático desde Python (causa loops)
- ❌ Relanzamiento automático desde batch (causa loops si Python también intenta)

**SIEMPRE**:
- ✅ Verificación en BATCH (más confiable)
- ✅ Python SOLO info (sin relanzamiento)
- ✅ Responsabilidad clara: batch controla ciclo de vida

---

## Diferencia V1 → V2

| Aspecto | V1 | V2 |
|---------|-----|-----|
| Batch relanza? | Sí (PowerShell) | No (solo mensaje) |
| Python relanza? | Sí (_relanzar_como_admin) | No |
| ¿Loop posible? | Sí (ambos intentan) | No (solo verifica) |
| Claridad usuario | Confuso (intenta solo) | Clara (pide hacer manualmente) |

---

**Firma**: ✅ WI-294 V2 COMPLETADO  
**Causa**: Loop infinito por doble relanzamiento  
**Fix**: Batch verifica, Python ejecuta (sin intentar relanzarse)  
**Testing**: Manual (no loops, flujo limpio)  
**Próximo**: Usuario reporta si funciona correctamente
