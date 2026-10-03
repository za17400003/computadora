# 🛡️ Módulo Guardian — Gestor Centralizado

> **Responsabilidad Única**: Gestionar estado de Guardian de forma centralizada, con validación de feature flags y State Pattern.

---

## Propósito

Centralizar toda la lógica de Guardian en **UNA sola clase** (`GuardianManager`) en lugar de esparcirla en múltiples archivos.

### Problema Anterior (FRAGMENTADO)

```
nlu.py:
  - _activar_guardian()
  - _modo_guardian = boolean
  - _activar_guardian_por_bloqueo()

flujos_guardian.py:
  - activar_guardian(cerebro)
  - desactivar_guardian()

hechizos_hp.py:
  - Referencias a _modo_guardian

enciclopedia_guardian.py:
  - GrimorioGuardian (wrong name)
```

**Problema**: Feature flag no validado centralmente, responsabilidad esparcida, difícil de mantener.

### Solución Actual (CENTRALIZADO)

```
computadora/cerebro/guardian/
├── __init__.py              # Exports públicos
├── manager.py               # GuardianManager (State Pattern)
├── states.py                # GuardianState enum + transiciones
├── events.py                # GuardianStateChangeEvent dataclass
└── README.md                # Este archivo
```

**Beneficios**:
- ✅ Una entrada única para activación/desactivación
- ✅ Feature flag validado en UN solo lugar
- ✅ State Pattern: enum de estados + transiciones válidas
- ✅ Eventos para desacoplamiento
- ✅ Thread-safe con RLock

---

## Arquitectura

### Estados Posibles

```
Guardian:
  INACTIVE          ← Default, sistema abierto
    ↓ (activar)
  ACTIVE            → Requiere autenticación
    ↓ (desactivar)
  INACTIVE

  Transiciones especiales:
  INACTIVE ↔ SESSION_LOCKED (Windows+L)
  TRANSITIONING (temporal, para cambios complejos)
```

**Validación**: Transiciones definidas en `states.py::TRANSICIONES_VALIDAS` dict.

### Componentes

#### 1. `GuardianState` enum (states.py)

Define los 4 estados posibles:

```python
class GuardianState(Enum):
    INACTIVE = "inactivo"              # Abierto
    ACTIVE = "activo"                  # Protegido
    SESSION_LOCKED = "sesion_bloqueada"
    TRANSITIONING = "transicionando"
```

#### 2. `GuardianManager` class (manager.py)

Gestor centralizado:

```python
class GuardianManager:
    def __init__(self, cerebro, feature_flags)
    
    def puede_activar() -> bool
        """¿Feature flag permite activación?"""
    
    def activar(razon, origen) -> bool
        """Activa Guardian, respetando feature flag"""
    
    def desactivar(razon, origen) -> bool
        """Desactiva Guardian"""
    
    @property
    def activo() -> bool
        """¿Guardian está activo?"""
    
    @property
    def estado() -> GuardianState
        """Estado actual (thread-safe)"""
```

#### 3. `GuardianStateChangeEvent` dataclass (events.py)

Evento emitido en cambios:

```python
@dataclass
class GuardianStateChangeEvent:
    estado_anterior: GuardianState
    estado_nuevo: GuardianState
    razon: str           # "sesion_bloqueada", "comando_voz", etc
    origen: str          # "windows_lock", "nlu", "manual", etc
    timestamp: datetime
```

---

## Uso

### Inicialización

```python
from computadora.cerebro.guardian import GuardianManager

# En CerebroComputadora.__init__:
self.guardian_manager = GuardianManager(self, FeatureFlags)
```

### Activación con Validación

```python
# Desde nlu.py o donde sea
if self.guardian_manager.puede_activar():
    if self.guardian_manager.activar(
        razon="sesion_bloqueada", 
        origen="windows_lock"
    ):
        logger.info("Guardian activado")
    else:
        logger.warning("Guardian bloqueado por feature flag")
else:
    logger.warning("Guardian_activo feature flag=True, no se permite")
```

### Monitorear Cambios

```python
def on_guardian_state_change(evento):
    logger.info(f"Guardian cambió: {evento.estado_anterior.value} → {evento.estado_nuevo.value}")

self.guardian_manager.registrar_callback_state_change(on_guardian_state_change)

def on_activation_blocked(razon, origen):
    logger.warning(f"Activación bloqueada: {razon} desde {origen}")

self.guardian_manager.registrar_callback_activation_blocked(on_activation_blocked)
```

