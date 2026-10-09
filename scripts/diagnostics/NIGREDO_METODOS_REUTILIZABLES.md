# NIGREDO — Métodos No Usados: ¿Funcionalidad Real? (Junio 1, 2026)

## Auditoría de Métodos Inyectados

### Método 1: `_valida_a_si_misma()` (Nivel 0: Recursión)

**Código Real**:
```python
def _valida_a_si_misma() -> bool:
    return (
        hasattr(cerebro_computadora, 'historial') and
        hasattr(cerebro_computadora, 'modelo') and
        getattr(cerebro_computadora, 'ollama_disponible', False)
    )
```

**¿Funcionalidad Real?**
✅ SÍ — Verifica 3 precondiciones críticas:
- `historial` — existe
- `modelo` — existe
- `ollama_disponible` — es True (no solo existe)

**¿Puede usarse?**
✅ SÍ — Ideal para:
- Validación pre-POST (antes de _pensar_con_herramientas)
- Health check en boot
- Detección de corrupción de estado

**Ubicación Óptima**:
```python
# En _pensar_con_herramientas (línea ~4170)
if not self._valida_a_si_misma():
    logger.error("CerebroComputadora no está validado")
    return "Sistema no listo. Reintentando..."
```

---

### Método 2: `_verificar_estructura_presente()` (Nivel 1: Estructura)

**Código**:
```python
def _verificar_estructura_presente() -> bool:
    return hasattr(cerebro_computadora, '_ciclo_actual') and all(
        fase in getattr(cerebro_computadora._ciclo_actual, 'fases', [])
        for fase in fases
    )
```

**¿Funcionalidad Real?**
❌ NO — Depende de `_ciclo_actual` que **NO existe en nlu.py**

**Búsqueda en nlu.py**:
```bash
grep "_ciclo_actual" computadora/cerebro/nlu.py
# Resultado: 0 matches
```

**Conclusión**: Método ortogonal a la arquitectura actual. Infraestructura no existe.

**Recomendación**: ❌ ELIMINAR (no es reutilizable sin refactor mayor)

---

### Método 3: `_reglas_activas, _anti_colateral_mode` (Nivel 2: Combinatoria)

**Código**:
```python
reglas = [
    "R1: Max 6 archivos por ciclo",
    "R2: Max 500 líneas por cambio",
    "R3: Snapshot obligatorio",
]
cerebro_computadora._reglas_activas = reglas
cerebro_computadora._anti_colateral_mode = True
```

**¿Funcionalidad Real?**
❌ NO — Solo asigna listas y flags
- Sin lógica de validación
- Sin comparación contra reglas
- Sin enforcement

**Búsqueda en nlu.py**:
```bash
grep "_reglas_activas\|_anti_colateral_mode\|_en_estructura" computadora/cerebro/nlu.py
# Resultado: 0 matches (nunca se usan)
```

**Conclusión**: Puramente decorativo.

**Recomendación**: ❌ ELIMINAR

---

### Método 4: `_verificar_verdad()` (Nivel 3: Verdad)

**Código**:
```python
def _verificar_verdad(respuesta: str, texto_usuario: str | None = None) -> dict:
    return {
        "logica": self._es_logicamente_consistente(respuesta),
        "empirica": self._es_empiricamente_verificable(respuesta, texto_usuario),
        "axiomatica": self._respeta_axiomas(respuesta),
        "revelada": self._tiene_mensaje_profundo(respuesta),
    }
```

**¿Funcionalidad Real?**
✅ SÍ — Llama 4 métodos validación que existen en nlu.py

**¿Puede usarse?**
✅ SÍ — **YA SE USA** (línea 4089 en nlu.py)

**Ubicación Actual**:
```python
# nlu.py línea 4077-4085
def _verificar_verdad(self, respuesta: str, texto_usuario: str | None = None) -> dict:
    return {
        "logica": self._es_logicamente_consistente(respuesta),
        "empirica": self._es_empiricamente_verificable(respuesta, texto_usuario),
        "axiomatica": self._respeta_axiomas(respuesta),
        "revelada": self._tiene_mensaje_profundo(respuesta),
    }
```

**Conclusión**: ✅ MANTENER (YA está en uso)

---

### Método 5: `_decodificar_mensaje()` (Nivel 4: Comunicación)

**Código**:
```python
def _decodificar_mensaje(respuesta: str) -> dict:
    return {
        "literal": respuesta,  # ¿Qué se hizo?
        "moral": getattr(cerebro_computadora, '_extraer_principio', lambda x: 'N/A')(respuesta),
        "profunda": getattr(cerebro_computadora, '_extraer_significado', lambda x: 'N/A')(respuesta),
    }
```

**¿Funcionalidad Real?**
✅ SÍ — Descompone respuesta en 3 niveles semánticos

**Métodos Dependientes** (búsqueda en nlu.py):
```bash
grep -n "_extraer_principio\|_extraer_significado" computadora/cerebro/nlu.py
# Resultado: 
#   4069: def _extraer_principio(self, respuesta: str) -> str:
#   4074: def _extraer_significado(self, respuesta: str) -> str:
```

✅ **EXISTEN** en nlu.py (líneas 4069, 4074)

**¿Puede usarse?**
✅ SÍ — Ideal para:
- Auditoría de respuestas (qué se dijo, qué principio, qué significa)
- Logging estructurado post-respuesta
- Análisis de intención vs comunicación

**Ubicación Óptima**:
```python
# Después de respuesta N2/N3 completada (línea ~1560)
if respuesta_ollama:
    decodificacion = self._decodificar_mensaje(respuesta_ollama)
    logger.debug(f"Decodificación: Literal: {decodificacion['literal'][:50]}, "
                 f"Principio: {decodificacion['moral']}, "
                 f"Profundo: {decodificacion['profunda']}")
```

---

## Síntesis: Métodos Reutilizables

| Método | Funcional? | Usable? | Acción | Ubicación Óptima |
|--------|-----------|--------|--------|------------------|
| `_valida_a_si_misma()` | ✅ | ✅ | **INTEGRAR** | Pre-POST validation |
| `_verificar_estructura_presente()` | ❌ | ❌ | **ELIMINAR** | N/A (infraestructura inexistente) |
| `_reglas_activas`, `_anti_colateral_mode` | ❌ | ❌ | **ELIMINAR** | N/A (decorativo) |
| `_verificar_verdad()` | ✅ | ✅ | **MANTENER** | Ya en uso (línea 4089) |
| `_decodificar_mensaje()` | ✅ | ✅ | **INTEGRAR** | Post-respuesta logging |

---

## Plan de Acción

### MANTENER (Sin cambios)
- `_verificar_verdad()` — Ya funciona

### INTEGRAR (Hacer reales)
- `_valida_a_si_misma()` — Usar en validación pre-POST
- `_decodificar_mensaje()` — Usar en logging post-respuesta

### ELIMINAR (Decorativo)
- `_verificar_estructura_presente()` — Infraestructura no existe
- `_reglas_activas`, `_anti_colateral_mode`, `_en_estructura` — Sin lógica

### CAMBIAR LOGS
- Log "5 Leyes inyectadas" → "2 métodos integrados (validación + verdad)"
- Log "Renovación completada" → "Renovación completada (métodos: _valida_a_si_misma, _verificar_verdad, _decodificar_mensaje)"

---

**Status**: 🔴 NIGREDO COMPLETO — Métodos analizados, plan de integración definido
