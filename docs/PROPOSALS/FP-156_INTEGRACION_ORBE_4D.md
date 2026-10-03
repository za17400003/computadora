# FP-156: GUÍA DE INTEGRACIÓN — Orbe 4D en ventana_principal.py

**Status**: 📋 PLANTILLA LISTA PARA INTEGRACIÓN  
**Archivos Dependientes**: `ventana_principal.py`, `pintarMarquee()`, `_animar()`

---

## 🎯 Resumen de Cambios

1. **Auto-instalación de deps** ✅ 
   - En `computadora/voz/escucha.py` ya integrado
   - Ejecutar: `python -m computadora.utilidad.auto_instalar_deps`

2. **Teseracto 4D** ✅ 
   - `computadora/geometria/teseracto_4d.py` creado
   - 16 vértices, 32 aristas, 6 planos de rotación

3. **Ferrofluido Mercurial** ✅ 
   - `computadora/geometria/ferrofluido.py` creado
   - 800 partículas, atracción dinámica a geometría

4. **Animador Orbe 4D** ✅ 
   - `computadora/interfaz/animador_orbe_4d.py` creado
   - Sincronización estado emocional + ciclo circadiano

---

## 🔗 Integración en ventana_principal.py

### Paso 1: Importar el animador

```python
# En imports del archivo (cerca de línea 52)
from computadora.interfaz.animador_orbe_4d import (
    AnimadorOrbe4D,
    crear_animador_orbe_4d_defecto,
)
```

### Paso 2: Inicializar en __init__

```python
def __init__(self, padre=None, config=None):
    super().__init__(padre)
    # ... código existente ...
    
    # FP-156: Inicializar animador orbe 4D
    self._animador_orbe_4d = crear_animador_orbe_4d_defecto(self)
    logger.info("🎬 FP-156: Animador Orbe 4D inicializado")
```

### Paso 3: Actualizar en el loop de animación (paintEvent)

En el método `paintEvent` o en `_animar`, agregar:

```python
def paintEvent(self, event):
    """Renderiza el orbe con ferrofluido 4D."""
    painter = QPainter(self)
    
    # ... código de renderizado existente ...
    
    # FP-156: Renderizar orbe 4D
    delta_t = 1.0 / 60.0  # Asumir 60 FPS
    self._animador_orbe_4d.actualizar(delta_t)
    self._animador_orbe_4d.renderizar(painter, self.width(), self.height())
    
    # ... resto del código ...
    painter.end()
```

### Paso 4: Sincronizar estado emocional

Cuando el orbe cambie de estado (ESCUCHANDO, HABLANDO, etc.):

```python
def cambiar_estado(self, nuevo_estado: str):
    """Cambia el estado del orbe (reposo, hablando, pensando, etc.)"""
    super().cambiar_estado(nuevo_estado)  # Llamar a método original
    
    # FP-156: Actualizar animador 4D
    self._animador_orbe_4d.actualizar_estado(nuevo_estado)
```

---

## 🧪 Testing Rápido

```bash
# Test unitario del teseracto
python -m computadora.geometria.teseracto_4d

# Test unitario del ferrofluido
python -m computadora.geometria.ferrofluido

# Test del animador (sin GUI)
python -m computadora.interfaz.animador_orbe_4d

# Boot completo con verificación de deps
.\iniciar_computadora_verificado.bat
```

---

## 🎨 Personalización

### Cambiar velocidad de rotación

En `AnimadorOrbe4D.__init__`:
```python
config = ConfigAnimadorOrbe4D()
config.vel_rotacion_hablando = 1.2  # Más rápido
config.vel_rotacion_reposo = 0.05   # Más lento
self.animador = AnimadorOrbe4D(orbe, config)
```

### Cambiar número de partículas

En `ferrofluido.py`:
```python
config = ConfigFerrofluido()
config.num_particulas = 1200  # Más partículas = más lindo pero lento
```

### Cambiar factor circadiano

```python
config.factor_circadiano_enabled = False  # Deshabilitar influencia de hora
```

---

## 🚀 Próximos Pasos (PALINGENESIA)

1. **Integración en ventana_principal**: Reemplazar renderización de orbe actual
2. **Testing full**: Boot + demos + interactividad del usuario
3. **Optimización**: Profiling CPU, reducir partículas si es necesario
4. **Sonido sincronizado**: Frecuencia de rotación = frecuencia de Whisper
5. **Interactividad**: Permitir que usuario "empuje" el ferrofluido

---

## 📊 Arquitectura

```
ventana_principal.py (OrbeComputadora)
    ↓
AnimadorOrbe4D (FP-156)
    ↓
    ├─ Teseracto4D (FP-154)
    │   ├─ Rotaciones 4D
    │   ├─ Proyección 4D→3D→2D
    │   └─ Aristas
    │
    └─ FerroffluidoMercurial (FP-155)
        ├─ 800 partículas
        ├─ Cálculo de atractores
        └─ Animación fluida
```

---

## ✅ Checklist Pre-Deploy

- [ ] `auto_instalar_deps.py` integrado en escucha.py
- [ ] Tests unitarios pasan (teseracto, ferrofluido, animador)
- [ ] Imports añadidos en ventana_principal.py
- [ ] Inicialización en `__init__` completada
- [ ] `paintEvent` updated con renderización 4D
- [ ] Estado emocional sincroniza con animador
- [ ] Boot completo sin errores
- [ ] FPS estable en 60 (min 30)
- [ ] Ferrofluido visible y fluido
- [ ] Documentación usuario agregada

---

**Responsable**: GitHub Copilot (Abril 28, 2026)  
**Categoría**: RUBEDO — Manifestación visual  
**Prioridad**: 🔴 ALTA (core experience del orbe)
