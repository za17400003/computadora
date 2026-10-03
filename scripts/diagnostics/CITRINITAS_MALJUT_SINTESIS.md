# CITRINITAS — MALJUT: Síntesis y Optimización

**Fecha**: Junio 1, 2026  
**Fase**: CITRINITAS (Iluminación, síntesis dorada)  
**Basado en**: [ALBEDO_MALJUT_SOLUCIONES.md](ALBEDO_MALJUT_SOLUCIONES.md)

---

## SÍNTESIS EJECUTIVA

Analizadas todas las soluciones ALBEDO. Se propone **estrategia MVP secuencial**:

1. **FASE 1 (MVP crítico)**: Arreglar 4 bloqueadores (ID 1,2,3,5) — 8h
2. **FASE 2 (Solidificación)**: Arreglar 8 problemas media — 8h  
3. **FASE 3 (Deuda técnica)**: 5 refactors arquitectónicos — 20h

**Total**: 36 horas a lo largo de **3 semanas**.

---

## TRADE-OFFS ANALIZADOS

### Trade-off 1: QMutex vs Atomic vs Signal

**ID 1 (Race condition)**

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| **QMutex** | Estándar Qt, robusto | +2-5% CPU | ✅ ELEGIDA |
| **QAtomicPointer** | Ultra-rápido | Requiere C++14 features | NO (código Python) |
| **PyQt Signal** | Qt-native | Asincrono, latencia | NO (necesita síncrono) |

**Decisión**: QMutex (patrón estándar Qt)

---

### Trade-off 2: Try-except en loop vs Exception handler centralizado

**ID 2 (Memory leak)**

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| **Try-except local** | Fácil, específico | Más líneas código | ✅ ELEGIDA |
| **Particula.__del__()** | Cleanup automático | Nondeterministic | NO (GC impredecible) |
| **Context manager** | Pythonic | Overcomplicated | NO |

**Decisión**: Try-except local (claro, determinístico)

---

### Trade-off 3: Threading.Timer vs QThread refactor

**ID 3 (Deadlock)**

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| **Threading.Timer** | Evita Qt event loop | No integrado Qt | ALTERNATIVA |
| **QThread refactor** | Qt-native, integrado | +20h refactor | ✅ ELEGIDA (con precaución) |
| **Usar QTimer pero sin bloqueos** | Mínimo cambio | Requiere auditar msleep() | PREPARATORIA |

**Decisión**: QThread refactor + auditar msleep() en MotorProactividad ANTES

---

### Trade-off 4: Gradual offset reset vs Instant reset

**ID 5 (Render offset)**

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| **Gradual (lerp 0.1)** | Suave visualmente | +1-2 atributos | ✅ ELEGIDA |
| **Instant** | Rápido código | Saltos visuales | NO (peor UX) |
| **Parametrizable** | Flexible | Overcomplicated | FUTURO (FP-050) |

**Decisión**: Gradual con timer (best visual quality)

---

## OPTIMIZACIONES IDENTIFICADAS

### Opt 1: Cache geografía de pantalla

**Actualmente**: `_obtener_info_escritorio()` llamado cada 500ms, recalcula todo.

**Optimización**:
```python
# Cache pantallas cada 5s
self._pantallas_cache = None
self._pantallas_cache_ts = 0
self._pantallas_cache_interval = 5.0

def _actualizar_pantallas_cache(self):
    if time.time() - self._pantallas_cache_ts > self._pantallas_cache_interval:
        self._pantallas_cache = _obtener_pantallas_win32()
        self._pantallas_cache_ts = time.time()

# En _tick(): usar cache en lugar de recalcular
```

**Impacto**: 1-2ms ahorrados por tick (~0.2% CPU, trivial pero acumula)

---

### Opt 2: Heatmap debounce + compresión

**Actualmente**: JSON write en disco cada 500ms.

**Optimización**:
```python
# Debounce a 5s, además comprimir JSON (gzip)
self._heatmap_save_counter = 0
self._heatmap_save_interval = 10  # 10 ticks * 500ms = 5s

if self._heatmap_save_counter >= self._heatmap_save_interval:
    self._heatmap_save_counter = 0
    self._guardar_heatmap_comprimido()  # gzip JSON → 80% menor tamaño
```

**Impacto**: IO reducido 5×, disk usage 5× menor

---

### Opt 3: State machine para decisiones (en lugar de ticks planos)

**Actualmente**: `_tick()` tiene lógica plana (if estorba → esquiva, if inactivo → reubicar, etc.)

**Optimización**:
```python
# Usar FSM para secuenciar decisiones
from enum import Enum, auto

class EstadoComportamiento(Enum):
    LIBRE = auto()
    ESQUIVANDO = auto()
    REUBICANDO = auto()
    REGRESANDO = auto()

# Solo una acción por tick, transitions explícitas
```

**Impacto**: Código más legible, debugging más fácil (+1-2h refactor pero vale la pena)

---

## PLAN DE IMPLEMENTACIÓN DETALLADO

### FASE 1: MVP Crítico (9h)

