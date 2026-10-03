# WI-295 — AttributeError `_cpu_display` FIX (Abril 27, 2026)

**Problema**: 
```
AttributeError: 'VidaAutonoma' object has no attribute '_cpu_display'
  at ventana_principal.py:1901 in paintEvent()
```

**Causa Raíz**: `VidaAutonoma.__init__` no inicializaba atributos de métricas (`_cpu_display`, `_ram_display`, etc.)

**Solución**: Agregar inicialización de atributos al __init__

**Status**: ✅ **COMPLETADO**

---

## Análisis (NIGREDO + ALBEDO)

### El Problema
```
ventana_principal.py línea 1901:
    dibujar_indicador_recursos(
        painter, cx, cy, brillo, self._draw_state(),
        self._vida._cpu_display,      # ← AttributeError aquí
        self._vida._ram_display,
        self._vida._gpu_display,
        self._vida._disk_display,
        self._vida._disk_io_display,
        ...
    )
```

**Raíz**: `VidaAutonoma.__init__` NO inicializaba estos atributos:
```python
# ANTES: __init__ incompleto
def __init__(self, metatron, orbe_widget):
    self.metatron = metatron
    self.orbe = orbe_widget
    self.estado_actual = EstadoOrbe.IDLE
    # ← Faltaba inicializar _cpu_display, _ram_display, etc.
```

---

## Solución (RUBEDO)

### Cambio en `computadora/interfaz/vida_autonoma.py`

```python
class VidaAutonoma:
    def __init__(self, metatron, orbe_widget):
        self.metatron = metatron
        self.orbe = orbe_widget
        self.estado_actual = EstadoOrbe.IDLE
        
        # WI-242/254/261: Métricas de sistema para indicador visual en el orbe
        self._cpu_percent = 0.0
        self._ram_percent = 0.0
        self._gpu_percent = -1.0   # -1 = no disponible
        self._disk_percent = 0.0
        self._disk_io_activity = 0.0
        
        # WI-251: Smoothed display values (interpolated, usados por ventana_principal.py)
        self._cpu_display = 0.0
        self._ram_display = 0.0
        self._gpu_display = -1.0
        self._disk_display = 0.0
        self._disk_io_display = 0.0
```

### Por Qué Esto Arregla el Error
- `ventana_principal.paintEvent()` intenta acceder a `self._vida._cpu_display`
- Ahora `VidaAutonoma.__init__` INICIALIZA `_cpu_display = 0.0`
- El atributo existe → NO hay `AttributeError`
- El valor inicial es 0.0 (correcto para mostrar 0% al iniciar)

---

## Verificación (CITRINITAS)

**Atributos Requeridos por ventana_principal.py línea 1901**:
- `_cpu_display` ✅ Ahora inicializado
- `_ram_display` ✅ Ahora inicializado
- `_gpu_display` ✅ Ahora inicializado
- `_disk_display` ✅ Ahora inicializado
- `_disk_io_display` ✅ Ahora inicializado

Estos atributos se usan en `dibujar_indicador_recursos()` para mostrar arcos giratorios de recursos del sistema.

---

## Archivo Modificado

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `computadora/interfaz/vida_autonoma.py` | Agregada inicialización de 10 atributos en __init__ | 498-517 |

---

## Patrón Aprendido (FP-150: EMET)

**Regla: Always initialize all attributes referenced in other parts of the codebase**

Cuando una clase `X` es usada por clase `Y`:
- `Y` espera que ciertos atributos de `X` existan
- `X.__init__` DEBE inicializar todos esos atributos
- Si falta uno → `AttributeError` en runtime

**Prevention**: 
- Revisar dónde se usa la clase
- Verificar qué atributos se acceden
- Inicializar TODOS en __init__

---

**Firma**: ✅ WI-295 COMPLETADO  
**Causa**: Inicialización incompleta de VidaAutonoma  
**Fix**: Agregar 10 líneas de inicialización  
**Impacto**: Sistema arranca sin error, indicador de recursos funciona  
**Testing**: "18:33:09 | INFO — COMPUTADORA ha despertado" (sin AttributeError) ✓
