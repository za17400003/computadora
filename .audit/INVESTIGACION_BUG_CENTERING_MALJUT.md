# 🔍 INVESTIGACIÓN: BUG DE CENTERING COORDENADAS EN MOVIMIENTO AUTÓNOMO MALJUT

**Fecha**: Mayo 2, 2026  
**Estado**: 🔴 IDENTIFICADO Y DOCUMENTADO  
**Síntoma**: Anillos y ferrofluido desplazados durante movimiento autónomo  
**Severidad**: 🔴 CRÍTICO — Desconexión visual entre orbe y capas renderizadas

---

## 📋 RESUMEN DEL PROBLEMA

Durante movimiento autónomo (esquive, regreso a hogar), el orbe (esfera central) se posiciona correctamente pero los anillos sagrados y el ferrofluido 4D aparecen **offset** (desplazados respecto al orbe).

**Reporte del usuario**:
> "cuando se mueve, los anillos y el ferrofluido se ponen en diferentes lugares"

---

## 🔬 ANÁLISIS DE FLUJO DE RENDERING

### 1. INICIALIZACIÓN DE OFFSETS (ventana_principal.py, líneas 698-699)

```python
self._render_offset_x = 0.0
self._render_offset_y = 0.0
self._en_transito = False
```

**Estado inicial**: Ambos offsets son cero (orbe en centro de ventana).

---

### 2. FASE DE EXPANSIÓN VENTANA (vida_autonoma.py, líneas 1355-1399)

Cuando el movimiento autónomo inicia:

```python
def _expandir_ventana_transito(self):
    """RF-340: Expande la ventana para cubrir origen + destino del movimiento."""
    # ... cálculos de bounding box ...
    
    orbe_pos = self._orbe.pos()  # Posición actual ventana
    tam = self.TAMANO_PLENO  # 180px (normal) o 50px (compacto)
    
    # Nueva ventana cubre origen → destino + margen
    x1 = min(orbe_pos.x(), self._pos_objetivo.x()) - margen
    y1 = min(orbe_pos.y(), self._pos_objetivo.y()) - margen
    x2 = max(orbe_pos.x(), self._pos_objetivo.x()) + tam + margen
    y2 = max(orbe_pos.y(), self._pos_objetivo.y()) + tam + margen
    
    new_w = x2 - x1
    new_h = y2 - y1
    
    # ⚠️ CÁLCULO CRÍTICO: Posicionar orbe dentro ventana expandida
    orbe_local_x = float(orbe_pos.x() - x1)  # Coordenadas locales respecto nueva ventana
    orbe_local_y = float(orbe_pos.y() - y1)
    
    # offset = orbe_local - centro_ventana
    self._orbe._render_offset_x = orbe_local_x + tam / 2.0 - new_w / 2.0
    self._orbe._render_offset_y = orbe_local_y + tam / 2.0 - new_h / 2.0
    
    # ⚠️ LIMITACIÓN DE OFFSET (clamping)
    max_off_x = max(0.0, new_w / 2.0 - tam / 2.0)
    max_off_y = max(0.0, new_h / 2.0 - tam / 2.0)
    self._orbe._render_offset_x = max(-max_off_x, min(self._orbe._render_offset_x, max_off_x))
    self._orbe._render_offset_y = max(-max_off_y, min(self._orbe._render_offset_y, max_off_y))
    
    # ⚠️ APLICAR CAMBIOS GEOMÉTRICOS
    self._orbe.resize(new_w, new_h)
    self._orbe.move(x1, y1)  # ← VENTANA REPOSICIONADA
```

**Estado después expansión**: 
- Ventana ahora ocupa área más grande
- `_render_offset_x/y` ≠ 0 (orbe desplazado del centro de ventana)
- Ventana física ha sido movida a `(x1, y1)`

---

### 3. INTERPOLACIÓN DURANTE MOVIMIENTO (vida_autonoma.py, líneas 1320-1346)

```python
def _interpolar_movimiento(self):
    # ... checks y validaciones ...
    
    if not self._orbe._en_transito:
        self._expandir_ventana_transito()
    
    # --- Fase 2: Interpolar offset hacia destino ---
    win_pos = self._orbe.pos()  # POSICIÓN ACTUAL VENTANA (en pantalla)
    
    # Destino en coordenadas LOCALES de ventana expandida
    dest_local_x = float(self._pos_objetivo.x() - win_pos.x())
    dest_local_y = float(self._pos_objetivo.y() - win_pos.y())
    
    # Calcular offset target para mover orbe hacia destino
    w_half = self._orbe.width() / 2.0
    h_half = self._orbe.height() / 2.0
    target_off_x = dest_local_x + self.TAMANO_PLENO / 2.0 - w_half
    target_off_y = dest_local_y + self.TAMANO_PLENO / 2.0 - h_half
    
    # Interpolar suavemente
    dx = target_off_x - self._orbe._render_offset_x
    dy = target_off_y - self._orbe._render_offset_y
    dist = math.sqrt(dx * dx + dy * dy)
    
    if dist < 2.0:
        # Llegada — fijar offset final
        self._orbe._render_offset_x = target_off_x
        self._orbe._render_offset_y = target_off_y
        self._pos_objetivo = None
        return
    
    # Interpolación exponencial
    factor = min(1.0, self._velocidad_actual / max(dist, 1.0))
    self._orbe._render_offset_x += dx * factor
    self._orbe._render_offset_y += dy * factor
```