```
Commit 1 (2h): QMutex + Race condition fix (ID 1)
  - Agregar _mutex_pos a MotorProactividad
  - Lock/unlock en _tick()
  - Lock/unlock en _interpolar_movimiento()
  - Test: Stress con 2 threads

Commit 2 (1h): Try-except particulas (ID 2)
  - Envolver p.actualizar() con try-except
  - Log de particulas removidas
  - Test: Inyectar excepción en actualizar()

Commit 3 (3h): Auditar MotorProactividad para deadlock (ID 3)
  - Buscar todos msleep() en MotorProactividad
  - Reemplazar con QTimer.singleShot() o threading
  - Test: 60s sin freeze

Commit 4 (2h): Gradual offset reset (ID 5)
  - Agregar _offset_collapse_timer
  - Implementar lerp en _interpolar_movimiento()
  - Test: Esquiva → collapse suave visualmente

Commit 5 (1h): Fix pre-boot early-exit (WI-MALJUT-002 part 2)
  - Mover repaint() antes de early-exit en pre-boot también (L1260)
  - Test: Pre-boot fluido sin freeze
```

**QA después Fase 1**:
- ✅ Sin race conditions (debugger + stress test)
- ✅ Sin memory leaks (valgrind / PSutil)
- ✅ Sin deadlocks (60s runtime limpio)
- ✅ Visual suave (capture video, sin saltos)

---

### FASE 2: Solidificación (8-10h)

```
Commit 6 (0.5h): Usar cache paintEvent (ID 4)
  - Reemplazar mapFromGlobal() con self._cached_cursor_local
  
Commit 7 (1h): Clamp cursor zone (ID 6)
  - Validar _estorba() contra pantalla
  
Commit 8 (2h): Multi-monitor dinámico (ID 7)
  - Actualizar _pantalla cada 5s basado en cursor
  
Commit 9 (1.5h): Wall-sliding mejorado (ID 8)
  - Agregar fallback a borde si flee escapa
  
Commit 10 (1h): Heatmap debounce (ID 9)
  - Reducir writes de JSON a 5s
  
Commit 11 (1h): FSM state sync (ID 10)
  - Conectar signal de cambio estado
  
Commit 12 (0.5h): Validación heatmap (ID 11)
  - Check pantalla actual vs pantalla heatmap
  
Commit 13 (0.5h): Cooldowns con retry (ID 12)
  - Agregar fallback rápido si cooldown expira
```

**QA después Fase 2**:
- ✅ Movimiento fluido en todos escenarios
- ✅ Multi-monitor funcional
- ✅ IO reducido (verificar disk writes)
- ✅ Comportamiento consistente (log analysis)

---

### FASE 3: Deuda Técnica (20h, extendida)

```
Refactor 1 (6h): FP-022 multi-monitor completa (ID 14)
Refactor 2 (5h): Thread safety exhaustiva (ID 15)
Refactor 3 (3h): Ferrofluido visible (ID 16)
Refactor 4 (3h): Particulas adaptive (ID 17)
Refactor 5 (3h): Consolidar _pos_anterior (ID 18)
```

---

## VALIDACIÓN 4D (GATE 1)

Después de cada FASE:

### Dimensión 1: VERDAD LÓGICA
- ¿Código es internamente consistente?
- ¿Pre-condiciones ⊂ estado actual?
- Verificar con AST parsing o manual review

### Dimensión 2: VERDAD EMPÍRICA
- ¿Tests pasan (unitarios + integración)?
- ¿Output visual es esperado?
- Verificar con pytest + visual inspection

### Dimensión 3: VERDAD AXIOMÁTICA
- ¿Respeta Garantía Tripartita?
- ¿No viola R1-R24?
- Verificar contra SDD.md

### Dimensión 4: VERDAD REVELADA
- ¿Se decodifica en 3 capas?
- ¿Hay síntesis del mensaje?
- Documentar en PALINGENESIA

---

## DECISIONES ARQUITECTÓNICAS

### Decisión 1: Mantener MotorProactividad en QThread
**Justificación**: Integración Qt limpia, permite signals, debugging fácil  
**Alternativa rechazada**: threading.Timer (menos integración)

### Decisión 2: QMutex para sincronización
**Justificación**: Estándar Qt, robusto, bajo overhead  
**Alternativa rechazada**: Atomic (no aplicable Python)

### Decisión 3: Caching de geografía (pantallas)
**Justificación**: 99% de casos no cambian monitor frecuentemente  
**Alternativa rechazada**: Recalcular siempre (overhead innecesario)

---

## MÉTRICAS DE ÉXITO

| Métrica | Baseline | Target |
|---------|----------|--------|
| FPS consistente | 30-40fps variable | 58-60fps estable |
| Jitter movimiento | 5-15px visible | <1px imperceptible |
| Latencia decisión | 500ms visible | <250ms imperceptible |
| Memory footprint | 150MB + leak | 120MB estable |
| CPU promedio | 8-12% | 6-8% |
| I/O writes/min | 2 (JSON heatmap) | 0.2 (comprimido, debounce) |

---

## TIMELINE PROPUESTO

- **Semana 1 (6/3-6/7)**: FASE 1 (MVP crítico) — 9 commits, 9h
- **Semana 2 (6/10-6/14)**: FASE 2 (Solidificación) — 8 commits, 8-10h
- **Semana 3+ (6/17+)**: FASE 3 (Deuda) — 5 refactors, 20h

---

## CONCLUSIONES CITRINITAS

✅ **Estrategia clara: MVP → Solidificación → Deuda**  
✅ **Trade-offs decididos, documentados**  
✅ **Métricas de éxito definidas**  
✅ **Validación 4D integrada en cada fase**

**Siguiente**: RUBEDO (implementación de FASE 1)

---

**FIN CITRINITAS**
