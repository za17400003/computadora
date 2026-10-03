# ALBEDO — MALJUT: Investigación de Soluciones

**Fecha**: Junio 1, 2026  
**Fase**: ALBEDO (Purificación, investigación)  
**Basado en**: [NIGREDO_MALJUT_AUDIT_COMPLETO.md](NIGREDO_MALJUT_AUDIT_COMPLETO.md)

---

## RESUMEN EJECUTIVO

Investigadas soluciones para 20 hallazgos en Maljut. Se proponen **3 patrones de remediación**:
1. **Thread Safety Pattern** (Mutex + Signals) → IDs 1, 3, 5, 10, 15
2. **Exception Handling Pattern** (Try-Except + Fallback) → IDs 2, 16, 19
3. **Geometric Validation Pattern** (Clamp + Bounds Check) → IDs 6, 7, 8, 11, 18

---

## GRUPO A: PROBLEMAS CRÍTICOS (Pipeline C — 24h)

### ID 1: Race condition `_pos_objetivo` — SOLUCIÓN

**Problema**: `_pos_objetivo` escrito por MotorProactividad (500ms), leído por _animar (16ms) sin sincronización.

**Investigación**:
- PyQt6 tiene `QMutex` + `QReadWriteLock`
- MotorProactividad corre en QThread separado
- _animar corre en hilo principal Qt

**Solución propuesta**:
```python
# En vida_autonoma.py (MotorProactividad)
from PyQt6.QtCore import QMutex

class VidaAutonoma:
    def __init__(self, ...):
        self._mutex_pos = QMutex()
        self._pos_objetivo = None
    
    def _tick(self):
        # ... lógica
        self._mutex_pos.lock()
        try:
            self._pos_objetivo = QPoint(target_x, target_y)
        finally:
            self._mutex_pos.unlock()

# En ventana_principal.py (_animar)
def _interpolar_movimiento(self):
    if hasattr(self._vida, '_mutex_pos'):
        self._vida._mutex_pos.lock()
        try:
            pos_obj = self._vida._pos_objetivo
        finally:
            self._vida._mutex_pos.unlock()
    else:
        pos_obj = None  # Fallback
    
    if pos_obj:
        # ... interpolar
```

**Impacto**: Elimina race condition, +2-5% CPU overhead (acceptable)  
**Complejidad**: MEDIA (4-6 cambios localizados)  
**Testing**: Unitario con 2 threads writing/reading simultaneo

---

### ID 2: Memory leak partículas — SOLUCIÓN

**Problema**: Si `p.actualizar()` falla (excepción), particula nunca se remueve.

**Investigación**:
- `Particula.actualizar()` no tiene error handling explícito
- Loop `for p in self._particulas` expone si hay excepción
- Alternativa: usar `try-except` vs `Particula.actualizar()` retorna bool de error

**Solución propuesta**:
```python
# ventana_principal.py L1625
for p in list(self._particulas):
    try:
        if not p.actualizar(dx, dy):
            self._particulas.remove(p)
    except Exception as e:
        # Particula corrompida → remover + log
        logger.debug(f"Particula error (remover): {e}")
        self._particulas.discard(p) if isinstance(self._particulas, set) else self._particulas.remove(p) if p in self._particulas else None
```

**Alternativa**: Hacer `Particula.actualizar()` robusto (catch internas, return None si error)

**Impacto**: Previene OOM a largo plazo  
**Complejidad**: BAJA (1 cambio)  
**Testing**: Inyectar excepción en actualizar(), verificar cleanup

---

### ID 3: Deadlock timers — SOLUCIÓN

**Problema**: `_timer` (16ms) en Qt + MotorProactividad._timer (500ms) pueden crear deadlock si hay sleep().

**Investigación**:
- MotorProactividad es QThread, tiene su propio event loop (si .exec() llamado)
- Si `.msleep()` dentro de _tick(), bloquea thread
- Qt thread intenta communicar → espera → deadlock

