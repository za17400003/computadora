# WI-CRIT-317: Fix AttributeError '_patron_sagrada' → '_patron_sagrado'

**Fecha**: Mayo 5, 2026 ~20:00 UTC
**Severidad**: 🔴 CRÍTICO (impide boot)
**Status**: ✅ FIXED
**Pipeline**: C (Bug fix crítico)

## Problema Reportado
```
AttributeError: 'OrbeGolem' object has no attribute '_patron_sagrada'. Did you mean: '_patron_sagrado'?
```
Error en `computadora/interfaz/ventana_principal.py:1694` durante paintEvent, impidiendo que la aplicación se inicie.

## Causa Raíz (NIGREDO)
Error tipográfico en línea 1694:
```python
if self._patron_sagrada and not _en_movimiento_render:  # ❌ '_patron_sagrada'
```
El atributo correcto definido en `__init__` (línea 647) es:
```python
self._patron_sagrado = ""  # ✅ '_patron_sagrado'
```

## Solución Aplicada (RUBEDO)
Corregido el error tipográfico:
```python
if self._patron_sagrado and not _en_movimiento_render:  # ✅ FIXED
```

## Validación
- ✅ Compilación exitosa sin errores
- ✅ Todas las referencias a `_patron_sagrado` consistentes en el codebase
- ✅ No hay otros errores similares

## Lecciones Alquímicas
1. **Fantasma Funcional**: Error tipográfico causa fallo completo en runtime
2. **Consistencia Atributo**: Verificar todas las referencias al cambiar nombres
3. **Boot Crítico**: Errores en paintEvent impiden UI completamente

## Archivos Modificados
- `computadora/interfaz/ventana_principal.py` (línea 1694)

## Status
✅ **RESUELTO** — COMPUTADORA puede iniciar nuevamente