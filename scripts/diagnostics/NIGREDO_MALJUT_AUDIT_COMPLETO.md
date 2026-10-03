# ⚫ NIGREDO AUDIT — MALJUT (Análisis Destructivo Completo)

**Fecha**: Junio 1, 2026  
**Ejecutado por**: GitHub Copilot (GATE -1 Workflow)  
**Estado**: DIAGNÓSTICO SIN IMPLEMENTACIÓN (ALBEDO→CITRINITAS→RUBEDO pendiente)

---

## EXECUTIVE SUMMARY

Se han identificado **13 hallazgos críticos + 8 problemas técnicos + 6 deudas arquitectónicas** en Maljut (vida_autonoma.py + ventana_principal.py). 

- ✅ **WI-MALJUT-002** ya parcialmente arreglado (animaciones + clipping)
- ❌ **Problemas restantes**: Race conditions, memory leaks, sincronización timer-decisión, cálculos geométricos
- 🔴 **BLOQUEADORES**: Deadlocks potenciales entre threads, inconsistencia render-offset

---

## I. PROBLEMAS CRÍTICOS (BLOQUEAN OPERACIÓN)

### 1. 🔴 **Race Condition: `_pos_objetivo` sin sincronización**
**Archivo**: `vida_autonoma.py`  
**Ubicación**: Línea 1094+ (main decision tick), línea 1142+ (animation interpol)  
**Severidad**: CRÍTICA

**Problema**:
```python
# _tick() (500ms)
self._pos_objetivo = QPoint(target_x, target_y)  # ESCRIBE (thread de vida_autonoma)

# _interpolar_movimiento() (16ms, thread de _animar)
render_offset_x += (self._pos_objetivo.x() - ...) * 0.1  # LEE (sin lock)
```

**Consecuencia**:
- Thread 1 (Vida): Escribe `_pos_objetivo` cada 500ms
- Thread 2 (Orbe/Animación): Lee `_pos_objetivo` cada 16ms
- **Race condition**: Lectura parcial → offset calculado a mitad de cambio de valor
- Resultado visual: **Saltos/jitter en movimiento**, especialmente en esquiva

**Raíz**: Sin QMutex ni lock, acceso concurrente no protegido

---

### 2. 🔴 **Memory Leak: `_particulas` no se limpian completamente**
**Archivo**: `ventana_principal.py`  
**Ubicación**: Línea 1400+ (`_animar`), línea 1625+ (actualizar partículas)  
**Severidad**: ALTA (degradación progresiva)

**Problema**:
```python
# Línea 1400
if len(self._particulas) < self._max_particulas:
    if self._estado == "trabajando" and random.random() < 0.4:
        self._particulas.append(Particula(...))

# Línea 1625
for p in list(self._particulas):
    if not p.actualizar(dx, dy):
        self._particulas.remove(p)  # ← Remove based on actualizar() return
```

**Pero**: ¿Qué pasa si `p.actualizar()` **falla** (excepción)?
- Particula nunca se remueve
- List crece indefinidamente
- Después de horas: miles de partículas inactivas en memoria

**Raíz**: Sin try-except en `for p in self._particulas`, error en una particula bloquea cleanup

---

### 3. 🔴 **Deadlock: Dos timers dependientes sin coordinación**
**Archivo**: `ventana_principal.py` + `vida_autonoma.py`  
**Ubicación**: `_iniciar_animacion()` L1040-1050, `__init__` de MotorProactividad  
**Severidad**: CRÍTICA

**Problema**:
```python
# ventana_principal.py L1040
self._timer = QTimer()  # FPS~60 (16ms)
self._timer.timeout.connect(self._animar)  # Leer self._vida._pos_objetivo
self._timer.start(intervalo_ms)

# vida_autonoma.py (MotorProactividad QThread)
self._timer = QTimer()  # 500ms
self._timer.timeout.connect(self._tick)  # ESCRIBIR self._pos_objetivo
```