**Estado durante interpolación**: 
- `_render_offset_x/y` se actualiza cada frame
- Ventana permanece en mismo tamaño pero offset cambia suavemente

---

### 4. RENDER LAYER 1: paintEvent (ventana_principal.py, líneas 2102-2119)

```python
def paintEvent(self, event):
    painter = QPainter(self)
    # ... setup painter ...
    
    # Obtener center de rectángulo de ventana actual
    centro = self.rect().center()
    
    # ⚠️ PROBLEMA AQUÍ: Aplicar offset al center
    cx = centro.x() + int(self._render_offset_x)
    cy = centro.y() + int(self._render_offset_y)
    brillo = max(0.0, min(1.0, self._brillo_actual))
    
    # ... dibujos varios (glow, Dmut, colores) ...
```

**Cálculo de `cx, cy`**:
- `centro = self.rect().center()` → `(width/2, height/2)` en **coordenadas locales de ventana**
- Se aplica offset: `cx = centro.x() + offset_x`
- Resultado: `(width/2 + offset_x, height/2 + offset_y)`

**CORRECTITUD EN NORMAL**: Cuando `offset = 0`, `cx, cy` es el center = `(width/2, height/2)` ✅

**POTENCIAL BUG DURANTE TRÁNSITO**: Los anillos y geometría se dibujan con `cx, cy` desplazado... ¿pero qué pasa con AnimadorOrbe4D?

---

### 5. RENDER LAYER 2: AnimadorOrbe4D.renderizar() (animador_orbe_4d.py, líneas 195-227)

En `ventana_principal.py` línea 2263:

```python
self._animador.renderizar(
    painter,
    self.width(),      # ← Ancho ACTUAL ventana
    self.height(),     # ← Alto ACTUAL ventana
    draw_state=_draw_state,
    color_pri=color_primario,
    color_sec=color_secundario,
    brillo=brillo,
)
```

**Dentro AnimadorOrbe4D.renderizar()** (animador_orbe_4d.py, líneas 207-208):

```python
def renderizar(
    self,
    painter: QPainter,
    width: int,
    height: int,
    draw_state: Any = None,
    color_pri: 'QColor | None' = None,
    color_sec: 'QColor | None' = None,
    brillo: float = 0.5,
) -> None:
    """Renderiza el orbe 4D RUBEDO con 4 layers: Core + Spikes + Particles + Aura."""
    from computadora.interfaz.dibujante_orbe import (
        dibujar_nucleo,
        DrawState,
    )
    
    # ⚠️ RECALCULA CENTER INDEPENDIENTEMENTE
    cx, cy = width // 2, height // 2  # ← SIEMPRE CENTER DE VENTANA
    radio_viewport = min(width, height) * 0.45
    
    # Renderiza 4 layers con ESTE CENTER
    self._renderizar_aura(painter, cx, cy, radio_viewport)
    self._renderizar_spikes(painter, cx, cy)
    self._renderizar_core(painter, cx, cy)
    self._renderizar_particles(painter, cx, cy, radio_viewport)
```

---

## 🚨 LA RAÍZ DEL BUG

**DESCONEXIÓN DE COORDINATES:**

1. **En `paintEvent`** (ventana_principal.py, línea 2118):
   - `cx = self.rect().center().x() + int(self._render_offset_x)`
   - Aplica offset al center
   - Los anillos sagrados se dibujan en `(cx, cy)` desplazado ✅ (CORRECTO)

2. **En `AnimadorOrbe4D.renderizar()`** (animador_orbe_4d.py, línea 208):
   - `cx, cy = width // 2, height // 2`
   - **NO APLICA OFFSET**
   - Todos los elementos (núcleo, aura, spikes, partículas) se dibujan en center de ventana sin offset ❌ (INCORRECTO)

**Resultado**:
- Anillos sagrados: dibujados en `(center + offset)` → POSICIÓN CORRECTA
- Ferrofluido 4D (núcleo, aura, spikes): dibujado en `(center)` → POSICIÓN ERRÓNEA
- **Visualmente**: Anillos y ferrofluido aparecen offset entre sí

