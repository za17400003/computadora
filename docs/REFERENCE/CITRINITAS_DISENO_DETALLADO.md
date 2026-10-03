# CITRINITAS — Iluminación: Diseño Detallado (Mayo 31, 2026)

## Investigación Externa: Best Practices

### 1. Timeout Strategy (¿Cómo Esperar a Ollama?)

**Patrón Industry Standard**:
```python
# PATTERN 1: Fixed Timeout
timeout = 30  # Espera hasta 30s
→ PROBLEMA: Si Ollama tarda 40s, falla

# PATTERN 2: Adaptive Timeout (✅ Lo que hacemos)
recientes_latencias = [2.5, 3.1, 2.8, 4.2, 3.5]
promedio = 3.2s
timeout = int(promedio * 3)  # 9.6s clamped a [5, 180]
→ VENTAJA: Se auto-ajusta a carga real del servidor
```

**Nuestra Implementación (Ya es smart)**:
```python
def _timeout_adaptativo(self) -> int:
    if len(self._latencias_ollama) < 3:
        return 30  # Default prudente
    recientes = self._latencias_ollama[-10:]
    promedio = sum(recientes) / len(recientes)
    timeout = int(max(5, min(180, promedio * 3)))  # 5-180s range
    return timeout
```

**Decisión**: MANTENER. Es robusto.

---

### 2. Availability Check Pattern

**PATTERN A: Background Watchdog**
```
✅ Ventaja: No bloquea main thread
❌ Desventaja: False positives, sleep delays, wasteful
USADO POR: Microservicios grandes (Kubernetes, Docker)
PORQUÉ NO AQUÍ: Local machine, single process
```

**PATTERN B: On-Demand Check (✅ Lo que proponemos)**
```
✅ Ventaja: Rápido (<5ms), solo cuando necesitas, sin overhead
❌ Desventaja: Si primer POST falla, esperas timeout completo
USADO POR: Simples tools, CLIs, scripts
PORQUÉ AQUÍ: No hay 100 usuarios simultáneos
```

**PATTERN C: Hybrid (Check + Retry)**
```
1. Quick check (5ms timeout)
2. If no: escalar a N3
3. If yes: POST con timeout adaptativo + reintenta 1x
→ IMPLEMENTAMOS ESTO (opción B + retry in POST)
```

**Decisión**: On-Demand (Pattern B) + Retry (Pattern C).

---

### 3. Retry Logic Best Practices

**PATTERN A: Exponential Backoff**
```python
for intento in range(max_intentos):
    try:
        result = llamar_servicio()
        return result
    except Exception:
        delay = 2 ** intento  # 1s, 2s, 4s, 8s...
        time.sleep(delay)
→ VENTAJA: Reduce tormenta de reintentos
→ DESVENTAJA: Lento (2+4+8 = 14s para 3 intentos)
```

**PATTERN B: Simple Retry (✅ Lo que ya hacemos)**
```python
for intento in range(2):
    try:
        result = llamar_servicio()
        return result
    except:
        if intento == 0:
            time.sleep(1)  # Solo una espera
        else:
            raise
→ VENTAJA: Rápido (máximo 1s espera), simple
→ DESVENTAJA: No escala con tormenta extrema
→ SUFICIENTE PARA: Local Ollama (no distribuido)
```

**PATTERN C: Exponential + Jitter**
```python
# Para distributed services (AWS, GCP)
delay = (2 ** intento) + random(0, 1)
→ OVERKILL PARA: Local single-box
```

**Decisión**: MANTENER Pattern B (simple + 1 reintento).

---

### 4. Fallback Strategy

**Nuestro Actual**:
```
N1 (regex) → OK: retorna
          → NO: 
            → N2 (Ollama) → OK: retorna
                         → TIMEOUT/ERROR: N3 (Copilot)
            → N3 (Copilot) → OK: retorna
                           → ERROR: N1 (fallback honesto)
```

**¿Es bueno?**: 
- ✅ Cascada lógica clara
- ✅ Graceful degradation
- ✅ Nunca devuelve basura
- ❌ PERO: Si Ollama tarda 20s, quick_ping falla prematuramente

**Propuesta**: Aumentar quick_ping timeout (2s → 5s) SOLO en boot.

```python
def _quick_ping_ollama(self, startup: bool = False) -> bool:
    timeout = 5 if startup else 2  # 5s en boot, 2s después
    try:
        r = requests.get("...", timeout=timeout)
        return r.status_code == 200
    except:
        return False
```

**Decisión**: Agregar startup mode para primera check más generosa.

---

## Diseño: Implementación Paso a Paso

### Paso 1: Remover el Watchdog

**Cambio 1A**: Línea ~1028 (eliminar)
```python
# ANTES:
threading.Thread(target=self._verificar_ollama, daemon=True, name="ollama-check").start()

# DESPUÉS:
# (nada)
```

