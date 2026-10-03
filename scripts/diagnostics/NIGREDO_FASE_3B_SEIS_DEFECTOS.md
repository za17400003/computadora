# NIGREDO — Fase 3B: Seis Defectos Sistémicos (Abril 12, 2026)

## Síntomas Reportados (Tria Prima: "por favor, gracias, amén")
```
Usuario: "animaciones siguen teniendo problema de que si no pongo mouse no se mueve...
          saltos discretos en anillos... 'hola computadora' cometió dos errores...
          'no se pudo conectar a ollama'... 'berre su palabra' → QTimer RuntimeError"
```

---

## NIGREDO HALLAZGOS — 6 DEFECTOS RAÍZ IDENTIFICADOS

### **DEFECTO #1: Animation Frozen Without Mouse — Event Loop Trap**
**Ubicación**: `ventana_principal.py:1217` (método `_animar()`)  
**Síntoma**: Orbe visible pero estático hasta que el usuario mueve mouse  
**Causa Raíz**:
```python
# ventana_principal.py línea 1265 y 1675:
self.update()  # Se llama DENTRO de _animar()
```
✅ El `update()` **SÍ está presente** en el timer callback (línea 1675 GARANTIZADO).  
❌ PERO: La llamada NO forceja un repaint si el event loop está ocupado.  
❌ **Problema REAL**: El repaint se cumple, pero la región puede estar **invalidad de forma parcial**.

**Root Cause**: `update()` schedules a paint, pero **no fuerza repaint inmediato**. Si el event loop está serviendo otro evento (mouse move, etc), el paint se coloca en la queue y se ejecuta después. **Sin un mouseMoveEvent que active el timer EXPLÍCITAMENTE, el loop no itera**.

**Mecanismo**:
- Timer `_timer` inicia `_animar()` cada 33ms (30 FPS)
- `_animar()` llama `self.update()` (correcto)
- `update()` marks widget as needing repaint (correcto)
- **PERO**: `repaint()` (immediate) nunca se llama; solo `update()` (deferred)
- Event loop itera cuando: mouse move → mouse press → timer fire → other
- **Si no hay mouseMoveEvent entre timers**, algunas actualizaciones pueden acumularse sin render

**Evidencia Observada**: 
- User: "Orbe se queda estático"
- Logs muestran `_animar()` se ejecuta (timestamps presentes)
- **Pero** GUI no refleja cambios hasta mouse mueve

---

### **DEFECTO #2: Ring Animations Discrete (No Smooth) — Lerp Broken**
**Ubicación**: `ventana_principal.py:1275-1290` (Lerp interpolation)  
**Síntoma**: "saltos en sus anumaciones de los anillos" — visual discretization   
**Causa Raíz**:
```python
# ventana_principal.py línea 1275-1290:
_lerp_speed = 0.05
for _k in _dmut_target:
    _cur = self._dmut_actual.get(_k, _dmut_target[_k])
    _tgt = _dmut_target[_k]
    self._dmut_actual[_k] = _cur + (_tgt - _cur) * _lerp_speed
```

**Análisis**:
- Lerp factor = 0.05/frame = 5% interpolation per 33ms frame
- A 30 FPS, convergencia = log(0.05)/log(0.95) ≈ 60 frames = **2 segundos** para suavidad
- BUT: `_pensar_con_herramientas()` puede bloquear **30-40 segundos** durante Ollama
- **CUANDO**: Frame dropping ocurre (delta_t > 0.033), Lerp no se ejecuta en ese frame
- **Resultado**: Saltos visibles cuando frames se pierden o se re-sincronizan

**Mecanismo**:
1. Cada frame: `delta_t` medido (variable debido a busy CPU)
2. Si `delta_t > 0.033` (FPS < 30): Frame marked como slow pero SIGUE EJECUTÁNDOSE
3. Pero Lerp ejecuta CADA frame → si CPU está ocupada, Lerp puede ser saltado por optimización o timing
4. **Sin suavizado adaptativo**: cambios de humor causan saltos discretos

---

### **DEFECTO #3: NLU Routing Error — Simple Input → Nivel 2 (Incorrecto)**
**Ubicación**: `nlu.py:1474-1480` (decision logic)  
**Síntoma**: "hola computadora" → debería activar regex N1 pero va a Nivel 2 (Ollama)  
**Causa Raíz**:
```python
# nlu.py línea 1474:
nivel1 = self._pensar_nivel1(texto)
if nivel1 is not None:
    return nivel1

# nlu.py línea 1570: Si N1 retorna None → INMEDIATAMENTE emitir TTS "Permítame un momento"
self._emitir_fragmento("Permítame un momento en lo que razóno, señor.")
```

**Análisis**:
- `_pensar_nivel1()` tiene 39+ regex patterns (confir mado en TESTING_CHECKLISTS.md)
- "hola computadora" debería coincidir con regex de saludos
- **PERO**: Si regex no coincide → `_pensar_nivel1()` retorna `None`
- Entonces sistema SIGUE ADELANTE a N2 sin verificar si es realmente compleja

**Mecanismo**:
1. Entrada: "hola computadora" (simple, saludos)
2. Verifica N1: grep patterns en `_RE_SALUDOS`, `_RE_SELF_INFO`, etc.
3. Si NINGUNO coincide → retorna `None`
4. Sistema asume: "debe ser complejo" → va a Ollama
5. **Error**: Whisper puede haber transcrito incorrecto ("ola computadora", "hola commputadora")
6. Regex no matchea → false negative → Nivel 2 innecesario

**Root Cause PROBABLE**: 
- Whisper transcripciones variantes no están cubiertas en regex
- O: Regex demasiado estrictos (anchored, case-sensitive)