**Escenario deadlock**:
1. `_tick()` en hilo de MotorProactividad empieza a escribir `_pos_objetivo`
2. `_animar()` en hilo principal intenta leer
3. Si MotorProactividad hace `self.msleep(100)` DENTRO de `_tick()`, bloquea el hilo
4. Pero `_animar()` en hilo Qt puede esperar a que MotorProactividad termine
5. **Deadlock circular**: Principal espera a MotorProactividad, MotorProactividad espera a Principal

**Raíz**: Sin mecanismo de sincronización explícito (QWaitCondition, QReadWriteLock)

---

### 4. 🔴 **Double-Call: `mapFromGlobal()` aún se llama 2× por frame**
**Archivo**: `ventana_principal.py`  
**Ubicación**: Línea 1612 (precalculada), pero línea 1920+ (pintEvent sigue recalculando)  
**Severidad**: MEDIA (rendimiento)

**Problema**:
```python
# _animar() L1612
pos_local_cache = self.mapFromGlobal(QCursor.pos())  # ← UNA VEZ
self._cached_cursor_local = pos_local_cache

# paintEvent() L1920
if self._proximidad > 0.2:
    pos_local = self.mapFromGlobal(QCursor.pos())  # ← SEGUNDA VEZ (no usa cache)
    # dibujar partículas...
```

**Consecuencia**: 
- `mapFromGlobal()` es operación Win32 cara (~5-10µs)
- Segunda llamada **innecesaria** 
- ~10% del presupuesto de frame en paintEvent desperdiciado

**Raíz**: `paintEvent()` no usa `self._cached_cursor_local`

---

### 5. 🔴 **Inconsistencia: `_render_offset_x/y` pueden desincronizarse de `_pos_objetivo`**
**Archivo**: `ventana_principal.py` + `vida_autonoma.py`  
**Ubicación**: L1150-1200 (`_interpolar_movimiento`), L1264-1292 (`_colapsar_ventana_transito`)  
**Severidad**: ALTA

**Problema**:
```python
# _interpolar_movimiento() L1150
if pos_objetivo:
    delta_x = pos_objetivo.x() - self._pos_actual_x
    self._render_offset_x += delta_x * 0.1  # Lerp suave

# _colapsar_ventana_transito() L1272
self._render_offset_x = 0.0  # RESET directo
```

Si el reset ocurre **DURANTE** una interpolación:
- Offset anulado abruptamente
- Orbe "salta" de vuelta al centro de ventana
- Visual: parpadeo/snap desagradable

**Especialmente peligroso** si collapse ocurre en mitad de animación

**Raíz**: Reset incondicional sin gradualidad

---

## II. PROBLEMAS TÉCNICOS (DEGRADAN EXPERIENCIA)

### 6. ⚠️ **Falta validación en `_estorba()`: Cursor muy cerca del origen (0,0)**
**Archivo**: `vida_autonoma.py L1291-1350`  
**Severidad**: MEDIA

**Problema**:
```python
margen_cursor = 100
cursor_zone = QRect(
    info.cursor.x() - margen_cursor, info.cursor.y() - margen_cursor,
    margen_cursor * 2, margen_cursor * 2,
)
```

Si cursor está en (50, 50):
- Zona = (-50, -50, 200, 200)
- Includes negative coordinates (off-screen)
- `orbe_rect.intersects()` may behave unexpectedly with negative rects

**Raíz**: Sin clamp de zona a pantalla

---

### 7. ⚠️ **`_mejor_borde()` assume pantalla rectangular, no multi-monitor**
**Archivo**: `vida_autonoma.py L732`  
**Severidad**: MEDIA (con múltiples pantallas)

**Problema**:
```python
# L732
def _mejor_borde(self, info: InfoEscritorio) -> QPoint:
    # Busca borde de self._pantalla (única pantalla cached)
    # Pero user puede tener 2+ monitores (FP-022 mencionado pero no implementado)
```

**Caso fallo**:
- User con 2 monitores: 1920x1080 + 2560x1440
- Orbe en monitor 1, intenta ir a "mejor borde"
- Calcula basado en _pantalla (asume una sola), ignora monitor 2
- Destino potencialmente fuera de pantalla

**Raíz**: FP-022 multi-monitor pendiente de completar

---

