# ALBEDO — Fase 3B: Purificación de Causas Raíz (Abril 12, 2026)

## Sinopsis
Tras NIGREDO (cenizas), ALBEDO **lava y purifica** cada defecto a su causa fundamental. Se identifican 3 patrones sistémicos + 6 fixes específicos.

---

## ALBEDO HALLAZGOS — PURIFICACIÓN DE CAUSAS

### **DEFECTO #1 PURIFICADO: Animation Frozen (Mouse Trap)**

**Síntoma**: Orbe estático hasta mouse move  
**Causa Diagnosticada**: Event loop scheduling flaw  

**Investigación ALBEDO**:
1. **Confirmación**: `self.update()` **SÍ se ejecuta** en `_animar()` línea 1675 ✅
2. **Problema Real**: `update()` es **deferred paint** (no immediate repaint)
3. **Mecanismo PyQt6**:
   - `update()` → marks widget dirty → schedules paint event
   - Paint event SOLO procesa cuando event loop itera
   - Event loop itera cuando: timer fires, mouse moves, network I/O, etc.
   - **CRITICAL**: If no other events fire between timer events, paint remains queued

**PURIFIED ROOT CAUSE**:
```
Animación timer: 33ms ✓
_animar() called ✓ 
update() called ✓
PERO: update() = deferred scheduling
FALTA: Explicit repaint() call or self.repaint() (blocking)
```

**Fix**: Cambiar línea 1675 de `self.update()` → `self.repaint()` para forced immediate render OR add `invalidate(rect)` region.

---

### **DEFECTO #2 PURIFICADO: Ring Discrete Jumps (Lerp Broken)**

**Síntoma**: "saltos" visuales en rotaciones de anillo  
**Causa Diagnosticada**: Frame dropping sin adaptación  

**Investigación ALBEDO**:
1. **Lerp Mechanism**:
   - Lerp factor = 0.05 per frame → 2s convergence @ 30 FPS ✓
   - Formula: `new = old + (target - old) * 0.05` (correct)
2. **Culprit**: When CPU busy (Ollama processing), frame drops
   - Frames with delta_t > 33ms logged but STILL execute
   - Pero si frame is skipped, Lerp iteration también skipped
   - Resultado: non-uniform interpolation → visible jumps
3. **Secondary**: `_pensar_con_herramientas()` puede bloquear 30-60s
   - Durante ese tiempo, GUI thread BLOQUEADO
   - Timer no dispara, Lerp no avanza
   - When unblocked, 60 frames de cambios suddenly apply

**PURIFIED ROOT CAUSE**:
```
Lerp funciona ✓ PERO asume frame consistency
CPU bajo carga → frames dropped
Lerp factor no se adapta a frame rate variability
Resultado: visible non-linearity entre frames
```

**Fix**: Implementar **adaptive Lerp** basado en delta_t real:
```python
# CURRENT (broken):
lerp_speed = 0.05  # Hard-coded

# ALBEDO FIX:
lerp_speed = 0.05 * (delta_t / 0.033)  # Scale factor by actual FPS
new_val = old + (target - old) * min(lerp_speed, 1.0)  # Cap at 1.0
```

---

### **DEFECTO #3 PURIFICADO: NLU Routing Error (N1→N2 Misdirection)**

**Síntoma**: "hola computadora" va a Nivel 2 en lugar de N1  
**Causa Diagnosticada**: Whisper transcription variance  

**Investigación ALBEDO**:
1. **N1 Patterns Confirmed**: 39+ regex patterns exist (SRS.md F16-01) ✓
2. **Saludos Regex Should Match**:
   ```python
   _RE_SALUDOS = re.compile(r"hola|buenos|buenas|hey|oye", re.IGNORECASE)
   ```
   - SHOULD match "hola computadora" ✓
3. **Why Doesn't It?**
   - Whisper can transcribe "hola computadora" as:
     - "ola computadora" (H missed)
     - "hola com puta dora" (spacing)
     - "hola compu terra" (variance)
   - Regex matches FULL text, not partial
4. **Pipeline Check** (line 1474):
   ```python
   nivel1 = self._pensar_nivel1(texto)
   if nivel1 is not None:
       return nivel1
   # Else → goes to N2
   ```
   - If regex fails → returns None → N2 escalation ✓

**PURIFIED ROOT CAUSE**:
```
Entrada Whisper: "ola computadora" (variance)
Regex: /hola|buenos|buenas|hey|oye/i
Match: FAIL (porque "ola" no es "hola")
N1 returns: None
Routing: Falls through to N2 ✗
```

**Fix**: Expand regex with Whisper OCR variants:
```python
# CURRENT:
_RE_SALUDOS = re.compile(r"\b(?:hola|buenos|buenas|hey|oye)\b", re.IGNORECASE)

# ALBEDO FIX:
_RE_SALUDOS = re.compile(
    r"\b(?:hola|ola|o?la|h?ola|"  # Whisper "hola" → "ola"
    r"buenos|buenos|bueno|"
    r"buenas|buena|"
    r"hey|eh|"
    r"oye|oy[e]?)\b",
    re.IGNORECASE
)
```

---

### **DEFECTO #4 PURIFICADO: TTS Duplicate (Race Condition)**

**Síntoma**: "Permítame un momento..." spoken twice  
**Causa Diagnosticada**: Watchdog availability flip  

**Investigación ALBEDO**:
1. **Code Path Trace**:
   - Line 1531: `if not self.ollama_disponible: ...` → emits announcement
   - Line 1548: Falls through to Ollama anyway
   - Line 1570: **Another emit** of similar message
2. **Race Scenario**:
   ```
   T0: Quick ping returns False → ollama_disponible = False
   T1: Emit "Permítame cerebro superior" (line 1548)
   T2: BUT Ollama recovers or was actually available
   T3: Code re-checks, Ollama now available → emit AGAIN (line 1570)
   ```