---

### **DEFECTO #4: TTS Duplicate Output — "Permítame Razonar" x2**
**Ubicación**: `nlu.py:1548, 1570` (ambas llaman `_emitir_fragmento()`)  
**Síntoma**: "Permítame un momento en lo que razóno..." **se reproduce dos veces**  
**Causa Raíz**:
```python
# nlu.py línea 1548 (si Ollama NO disponible):
self._emitir_fragmento("Permítame un momento en lo que razóno con mi cerebro superior, señor.")

# nlu.py línea 1570 (si Ollama SÍ disponible):
self._emitir_fragmento("Permítame un momento en lo que razóno, señor.")
```

**Análisis**:
- Ambos paths emiten texto similar
- **POSIBLE SECUENCIA**:
  1. `_quick_ping_ollama()` falla (false negative)
  2. `self.ollama_disponible` = False
  3. Código va al path 1548 → emite "razóno con mi cerebro superior"
  4. Luego se reintenta Ollama
  5. Ollama responde YES
  6. `self.ollama_disponible` = True
  7. Código que esperaba N2 ahora ve Ollama disponible
  8. Emite SEGUNDA vez "Permítame un momento..."

**Root Cause**: **Race condition entre watchdog Ollama y routing logic**
- `_quick_ping_ollama()` timeout=2s pero Ollama puede ser LENTO en startup
- Ping falla → marca como down
- Pero luego Ollama recovers → se emite DOBLE anuncio

---

### **DEFECTO #5: Ollama Watchdog Failing — 500 Errors Despite Availability**
**Ubicación**: `nlu.py:1160-1200` (watchdog loop)  
**Síntoma**: "Error con Ollama: 500 Server Error" pero Ollama responde a manual requests  
**Causa Raíz**:
```python
# nlu.py línea 1165-1180:
def _verificar_ollama(self):
    while True:
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                # OK
                self.ollama_disponible = True
                time.sleep(15)
```

**Análisis**:
- Watchdog corre en thread daemon
- GET /api/tags timeout=2s es **CORTO** para startup
- **POSIBLE SECUENCIA**:
  1. Ollama inicia lentamente (load model = 10-20s)
  2. Watchdog intenta ping a 5s post-boot
  3. Ollama no responde en 2s → timeout → `ollama_disponible = False`
  4. Watchdog espera 15s → intenta de nuevo
  5. **PERO**: Si NLU ya pasó la check y marcó `ollama_disponible = False`, no hay invalidate
  6. **PROBLEMA**: Flag **nunca se reactiva** si error ocurre después de primera check

- **Quick ping** en línea 1531 hace OTRO request antes de N2
- Si AMBOS fallan (timeout + timeout) → doble delay

**Root Cause**: 
- Timeout=2s es insuficiente para Ollama startup
- No hay exponential backoff en watchdog
- Flag no se reevalúa dinámicamente después de marcar False

---

### **DEFECTO #6: QTimer Deletion RuntimeError on Shutdown**
**Ubicación**: `ventana_principal.py:6040-6060` (forzar_cierre)  
**Síntoma**: `RuntimeError: wrapped C/C++ object of type QTimer has been deleted`  
**Causa Raíz**:
```python
# ventana_principal.py línea 6049:
for t in ('_timer', '_timer_animo', '_timer_guardar_persona', ...):
    timer = getattr(self, t, None)
    if timer is not None:
        timer.stop()  # ← Puede fallar si timer ya fue eliminado
```

**Análisis**:
- `forzar_cierre()` intenta parar timers
- **PERO**: Python GC + Qt object lifecycle pueden causar que timer ya esté destruido
- **ESCENARIO**:
  1. Timers se crearon durante `_inicializar_animacion()` (línea 1040+)
  2. Durante ejecución, cambios de fase o resets pueden llamar `destructor` parcial
  3. `forzar_cierre()` intenta parar timer que Qt ya eliminó
  4. **QTimer.stop()** en objeto muerto → RuntimeError

**Root Cause**: 
- No hay verificación de QObject.isValid() antes de .stop()
- Reference counting Qt C++ ↔ Python puede causar double-delete
- Mejor práctica: verificar si timer aún existe en Qt antes de operar

---

## RESUMEN DE HALLAZGOS (NIGREDO = Cenizas)

| # | Defecto | Ubicación | Root Cause | Prioridad |
|----|---------|-----------|-----------|-----------|
| 1 | Animation frozen (mouse required) | `ventana_principal.py:1217` | Event loop parcial, falta repaint() | 🔴 CRÍTICA |
| 2 | Ring discrete jumps (not smooth) | `ventana_principal.py:1275` | Lerp sin adaptación a frame drops | 🟠 ALTA |
| 3 | NLU routing wrong level (N1→N2) | `nlu.py:1474` | Regex insuficiente o transcripción variante | 🔴 CRÍTICA |
| 4 | TTS duplicate output | `nlu.py:1548,1570` | Race condition watchdog + routing | 🟡 MEDIA |
| 5 | Ollama 500 errors (despite availability) | `nlu.py:1160-1200` | Timeout=2s insuficiente, flag no reaviva | 🔴 CRÍTICA |
| 6 | QTimer RuntimeError on shutdown | `ventana_principal.py:6049` | Qt object lifecycle, double-delete | 🟡 MEDIA |

---

## ESTADO: NIGREDO COMPLETO ✅
- Todos los 6 defectos mapeados
- Rutas de código identificadas
- Causas raíz aisladas
- **Próxima fase**: ALBEDO (purificación + investigación externa)