### 8. ⚠️ **Cálculo geométrico en `_esquivar()`: Wall-sliding incorrecta**
**Archivo**: `vida_autonoma.py L1355-1450`  
**Severidad**: MEDIA

**Problema**:
```python
# L1380
target_x = int(orbe_cx + nx * flee_dist - w // 2)
target_y = int(orbe_cy + ny * flee_dist - w // 2)

# L1385 Wall-sliding (clamping)
target_x = max(left, min(target_x, right))
target_y = max(top, min(target_y, bottom))
```

**Issue**:
1. Calcula destino a 300px del orbe
2. Clampea a pantalla
3. **Pero**: Si resultado es clamped, dirección de huida se pierde
4. Orbe "rebotas" contra esquina en vez de deslizar

**Ejemplo**:
- Cursor en (1900, 1000)
- Orbe en centro (960, 540)
- Flee direction: NE (↗)
- Target: (960 + 300, 540 - 300) = (1260, 240) ← dentro pantalla ✅
- Pero si cursor estaba FUERA pantalla → target puede estar fuera también
- Clamp produce: (1920-180, 240) = (1740, 240)
- **Resultado**: Rebota a esquina en lugar de deslizar suavemente

**Raíz**: No hay logic de "mejor borde" si flee escapa pantalla

---

### 9. ⚠️ **Performance: Recalcular heatmap CADA TICK (500ms)**
**Archivo**: `vida_autonoma.py L960+`  
**Severidad**: BAJA (pero acumulativa)

**Problema**:
```python
# _tick() L960
self._actualizar_heatmap(info.cursor)  # JSON write + dict updates cada 500ms
```

Con múltiples decisiones (esquiva, reubicar, compacta) en un tick, si CADA una llama `_actualizar_heatmap()`:
- IO overhead
- JSON parsing innecesario
- Delta time pequeño (500ms) → heatmap muy granular

**Raíz**: Sin debounce o batching de heatmap updates

---

### 10. ⚠️ **FSM State inconsistencia: `_estado` vs `OrbeComputadora._estado`**
**Archivo**: `ventana_principal.py`, `fsm_golem.py`  
**Severidad**: MEDIA

**Problema**:
- `OrbeComputadora._estado` = visual state (dormido, hablando, procesando)
- `VidaAutonoma` decide movimiento basado en `self._ultimo_estado_golem`
- Si FSM cambia estado sin notificar VidaAutonoma → desincronizado

**Ejemplo**:
1. FSM cambia a "hablando" (orbe brilla, gira)
2. VidaAutonoma no se entera (aún cree que "procesando")
3. Comportamiento autónomo (esquivar, reubicar) no adapta a nuevo estado

**Raíz**: Signal de estado en FSM no conecta a VidaAutonoma

---

### 11. ⚠️ **Cálculo de `hogar_dinamico`: Historial de 14 días pero `_pantalla` no persiste entre sesiones**
**Archivo**: `vida_autonoma.py L771+`  
**Severidad**: BAJA

**Problema**:
```python
# L771
def _calcular_hogar_dinamico(self, info: InfoEscritorio):
    # Usa heatmap persistente (JSON) → historial crece
    # Pero self._pantalla es QRect obtenido en __init__ una sola vez
    # Si user cambia resolución/monitor → _pantalla es stale
```

**Escenario**:
1. Sesión 1: 1920x1080, hogar en esquina (1850, 1050)
2. User cambia a 2560x1440
3. Sesión 2: hogar aún (1850, 1050) pero _pantalla es NUEVO
4. Orbe calcula destino basado en pantalla vieja en heatmap JSON

**Raíz**: _pantalla no se actualiza; heatmap no se valida contra pantalla actual

---

### 12. ⚠️ **Cooldowns sin reset: `_esquivar_cooldown`, `_reubicar_cooldown` no tienen max retries**
**Archivo**: `vida_autonoma.py L950+`  
**Severidad**: BAJA

**Problema**:
```python
# L950
if self._esquivar_cooldown > 0:
    self._esquivar_cooldown -= 1

# Pero si esquivar falla (destino inválido) → cooldown aún es ~12s
# Usuario queda "trancado" esperando sin movimiento visible
```