---

## 🔧 SOLUCIONES PROPUESTAS

### OPCIÓN A: Pasar `_render_offset` a AnimadorOrbe4D (RECOMENDADO)

**Ventaja**: Solución limpia, separación de responsabilidades clara  
**Cambios necesarios**:

1. Modificar firma `AnimadorOrbe4D.renderizar()`:
```python
def renderizar(
    self,
    painter: QPainter,
    width: int,
    height: int,
    offset_x: int = 0,  # ← NUEVO
    offset_y: int = 0,  # ← NUEVO
    draw_state: Any = None,
    color_pri: 'QColor | None' = None,
    color_sec: 'QColor | None' = None,
    brillo: float = 0.5,
) -> None:
```

2. Calcular center CON offset:
```python
cx = width // 2 + offset_x  # ← APLICAR OFFSET
cy = height // 2 + offset_y
```

3. En `ventana_principal.py` línea 2263, pasar offsets:
```python
self._animador.renderizar(
    painter,
    self.width(),
    self.height(),
    offset_x=int(self._render_offset_x),  # ← NUEVO
    offset_y=int(self._render_offset_y),  # ← NUEVO
    draw_state=_draw_state,
    color_pri=color_primario,
    color_sec=color_secundario,
    brillo=brillo,
)
```

**Archivos afectados**:
- [animador_orbe_4d.py](animador_orbe_4d.py#L195)
- [ventana_principal.py](ventana_principal.py#L2263)

---

### OPCIÓN B: Calcular `cx, cy` una sola vez en paintEvent, pasar a todos

**Ventaja**: Menos parámetros, una sola fuente de verdad  
**Desventaja**: Refactorización más grande (afecta otros dibujos)

```python
# Una sola vez al inicio de paintEvent
centro = self.rect().center()
cx = centro.x() + int(self._render_offset_x)
cy = centro.y() + int(self._render_offset_y)

# Pasar a TODOS los dibujos: anillos, animador, emet, etc.
self._animador.renderizar(painter, self.width(), self.height(), cx=cx, cy=cy, ...)
```

---

### OPCIÓN C: NO aplicar offset en paintEvent para AnimadorOrbe4D

**Desventaja**: Código confuso, offset se aplica selectivamente  
**NO RECOMENDADO**

---

## 📌 VERIFICACIÓN DE FIX

Una vez aplicada solución (OPCIÓN A recomendada):

```bash
# Test 1: Normal rendering (no movimiento)
# Esperado: Anillos y ferrofluido alineados al center ✅

# Test 2: Autonomous movement (esquive)
# Esperado: Mientras ventana se expande y orbe se interpola,
#          anillos y ferrofluido se mueven JUNTOS ✅

# Test 3: Collapse window
# Esperado: Al finalizar movimiento, anillos y ferrofluido
#          vuelven a center (offset → 0) ✅
```

---

## 🎯 LÍNEAS CRÍTICAS REFERENCIA

| Archivo | Línea | Descripción | Acción |
|---------|-------|-------------|--------|
| `vida_autonoma.py` | 1380 | Cálculo inicial `_render_offset` | VERIFICAR |
| `vida_autonoma.py` | 1330 | Interpolación `_render_offset` | VERIFICAR |
| `ventana_principal.py` | 2118-2119 | Aplicar offset a `cx, cy` | CORRECTO ✅ |
| `ventana_principal.py` | 2263 | Llamada a `_animador.renderizar()` | **MODIFICAR** ← FIX |
| `animador_orbe_4d.py` | 208 | Recalcular `cx, cy` SIN offset | **MODIFICAR** ← FIX |
| `animador_orbe_4d.py` | 218-227 | Usar `cx, cy` en 4 layers | AFECTADO por FIX |

---

## 🔐 IMPACTO DE SOLUCIÓN (OPCIÓN A)

**Riesgo**: 🟢 BAJO
- Cambios localizados a 2 archivos
- Parámetros son opcionales (default = 0)
- Backward compatible con código existente

**Beneficio**: 🟢 ALTO
- Soluciona desalieación visual
- Sincronización perfecta anillos ↔️ ferrofluido
- Base limpia para futuras animaciones

---

## SIGUIENTES PASOS

1. Aplicar FIX OPCIÓN A
2. Compilar y ejecutar `computadora_run.bat`
3. Ejecutar test autónomo: `python -m computadora`
4. Validar con movimiento manual: drag orbe a otra posición, luego deixar que regrese a hogar
5. Commit: `git add -A && git commit -m "FIX: Sincronizar offsets AnimadorOrbe4D durante tránsito autónomo"`