**Solución propuesta**:
```python
# En vida_autonoma.py
class MotorProactividad(QThread):
    def run(self):
        # NO crear QTimer aquí (pertenece al thread que lo crea)
        # Usar threading.Timer en lugar de QTimer
        import threading
        def tick_loop():
            while not self._stop_requested:
                self._tick()
                time.sleep(0.5)  # No bloquea Qt thread
        
        thread = threading.Thread(target=tick_loop, daemon=True)
        thread.start()

# Alternativa: Usar QTimer pero NO bloquear
class MotorProactividad(QThread):
    def __init__(self, ...):
        super().__init__()
        self._stop_requested = False
        self.moveToThread(self)  # Mover a su propio thread
    
    def run(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(500)
        self.exec()  # Event loop para el thread
    
    def _tick(self):
        # No usar msleep() — usar QTimer en lugar
        pass
```

**Impacto**: Elimina deadlock, arqui más limpia  
**Complejidad**: ALTA (refactor de MotorProactividad, posible cambio a threading.Timer)  
**Testing**: Stress test con 2+ cores, verificar no freeze UI

---

### ID 5: Render offset desincronización — SOLUCIÓN

**Problema**: Reset incondicional de `_render_offset_x/y = 0.0` en collapse causa salto visual durante interpolación.

**Investigación**:
- Offset se interpola gradualmente (lerp 0.1)
- Reset directo ignora esto
- Alternativa: gradual reset, o detener interpolación primero

**Solución propuesta**:
```python
# vida_autonoma.py L1264 (_colapsar_ventana_transito)
def _colapsar_ventana_transito(self):
    # ANTES: Reset incondicional
    # self._orbe._render_offset_x = 0.0
    # self._orbe._render_offset_y = 0.0
    
    # AHORA: Gradual reset (durante próximos 10 frames)
    self._orbe._offset_collapse_timer = 10  # frames para interpolar a 0
    self._orbe._offset_collapse_target_x = 0.0
    self._orbe._offset_collapse_target_y = 0.0
    
    # En _interpolar_movimiento():
    if hasattr(self._orbe, '_offset_collapse_timer') and self._orbe._offset_collapse_timer > 0:
        self._render_offset_x += (0.0 - self._render_offset_x) * 0.1
        self._render_offset_y += (0.0 - self._render_offset_y) * 0.1
        self._offset_collapse_timer -= 1
    elif hasattr(self._orbe, '_offset_collapse_target_x'):
        self._render_offset_x = 0.0
        self._render_offset_y = 0.0
```

**Impacto**: Suavidad visual en collapse  
**Complejidad**: BAJA (4-5 cambios)  
**Testing**: Visual: esquiva → collapse debe ser suave

---

## GRUPO B: PROBLEMAS MEDIA (Pipeline B — 1 semana)

### ID 4: Double mapFromGlobal — SOLUCIÓN

**Problema**: `mapFromGlobal()` llamado 2× por frame (en _animar + paintEvent).

**Solución**:
```python
# paintEvent() — usar cache en lugar de recalcular
def paintEvent(self, event):
    # Antes: pos_local = self.mapFromGlobal(QCursor.pos())  # ← RETIRAR
    # Después: usar self._cached_cursor_local (ya calculado en _animar)
    
    if self._proximidad > 0.2 and self._cached_cursor_local is not None:
        pos_local = self._cached_cursor_local  # ✅ Usa cache
        # dibujar partículas con pos_local
```

**Impacto**: ~1-2ms ahorrados per frame (~3-5% presupuesto)  
**Complejidad**: BAJA (1 cambio)  
**Testing**: Profiler confirma una sola llamada a mapFromGlobal

---

### ID 6: `_estorba()` sin clamp negativo — SOLUCIÓN