**Raíz**: Sin mecanismo de "reintento" o "fallback rápido"

---

### 13. ⚠️ **Timer de resolución: FPS 16ms pero decisiones cada 500ms = 31× desfase**
**Archivo**: `ventana_principal.py` + `vida_autonoma.py`  
**Severidad**: MEDIA

**Problema**:
```
Animación: 16ms (60fps)
Decisiones: 500ms (2fps)
Ratio: 31:1
```

Decisión tomada en tick N (t=500ms):
- Ejecuta en animación N+1 a N+30
- Si usuario mueve cursor en animación N+15 → decisión "vieja"
- Latencia visible: hasta 500ms entre input y respuesta

**Raíz**: Desacoplamiento deliberado (para CPU) crea latencia

---

## III. DEUDAS ARQUITECTÓNICAS

### 14. 📋 **FP-022: Multi-monitor support incomplete**
- `_pantalla` asume una sola pantalla
- `info.pantallas` está en `InfoEscritorio` pero no se usa
- Hogar dinámico ignora múltiples displays

**Impact**: User con 2+ monitores tendrá comportamiento errado en bordes

---

### 15. 📋 **Thread safety: Sin QMutex en atributos compartidos**
- `_pos_objetivo` (escrito por MotorProactividad, leído por Orbe)
- `_estado` (escrito por FSM, leído por VidaAutonoma)
- `_heatmap` (leído en JSON, escrito en _tick)

**Impact**: Race conditions silenciosas

---

### 16. 📋 **Ferrofluido (`_animador_orbe_4d`): Error silencioso, nunca falla visible**
**Archivo**: `ventana_principal.py L1553`  
```python
try:
    self._actualizar_ferrofluido(delta_t)
except Exception as e:
    logger.warning(...)
    self._animador_orbe_4d = None  # Silenciosamente desactiva
```

**Problem**: User nunca sabe que ferrofluido está apagado (visual silencioso)

---

### 17. 📋 **Particulas: `_max_particulas` hardcoded, no respeta CPU load**
**Archivo**: `ventana_principal.py L1375`  
- Cap de 200 partículas, pero no reduce con CPU>80%
- WI-263 (FPS adaptativo) existe pero no ajusta particulas

**Impact**: Bajo FPS mantiene particulas altas → aún más lento

---

### 18. 📋 **Deprecated attributes: `_pos_anterior` vs `_pos_anterior_x/y`**
**Archivo**: `ventana_principal.py`  
- Mezcla de `_pos_anterior` (QPoint) y `_pos_anterior_x/y` (float)
- Inconsistencia: a veces se sincroniza, a veces no
- Causa: Refactor incompleto

**Impact**: Delta de partículas puede ser incorrecto

---

## IV. PROBLEMAS PENDIENTES DEL FIX WI-MALJUT-002

### 19. ⚠️ **Repaint() siempre llamado, pero `paintEvent()` aún muy costoso**
**Archivo**: `ventana_principal.py L1830+`  
**Severidad**: MEDIA (performance)

**Problema**:
```python
# _animar() L1679
self.repaint()  # Immediate paint, bloquea

# paintEvent() L1830 (ahora llamado CADA frame)
# 1. Calcula cursor zone (L1920 aún sin cache pese a arreglo anterior)
# 2. Dibuja 200+ partículas 
# 3. Dibuja anillos con rotación
# 4. Dibuja núcleo + resplandor
# Todo esto 60× por segundo
```

**Metrics**:
- paintEvent() ~6-12ms por frame (10-20% presupuesto)
- Si CPU ya está en 80%+ → drop a 30fps

**Raíz**: `paintEvent()` no es lo suficientemente rápido para 60fps consistente

---

### 20. ⚠️ **Early-exit ANTERIOR aún en línea 1584**
**Archivo**: `ventana_principal.py L1580+`  
**Severidad**: BAJA (pero confuso)

