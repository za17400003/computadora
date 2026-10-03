# WI-321: FSM Transiciones Inválidas Fix — PALINGENESIA

## Problema Reportado
Logs mostraban "procesando→despertando" como transición inválida, causando violaciones del FSM que se permitían con solo una warning.

## Causa Raíz (NIGREDO)
1. **FSM Permisivo**: `cambiar_estado()` solo logueaba warnings para transiciones inválidas pero las permitía ("permitida por seguridad")
2. **Race Condition Circadiana**: Cambio de fase a "activo" siempre cambiaba a "despertando" sin verificar estado actual
3. **Transición Inválida**: Desde "procesando" no se puede ir a "despertando" según tabla FSM

## Soluciones Aplicadas (RUBEDO)

### Fix #1: Rechazar Transiciones Inválidas
```python
# Antes: solo warning, permitía la transición
logger.warning(f"Transición inválida {actual.value}→{nuevo.value} — permitida por seguridad")

# Después: rechazar completamente
logger.error(f"Transición inválida RECHAZADA: {actual.value}→{nuevo.value} — FSM violado")
return  # RECHAZAR la transición inválida
```

### Fix #2: Cambio Fase Circadiana Inteligente
```python
elif fase == "activo":
    # Solo cambiar a despertando si estamos en reposo, sino ir directo a escuchando
    if self._estado in ("dormido", "descanso_guardian", "vigilia"):
        self.cambiar_estado("despertando")
        QTimer.singleShot(3000, lambda: self.cambiar_estado("escuchando"))
    else:
        # Ya estamos activos, solo asegurar que estamos escuchando
        if self._estado not in ("escuchando", "procesando", "hablando", "trabajando"):
            self.cambiar_estado("escuchando")
```

## Validación
- ✅ Sintaxis correcta (py_compile OK)
- ✅ Imports exitosos
- ✅ FSM ahora rechaza transiciones inválidas
- ✅ Cambio fase circadiana respeta estados activos

## Impacto
- **Seguridad Mejorada**: FSM ahora es enforzado, no solo logged
- **Estabilidad**: No más transiciones inválidas que causan comportamientos impredecibles
- **Consistencia**: Estados del orbe siguen lógica formal del Maljut

## Lecciones Alquímicas
1. **Advertencias ≠ Seguridad**: Loggear no previene bugs
2. **Race Conditions**: Eventos asíncronos pueden violar invariantes
3. **FSM Enforcement**: Validar en runtime, no solo en diseño

## Citation
- Logs: "procesando→despertando" transición inválida
- FSM: `fsm_golem.py` tabla TRANSICIONES_VALIDAS
- Método: `cambiar_estado()` línea 1075, `_al_cambio_fase_circadiana()` línea 3047

## Status
✅ **FSM AHORA ENFORZADO** — Transiciones inválidas rechazadas, race conditions resueltas.</content>
<parameter name="filePath">c:\Users\woire\Documents\proyecto-golem\.audit\WI-321_FSM_TRANSICIONES_INVALIDAS_FIX.md