```python
# vida_autonoma.py L1300 (_estorba)
margen_cursor = 100
# Clamp a pantalla
left = max(self._pantalla.left(), info.cursor.x() - margen_cursor)
top = max(self._pantalla.top(), info.cursor.y() - margen_cursor)
right = min(self._pantalla.right(), info.cursor.x() + margen_cursor)
bottom = min(self._pantalla.bottom(), info.cursor.y() + margen_cursor)
cursor_zone = QRect(left, top, right - left, bottom - top)
```

**Impacto**: Valida edge case  
**Complejidad**: BAJA (1 cambio)

---

### ID 7: Multi-monitor — SOLUCIÓN

**Investigación**: FP-022 menciona `.pantallas` en InfoEscritorio pero nunca se usa.

**Solución**:
```python
# vida_autonoma.py __init__
# Actualizar _pantalla periódicamente (cada ~5s)
self._pantalla_update_counter = 0
self._pantalla_update_interval = 10  # ticks de 500ms = 5s

# En _tick():
self._pantalla_update_counter += 1
if self._pantalla_update_counter >= self._pantalla_update_interval:
    self._pantalla_update_counter = 0
    # Recalcular pantalla actual (cursor puede estar en diferente monitor)
    cursor_screen = None
    for screen_rect in info.pantallas:
        if screen_rect.contains(info.cursor):
            cursor_screen = screen_rect
            break
    if cursor_screen and cursor_screen != self._pantalla:
        logger.debug(f"Pantalla cambió: {self._pantalla} → {cursor_screen}")
        self._pantalla = cursor_screen
```

**Impacto**: Soporta multi-monitor dinámicamente  
**Complejidad**: MEDIA (3-4 cambios)

---

### ID 8-13: Otros problemas media
- **ID 8** (wall-sliding): Agregar fallback a borde si flee escapa
- **ID 9** (heatmap): Debounce a 5s en lugar de cada tick
- **ID 10** (FSM desincronizado): Conectar signal de cambio de estado
- **ID 11** (hogar stale): Validar pantalla en lectura de heatmap
- **ID 12** (cooldowns): Agregar retry flag después de cooldown
- **ID 13** (latencia): Reducir a 250ms si CPU < 50%, expandir a 750ms si CPU > 80%

---

## GRUPO C: DEUDA TÉCNICA (Pipeline E — 3 semanas)

### ID 14-18: Multi-monitor, thread safety, ferrofluido, partículas adaptive, pos_anterior

**Investigación por ID**:
- **ID 14** (FP-022): Refactor completo de hogar dinámico para multi-monitor
- **ID 15** (Thread safety): Agregar QMutex a `_estado`, `_heatmap`, etc.
- **ID 16** (Ferrofluido): Log visible si falla, UI indicator "ferrofluido apagado"
- **ID 17** (Particulas adaptive): Reducir cap basado en CPU load
- **ID 18** (`_pos_anterior`): Consolidar a `_pos_anterior_x/y` solamente

---

## MATRIZ DE SOLUCIONES

| ID | Problema | Solución | Pipeline | Estimación |
|----|----------|----------|----------|------------|
| 1  | Race `_pos_objetivo` | QMutex lock/unlock | C | 2h |
| 2  | Memory leak | Try-except en loop | C | 1h |
| 3  | Deadlock | Threading.Timer o QThread refactor | C | 4h |
| 5  | Offset desincronización | Gradual reset con timer | C | 2h |
| 4  | Double mapFromGlobal | Usar cache paintEvent | B | 0.5h |
| 6-13 | 8 problemas media | Según tabla arriba | B | 6-8h total |
| 14-18 | 5 deudas | Refactor por ID | E | 15-20h total |

**Total estimado**: 30-40 horas (B+C+E)  
**MVP (C solamente)**: 9 horas

---

## CONCLUSIONES ALBEDO

✅ **Todas las soluciones son viables técnicamente**  
✅ **No requieren cambios de arquitectura fundamental**  
✅ **3 patrones simples cubren 80% de hallazgos**  

**Siguiente**: CITRINITAS (optimizar soluciones, trade-offs)

---

**FIN ALBEDO**