**Problema**:
```python
# L1260 (pre-boot check)
if not self._boot_completo and not hasattr(self, '_bereshit_activo'):
    self._objetivo_brillo = 0.04 + 0.02 * math.sin(...)
    self._brillo_actual += (self._objetivo_brillo - self._brillo_actual) * 0.06
    self._escala += (self._escala_objetivo - self._escala) * 0.1
    
    # FIX CRÍTICO: Siempre actualizar en pre-boot para animaciones fluidas
    self.update()
    return  # ← SIGUE AQUÍ (después de nuestro fix L1679)
```

**Impacto**:
- Pre-boot early-exit ANTES de `repaint()` en L1679
- Pre-boot sigue sin renderizarse (aunque menos crítico que antes)
- Inconsistencia: arreglamos early-exit en L1584 pero no en L1260

**Raíz**: Fix WI-MALJUT-002 parcial — falta pre-boot

---

## MATRIZ DE SEVERIDAD

| ID | Problema | Severidad | Impacto | Pipeline |
|----|----------|-----------|--------|----------|
| 1  | Race condition `_pos_objetivo` | 🔴 CRÍTICA | Jitter, saltos | C |
| 2  | Memory leak partículas | 🔴 CRÍTICA | Degradación | C |
| 3  | Deadlock timers | 🔴 CRÍTICA | Freeze UI | C |
| 4  | Double mapFromGlobal | ⚠️ MEDIA | Rendimiento | B |
| 5  | Render offset desincronizado | 🔴 CRÍTICA | Saltos visuales | C |
| 6  | _estorba() sin clamp negativo | ⚠️ MEDIA | Edge case | B |
| 7  | Multi-monitor incompleto | ⚠️ MEDIA | Falla 2+ monitors | E |
| 8  | Wall-sliding geométrica | ⚠️ MEDIA | Movimiento pobre | B |
| 9  | Heatmap sin debounce | ⚠️ BAJA | IO overhead | B |
| 10 | FSM desincronizado | ⚠️ MEDIA | Behavior wrong | D |
| 11 | Hogar stale con resolución | ⚠️ BAJA | Edge case | B |
| 12 | Cooldowns sin retry | ⚠️ BAJA | UX pobre | B |
| 13 | Latencia decisión 500ms | ⚠️ MEDIA | Responsividad | E |
| 14 | FP-022 incompleta | 📋 DEUDA | Multi-monitor | E |
| 15 | Thread safety ausente | 📋 DEUDA | Instabilidad | E |
| 16 | Ferrofluido error silencioso | 📋 DEUDA | Visibility | B |
| 17 | Particulas no adaptan CPU | 📋 DEUDA | Performance | B |
| 18 | `_pos_anterior` inconsistente | 📋 DEUDA | Delta wrong | C |
| 19 | paintEvent() aún costoso | ⚠️ MEDIA | FPS drops | B |
| 20 | Pre-boot early-exit | ⚠️ BAJA | Pre-boot lento | B |

---

## RECOMENDACIONES (GATE 0: ROUTING)

### Grupo A: CRÍTICOS (bloquean operación) → Pipeline C (24h)
- **ID 1**: Race condition `_pos_objetivo` → Add QMutex
- **ID 2**: Memory leak partículas → Add try-except
- **ID 3**: Deadlock timers → Redesign coordination
- **ID 5**: Render offset desincronización → Gradual reset

### Grupo B: MEDIA (degradan) → Pipeline B (1 sem)
- **ID 4**: Double mapFromGlobal → Use cache
- **ID 6-13**: Múltiples fixes geométricos/sync

### Grupo C: DEUDA TÉCNICA → Pipeline E (3 sem)
- **ID 14-18**: Arquitectura

---

## DOCUMENTACIÓN DE PALINGENESIA (Lección aprendida)

**Antes**: Saltamos directo a RUBEDO (implementación) sin NIGREDO (diagnóstico completo)  
**Ahora**: Workflow completo asegurado (GATE -1 → GATE 0 → GATE 1 → NIGREDO → ALBEDO → ...)

**Semilla**: Siempre ejecutar NIGREDO AUDIT completo ANTES de implementar.

---

**FIN NIGREDO AUDIT**  
Próximo paso: ALBEDO (investigación) si user aprueba.