### Desactivación

```python
self.guardian_manager.desactivar(razon="cierre_sesion")
```

---

## Feature Flag Integration

**Feature flag**: `guardian_activo` en `config.json`

```json
{
  "guardian_activo": false
}
```

**Semántica**:
- `guardian_activo: false` → "Guardian NO debe estar activo" → Se permite activar (para testing)
- `guardian_activo: true` → "Guardian debe estar activo" → Se bloquea activación automática

**Validación centralizada**:

```python
# En GuardianManager.puede_activar():
flag_value = self._feature_flags.obtener("guardian_activo")
return flag_value is False  # Guardian_activo=False permite activación
```

---

## Integración con Otros Módulos

### nlu.py

**Antes** (MAL):
```python
def procesar(self, texto):
    if self._modo_guardian:  # Boolean esparcido
        # Protección
    else:
        # Sin protección
```

**Ahora** (BIEN):
```python
def procesar(self, texto):
    if self.guardian_manager.activo:  # Centralizado
        # Protección
    else:
        # Sin protección
```

### SessionLockListener (Windows+L)

**Antes** (MAL):
```python
def on_session_lock():
    cerebro._activar_guardian_por_bloqueo()  # Directo, sin centralización
```

**Ahora** (BIEN):
```python
def on_session_lock():
    cerebro.guardian_manager.activar(
        razon="sesion_bloqueada",
        origen="windows_lock"
    )
```

### flujos_guardian.py (DEPRECATED)

**Antes**:
```python
def activar_guardian(cerebro):
    cerebro._modo_guardian = True  # Sin validación
```

**Ahora** (REEMPLAZADO):
```python
def activar_guardian(cerebro):
    """Delegado a GuardianManager (DEPRECATED — usar manager directamente)"""
    return cerebro.guardian_manager.activar(
        razon="flujo_manual",
        origen="flujo_guardian"
    )
```

---

## Tests

### Test 1: Feature Flag Bloquea Activación

```python
def test_guardian_activacion_bloqueada_por_feature_flag():
    """Si guardian_activo=True, activación debe ser bloqueada."""
    feature_flags.activar("guardian_activo")  # Simular flag=True
    
    resultado = manager.activar(razon="test", origen="test")
    
    assert resultado == False
    assert manager.estado == GuardianState.INACTIVE
    logger.assert_logged("⛔ Intento de activar Guardian BLOQUEADO")
```

### Test 2: Transición de Estado Válida

```python
def test_guardian_transicion_valida():
    """Transición INACTIVE → ACTIVE debe ser válida."""
    feature_flags.desactivar("guardian_activo")  # flag=False
    
    resultado = manager.activar(razon="test", origen="test")
    
    assert resultado == True
    assert manager.estado == GuardianState.ACTIVE
    assert manager.activo == True
```

### Test 3: Transición Inválida Rechazada

```python
def test_guardian_transicion_invalida():
    """ACTIVE → ACTIVE no debería ser válida."""
    # Setup: Guardian en ACTIVE
    manager._estado = GuardianState.ACTIVE
    
    # Intentar transición inválida
    resultado = manager.desactivar()
    resultado = manager.desactivar()  # ACTIVE → INACTIVE → ACTIVE (2 veces)
    
    # Debería fallar la segunda
    assert resultado == True  # Primera desactivación OK
    # ...
```

---

## Migration Path from Flujos_Guardian

### Pasos de Migración

1. **Crear GuardianManager** ✅ (HECHO)
2. **Refactorizar nlu.py**:
   - Reemplazar `self._activar_guardian()` → `self.guardian_manager.activar()`
   - Reemplazar `self._modo_guardian` → `self.guardian_manager.activo`
3. **Refactorizar SessionLockListener**:
   - Delegado a GuardianManager
4. **Deprecar flujos_guardian.py**:
   - Mantener si es importado, pero delegado a manager
5. **Tests**:
   - Cobertura >90%
   - Todos casos de feature flag

---

## Lecciones Aprendidas (PALINGENESIA)

**Verdad**: La arquitectura de Guardian era FRAGMENTADA — eso causaba bugs y confusión.
**Consecuencia**: Feature flags no eran respetados en TODAS las rutas → Sistema se portaba inconsistentemente.
**Solución**: Concentrar responsabilidad en UNA clase con State Pattern.
**Beneficio**: Mantenimiento más fácil, testing más simple, comportamiento predecible.

---

**Fin de documentación. Referencia: `/computadora/cerebro/guardian/`**
