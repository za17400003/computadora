# ALBEDO — Purificación: Arquitectura Limpia (Mayo 31, 2026)

## Filtración y Clasificación

### Qué Se Queda (Esencial)

| Componente | Por Qué | Línea | Uso |
|-----------|---------|-------|-----|
| `quick_ping_ollama()` | Verifica disponibilidad antes de N2 | 1217-1225 | Línea 1531 |
| `_timeout_adaptativo()` | Calcula timeout basado en latencias | 1230-1243 | _llamar_ollama_impl |
| `_latencias_ollama[]` | Historial de latencias (últimas 20) | 1030 | Adaptive timeout |
| `_llamar_ollama_impl()` | Reintentos (500 error) + timeout | 3757-3802 | Core N2 call |
| `ollama_disponible` flag | Estado actual conocido | 960 | Decisión N1/N2/N3 |

---

### Qué Se Va (Innecesario)

| Componente | Redundante Con | Razón |
|-----------|----------------|-------|
| `_verificar_ollama()` loop | `quick_ping_ollama()` | Ambos hacen GET /api/tags |
| Watchdog thread daemon | N/A | Innecesario; check on-demand |
| `_ollama_proceso_muerto` | `ollama_disponible` | Una flag es suficiente |
| 30s sleep después fallos | `_timeout_adaptativo()` | Timeout adaptativo es más smart |
| `_iniciar_reconexion_background()` | Fallback a N3 | Si N2 falla, escala a N3 |

---

## Arquitectura Propuesta: 2 Capas (Simple)

### Capa 1: Quick Availability Check (On-Demand)
```python
def _quick_ping_ollama(self) -> bool:
    """5ms check antes de decidir N2 vs N3"""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False
```

**Ubicación**: Línea ~1531 (justo antes de decidir N1/N2/N3)

```python
if not self._quick_ping_ollama():
    logger.debug("Ollama no accesible → escalando a N3")
    return self._pensar_con_copilot(texto)
```

---

### Capa 2: Robust Retry Logic (In-Call)
```python
def _llamar_ollama_impl(self, mensajes: list, num_predict: int = 150) -> str | None:
    """Reintentos automáticos + timeout adaptativo"""
    timeout = self._timeout_adaptativo()
    
    for intento in range(2):
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            if r.status_code == 500 and intento == 0:
                logger.warning("500, reintentando...")
                time.sleep(2)
                continue
            r.raise_for_status()
            return r.json()["message"]["content"]
        except requests.exceptions.Timeout:
            if intento == 0:
                time.sleep(1)
                continue
            logger.error("Timeout en Ollama")
            return None
    return None
```

**Ubicación**: Línea ~3757 (core N2 execution)

---

## Decision Tree (Flujo Limpio)

```
Usuario → N1 (regex)?
    ├─ YES → Retorna <100ms
    └─ NO → Quick Ping Ollama?
            ├─ YES → N2 (Ollama)
            │         ├─ POST ok → Retorna respuesta
            │         ├─ 500 error → Reintenta (2x)
            │         ├─ Timeout → Escalada a N3
            │         └─ Connection error → Escalada a N3
            └─ NO → N3 (Copilot/Gemini)
```

**Ventajas**:
- ✅ Máximo 2 checks: quick_ping (5ms) + POST (15-60s)
- ✅ Sin threads daemon innecesarios
- ✅ Reintentos donde cuenta (en la llamada real)
- ✅ Timeout adaptativo + fallback automático
- ✅ Código legible: 1 decisión → 1 acción

---

## Cambios Requeridos

### 1. ELIMINAR
```python
# Línea 1028: REMOVER
threading.Thread(target=self._verificar_ollama, daemon=True).start()

# Línea 1172-1214: ELIMINAR método completo
def _verificar_ollama(self):
    # ...

# Línea 1288-1307: ELIMINAR método completo
def _iniciar_reconexion_background(self):
    # ...

# Línea 961: ELIMINAR (reemplazar con simple flag)
self._ollama_proceso_muerto = False
```

### 2. SIMPLIFICAR
```python
# Línea 1215-1225: MANTENER (ya es eficiente)
def _quick_ping_ollama(self) -> bool:
    """Cambio ÚNICO: timeout 5s → 2s (más responsivo)"""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False

# Línea 1230-1243: MANTENER (ya es smart)
def _timeout_adaptativo(self) -> int:
    """Sin cambios — esto es bueno"""
    pass
```

### 3. ACTUALIZAR ROUTING
```python
# Línea 1476-1610: En _pensar()
# NUEVO flujo:

nivel1 = self._pensar_nivel1(texto)
if nivel1 is not None:
    return nivel1

# ANTES:
# if self.ollama_disponible and not self._quick_ping_ollama():
#     self.ollama_disponible = False

# DESPUÉS (sin watchdog):
if not self._quick_ping_ollama():
    logger.debug("Ollama no accesible → N3")
    return self._pensar_con_copilot(texto)

# Si quick_ping OK, procede a N2
return self._pensar_con_herramientas(texto)
```

---

## Estado Post-ALBEDO

### Configuración Final
```python
# En __init__:
self.ollama_disponible = True  # Optimistic assumption
self._latencias_ollama: list[float] = []

# NO más:
# - self._ollama_proceso_muerto
# - watchdog thread
# - reconexión background
# - verificar_ollama loop
```

### Métodos Que Quedan
| Método | Línea | Propósito |
|--------|-------|----------|
| `_quick_ping_ollama()` | 1217 | Check antes de N2 |
| `_timeout_adaptativo()` | 1230 | Timeout smart |
| `_llamar_ollama()` | 3751 | Guard + impl |
| `_llamar_ollama_impl()` | 3757 | POST + retry |
| `_llamar_ollama_streaming()` | 3806 | Stream version |

### Métodos Que Se Eliminan
| Método | Razón |
|--------|-------|
| `_verificar_ollama()` | Watchdog innecesario |
| `_iniciar_reconexion_background()` | N3 ya es fallback |
| `_ollama_proceso_activo()` | No lo necesitamos |
| `liberar_modelos_ollama()` | WI-324 demasiado complejo |
| `_check_ollama_degradacion()` | Timeout adaptativo mejor |

---

## Purificación Completa

**Líneas a Eliminar**: ~150 líneas innecesarias  
**Métodos a Remover**: 5 completos  
**Threads Daemon**: -1 (menos complejidad)  
**Flags Globales**: -2 (una basta)  

**Resultado**: Código limpio, predecible, sin magic.

---

**Status**: 🟡 ALBEDO COMPLETO — Clasificación pura