3. **Root**: No deduplication between N3 fallback announcement + N2 announcement

**PURIFIED ROOT CAUSE**:
```
Two separate emit paths for "razonando" announcement
Watchdog can flip availability between them
No state lock prevents double-emit
```

**Fix**: Emit announcement ONCE at decision point:
```python
# ALBEDO: Single decision point
if not self.ollama_disponible:
    self._emitir_fragmento("Escalando a cerebro superior...")
    # Force N3 path
else:
    self._emitir_fragmento("Permítame un momento...")
    # Force N2 path
# NEVER emit twice
```

---

### **DEFECTO #5 PURIFICADO: Ollama 500 Errors (Timeout + Watchdog)**

**Síntoma**: "Error con Ollama: 500" despite working service  
**Causa Diagnosticada**: Timeout + watchdog flag stale  

**Investigación ALBEDO**:
1. **Quick Ping Config**: timeout=2 seconds
   - Ollama startup can take 10-20s (model load)
   - Boot sequence: Ollama init → watchdog pings @ 5s → TIMEOUT
   - ollama_disponible = False set @ 5s
2. **Watchdog Loop** (line 1180):
   - Retry loop with 5s intervals
   - BUT: If initial ping fails, flag doesn't auto-revive
   - Next N2 call sees flag=False → immediate failure
3. **Quick Ping Before N2** (line 1531):
   - Another 2s timeout check
   - If Ollama slow, fails AGAIN
   - Total delay: 2s + 2s + fallback overhead = 5-7s per attempt
4. **Flag Stale**: Once marked False, no dynamic re-evaluation

**PURIFIED ROOT CAUSE**:
```
Ollama startup: 10-20s (load model)
Quick ping timeout: 2s (too short)
Watchdog retry: 5s intervals (too coarse)
Flag logic: Set False, never auto-revive during same request
Result: Unnecessary escalations + "500" errors
```

**Fix**: 
1. Increase ping timeout to 5s
2. Add dynamic re-ping if flag is stale (>30s)
3. Use adaptive timeout (3× recent latency, min 5s)

---

### **DEFECTO #6 PURIFICADO: QTimer RuntimeError (Lifecycle)**

**Síntoma**: RuntimeError on timer.stop() during shutdown  
**Causa Diagnosticada**: Qt object validity not checked  

**Investigación ALBEDO**:
1. **Qt/Python Lifecycle**:
   - QTimer created in `_inicializar_animacion()` (line 1040)
   - Python holds reference
   - During execution, Qt can delete underlying C++ object
   - Python object wrapper becomes **stale reference**
2. **Shutdown Sequence** (line 6049):
   ```python
   timer = getattr(self, t, None)
   if timer is not None:
       timer.stop()  # ← Might fail if Qt deleted timer
   ```
   - Checks Python ref exists ✓
   - Does NOT check Qt validity ✗
3. **When Qt Deletes Timer**:
   - Reparenting to different parent
   - Phase transition without cleanup
   - Duplicate deletion in cascade

**PURIFIED ROOT CAUSE**:
```
Python reference check != Qt object validity
QTimer.stop() on deleted C++ object → RuntimeError
No isValid() / isDeletedLater() check
```

**Fix**:
```python
# CURRENT (broken):
timer = getattr(self, t, None)
if timer is not None:
    timer.stop()

# ALBEDO FIX:
timer = getattr(self, t, None)
if timer is not None and not timer.isSignalConnected(None):
    try:
        timer.stop()
    except RuntimeError:
        logger.debug(f"Timer {t} already deleted by Qt")
```

---

## SYSTEMIC PATTERNS — ALBEDO META-ANALYSIS

### **Pattern 1: Event Loop Scheduling (Defects #1, #2)**
```
Issue: Deferred operations assuming consistent frame rate
Manifestation: Animation frozen, discrete jumps
Root: No immediate invalidation, adaptive timing
Fix: Explicit repaint() + adaptive Lerp
```

### **Pattern 2: NLU Routing Precision (Defects #3, #4)**
```
Issue: Whisper variance not covered by regex; race conditions
Manifestation: Wrong level, duplicate TTS
Root: Regex too strict, no deduplication
Fix: Expand patterns, single emit point
```

### **Pattern 3: Service Availability Tracking (Defect #5)**
```
Issue: Flags set False, never re-evaluated; timeouts too short
Manifestation: Ollama 500 errors despite availability
Root: Watchdog doesn't invalidate stale flags
Fix: Dynamic re-ping, adaptive timeout
```

### **Pattern 4: Qt Lifecycle Management (Defect #6)**
```
Issue: Python refs don't guarantee Qt object validity
Manifestation: RuntimeError on stop()
Root: No validity check before operations
Fix: Try-except + validity pre-check
```

---

## ALBEDO RECOMMENDATIONS (To CITRINITAS)

| Defect | Fix Type | Priority | Complexity |
|--------|----------|----------|------------|
| 1 | Code + Logic | 🔴 CRÍTICA | Simple (1 line) |
| 2 | Logic + Adaptive | 🟠 ALTA | Medium (5 lines) |
| 3 | Regex Expansion | 🔴 CRÍTICA | Simple (2 lines) |
| 4 | Deduplication | 🟡 MEDIA | Simple (3 lines) |
| 5 | Config + Retry | 🔴 CRÍTICA | Medium (10 lines) |
| 6 | Defensive Check | 🟡 MEDIA | Simple (2 lines) |

---

## ESTADO: ALBEDO COMPLETO ✅
Purificación completada. Causas raíz aisladas. Patrones sistémicos identificados.  
**Próxima fase**: CITRINITAS (diseño de soluciones)