**Cambio 1B**: Línea 961 (simplificar flags)
```python
# ANTES:
self.ollama_disponible = False
self._ollama_proceso_muerto = False

# DESPUÉS:
self.ollama_disponible = True  # Optimistic: assumes OK until proven wrong
```

**Cambio 1C**: Eliminar métodos innecesarios
```python
# Eliminar completamente:
def _verificar_ollama(self):
    # Líneas 1172-1214 (43 líneas)
    
def _iniciar_reconexion_background(self):
    # Líneas 1288-1307 (20 líneas)
    
def _ollama_proceso_activo(self) -> bool:
    # Líneas 1274-1287 (14 líneas)
    
def liberar_modelos_ollama(self):
    # Líneas 1257-1273 (17 líneas)
    
def _check_ollama_degradacion(self) -> bool:
    # Líneas 1251-1255 (5 líneas)
    
# Total: 99 líneas eliminadas
```

---

### Paso 2: Mejorar quick_ping

**Cambio 2A**: Línea ~1217 (agregar startup mode)
```python
def _quick_ping_ollama(self, startup: bool = False) -> bool:
    """Check rápido antes de decidir N2.
    En startup: 5s (Ollama puede estar cargando modelo).
    En runtime: 2s (debe ser instantáneo).
    """
    timeout = 5 if startup else 2
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception as e:
        logger.debug(f"Ping Ollama falló: {e}")
        return False
```

**Cambio 2B**: Línea ~1024 (llamar con startup=True en boot)
```python
# En __init__, después de crear CerebroComputadora:
# Primer check al inicio (5s generoso)
if not self._quick_ping_ollama(startup=True):
    logger.warning("Ollama no accesible en boot (escalará a N3)")
else:
    logger.info("✅ Ollama accesible en boot")
```

---

### Paso 3: Refactorizar el Routing

**Cambio 3A**: Línea ~1500-1610 (simplificar flujo)
```python
# ANTES (complejo, con verificaciones redundantes):
if self.ollama_disponible and not self._quick_ping_ollama():
    logger.warning("Quick ping Ollama falló...")
    self.ollama_disponible = False

if not self.ollama_disponible:
    proceso_vivo = self._ollama_proceso_activo()  # ← innecesario
    if proceso_vivo:
        for espera in (1, 2, 3):
            self._verificar_ollama()  # ← innecesario
            if self.ollama_disponible:
                break
            time.sleep(espera)

if not self.ollama_disponible:
    return self._pensar_con_copilot(texto)  # Escala a N3
else:
    return self._pensar_con_herramientas(texto)  # Va a N2

# DESPUÉS (limpio, 3 líneas):
if not self._quick_ping_ollama():
    logger.debug("Ollama no accesible → N3")
    return self._pensar_con_copilot(texto)

return self._pensar_con_herramientas(texto)
```

---

### Paso 4: Mantener & Validar Retry Logic

**Sin cambios** en `_llamar_ollama_impl()`:
```python
# Líneas 3757-3802: MANTENER TAL CUAL
# Ya reintenta en 500 error
# Ya tiene timeout adaptativo
# Ya registra latencias
```

---

## Síntesis Dorada: Cambios Mínimos

| Archivo | Líneas | Acción | Rationale |
|---------|--------|--------|-----------|
| nlu.py | 1028 | Eliminar | Watchdog innecesario |
| nlu.py | 961 | Modificar flag | Simplificar estado |
| nlu.py | 1172-1307 | Eliminar 5 métodos | Redundantes |
| nlu.py | 1217-1225 | Actualizar | Agregar startup mode |
| nlu.py | 1500-1610 | Refactor | Simplificar routing |
| config.json | ? | Verificar | Quitar TIMEOUT si existe |

---

## Validación Post-Cambios

### Test 1: N1 (Regex) — No debe cambiar
```
Usuario: "Hola computadora"
→ Nivel 1 match
→ Respuesta <100ms
✅ Igual que antes
```

### Test 2: N2 (Ollama) — Debe ser más rápido
```
Usuario: "Piensa en la vida"
→ Quick ping (5ms)
→ N2 → POST → Reintento si 500 → OK
→ Respuesta en 15-60s (sin falsos 30s delays)
✅ Mejora: sin watchdog delays
```

### Test 3: N3 (Copilot) — Fallback si Ollama no responde
```
Usuario: pregunta (Ollama OFF)
→ Quick ping timeout (2s)
→ N3 → Copilot API
→ Respuesta en 5-30s
✅ Igual que antes (pero sin watchdog confusión)
```

### Test 4: Startup — Ollama tardío
```
Boot: Ollama aún cargando (15s)
→ Quick ping (5s timeout, startup=True)
→ Si falla: escalada a N3 (razonable)
→ Si OK: va a N2 (correcto)
✅ Mejora: 5s más generoso en boot
```

---

**Status**: 🟠 CITRINITAS COMPLETO — Síntesis diseñada
