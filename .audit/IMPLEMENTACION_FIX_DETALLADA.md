# 🛠️ IMPLEMENTACIÓN DEL FIX — Coordinate Centering Bug

**Propuesta**: OPCIÓN A — Pasar `_render_offset` a AnimadorOrbe4D  
**Archivos a modificar**: 2  
**Líneas afectadas**: ~10 líneas de código real  
**Complejidad**: BAJA  
**Riesgo**: MÍNIMO (cambios backward-compatible)

---

## ARCHIVO 1: animador_orbe_4d.py

**Línea objetivo**: 195-210 (firma de `renderizar()`)

### CAMBIO 1A: Actualizar firma de método

**ANTES:**
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
```

**DESPUÉS:**
```python
def renderizar(
    self,
    painter: QPainter,
    width: int,
    height: int,
    offset_x: int = 0,                    # ← NUEVO PARÁMETRO
    offset_y: int = 0,                    # ← NUEVO PARÁMETRO
    draw_state: Any = None,
    color_pri: 'QColor | None' = None,
    color_sec: 'QColor | None' = None,
    brillo: float = 0.5,
) -> None:
```

### CAMBIO 1B: Calcular center CON offset

**UBICACIÓN**: Línea ~207-208

**ANTES:**
```python
cx, cy = width // 2, height // 2
radio_viewport = min(width, height) * 0.45
```

**DESPUÉS:**
```python
cx = width // 2 + offset_x            # ← APLICAR OFFSET
cy = height // 2 + offset_y           # ← APLICAR OFFSET
radio_viewport = min(width, height) * 0.45
```

**JUSTIFICACIÓN**:
- El `offset_x` y `offset_y` representan el desplazamiento del orbe respecto al center de la ventana
- Durante movimiento autónomo, la ventana se expande pero el orbe se dibuja desplazado
- AnimadorOrbe4D necesita saber este desplazamiento para renderizar todas las capas en el mismo lugar

---

## ARCHIVO 2: ventana_principal.py

**Línea objetivo**: 2263-2271 (llamada a `self._animador.renderizar()`)

### CAMBIO 2: Pasar offsets a renderizar()

**ANTES:**
```python
        # use dibujante_orbe.dibujar_nucleo() como base, evitando duplicación visual.
        # FP-155: Usar _draw_state cacheado (evita copias redundantes de partículas)
        if self._estado not in ("dormido", "descanso_guardian", "tzimtzum", "apagado"):
            self._animador.renderizar(
                painter,
                self.width(),
                self.height(),
                draw_state=_draw_state,
                color_pri=color_primario,
                color_sec=color_secundario,
                brillo=brillo,
            )
```

**DESPUÉS:**
```python
        # use dibujante_orbe.dibujar_nucleo() como base, evitando duplicación visual.
        # FP-155: Usar _draw_state cacheado (evita copias redundantes de partículas)
        if self._estado not in ("dormido", "descanso_guardian", "tzimtzum", "apagado"):
            self._animador.renderizar(
                painter,
                self.width(),
                self.height(),
                offset_x=int(self._render_offset_x),  # ← NUEVO PARÁMETRO
                offset_y=int(self._render_offset_y),  # ← NUEVO PARÁMETRO
                draw_state=_draw_state,
                color_pri=color_primario,
                color_sec=color_secundario,
                brillo=brillo,
            )
```

**JUSTIFICACIÓN**:
- Los offsets `_render_offset_x` y `_render_offset_y` se actualizan en `vida_autonoma.py` durante interpolación
- Necesitan ser comunicados a AnimadorOrbe4D CADA FRAME para mantener sincronización
- Se convierte a `int` porque AnimadorOrbe4D usa coordenadas de píxeles enteros

---

## VERIFICACIÓN DE CAMBIOS

### Test 1: Compilación sin errores

```powershell
# En PowerShell, en raíz del proyecto
python -c "from computadora.interfaz.animador_orbe_4d import AnimadorOrbe4D; print('✅ Import OK')"
python -c "from computadora.interfaz.ventana_principal import OrbeComputadora; print('✅ Import OK')"
```

### Test 2: Backward compatibility

El cambio es 100% backward-compatible porque:
- Los nuevos parámetros `offset_x` y `offset_y` tienen defaults = 0
- Cualquier código que llame sin estos parámetros sigue funcionando
- Solo el renderizado se verá mejorado

```python
# Esto SIGUE funcionando (offset = 0 = comportamiento anterior)
animator.renderizar(painter, width, height, color_pri=color, ...)

# Esto TAMBIÉN funciona (con offsets)
animator.renderizar(
    painter, width, height,
    offset_x=50, offset_y=30,  # Nuevos parámetros
    color_pri=color, ...
)
```

### Test 3: Movimiento autónomo visual

**Pasos**:

1. Arrancar aplicación:
```powershell
python -m computadora
```

2. Invocar movimiento autónomo (esquive):
   - Mover cursor rápidamente hacia el orbe
   - El orbe debería esquivar
   - Durante esquive: observar que **anillos y ferrofluido se mueven JUNTOS**

3. Solicitar regreso a hogar:
   - Esperar unos segundos o ejecutar comando
   - El orbe debería volver a posición original
   - Durante tránsito de regreso: observar que **anillos y ferrofluido siguen alineados**

4. Verificar en fin de tránsito:
   - Window debería colapsar a tamaño normal (220×220)
   - Offset debería ser 0
   - Orbe debería estar centrado

---

## VALIDACIÓN COMPLETA

Para validar exhaustivamente que el fix funciona:

### A. Modo debug (con logging)

Editar temporalmente `vida_autonoma.py` línea ~1330 para agregar:

```python
def _interpolar_movimiento(self):
    # ... existing code ...
    
    if not self._orbe._en_transito:
        self._expandir_ventana_transito()
        logger.debug(f"🚀 TRÁNSITO INICIADO: offset=({self._orbe._render_offset_x:.1f}, {self._orbe._render_offset_y:.1f})")
    
    # ... existing code ...
    
    # Interpolar
    self._orbe._render_offset_x += dx * factor
    self._orbe._render_offset_y += dy * factor
    
    # ← AGREGAR DEBUG LOG
    if dist > 2.0:
        logger.debug(f"📍 INTERPOLANDO: offset=({self._orbe._render_offset_x:.1f}, {self._orbe._render_offset_y:.1f}) dist={dist:.1f}")
```

Luego en `ventana_principal.py` línea ~2263, agregar:

```python
if self._estado not in ("dormido", "descanso_guardian", "tzimtzum", "apagado"):
    # ← AGREGAR DEBUG LOG
    if self._en_transito and (int(self._render_offset_x) != 0 or int(self._render_offset_y) != 0):
        logger.debug(f"🎨 PAINTVENT: cx={cx}, cy={cy}, offset=({int(self._render_offset_x)}, {int(self._render_offset_y)})")
    
    self._animador.renderizar(
        painter,
        self.width(),
        self.height(),
        offset_x=int(self._render_offset_x),
        offset_y=int(self._render_offset_y),
        draw_state=_draw_state,
        color_pri=color_primario,
        color_sec=color_secundario,
        brillo=brillo,
    )
```

Ejecutar y observar logs durante movimiento autónomo:

```
Expected output:
🚀 TRÁNSITO INICIADO: offset=(-60.0, -40.0)
📍 INTERPOLANDO: offset=(-55.2, -36.8) dist=71.4
📍 INTERPOLANDO: offset=(-50.4, -33.6) dist=62.1
...
📍 INTERPOLANDO: offset=(-2.1, -1.4) dist=2.3
🎨 PAINTVENT: cx=198, cy=149, offset=(-2, -1)
```

### B. Test visual

Instalar herramienta de color para validar píxeles (opcional):

```powershell
# Tomar screenshot durante tránsito
# Usar ImageMagick o similar para verificar que:
# 1. Anillos están en posición (cx, cy)
# 2. Ferrofluido núcleo está en MISMA posición
# 3. NO hay offset entre capas
```

### C. Test de colapso

Verificar que al finalizar movimiento:

```python
# En vida_autonoma.py _colapsar_ventana_transito()

# ANTES de reset offset:
# - Ventana tamaño expandido
# - Offset ≠ 0

# DESPUÉS de reset offset:
# - Ventana tamaño normal (220×220)
# - Offset = 0 exactamente
# - Orbe centrado en pantalla
```

---

## CHECKLIST DE IMPLEMENTACIÓN

- [ ] Leer esta documentación completa
- [ ] Revisar archivos [animador_orbe_4d.py](animador_orbe_4d.py#L195) y [ventana_principal.py](ventana_principal.py#L2263)
- [ ] Realizar CAMBIO 1A (firma de método)
- [ ] Realizar CAMBIO 1B (calcular center con offset)
- [ ] Realizar CAMBIO 2 (pasar offsets en llamada)
- [ ] Verificar compilación: `python -c "import computadora.interfaz.ventana_principal"`
- [ ] Ejecutar test visual: `python -m computadora`
- [ ] Triggerar movimiento autónomo y observar
- [ ] Validar anillos + ferrofluido alineados
- [ ] Revisar logs si fue usado modo debug
- [ ] Commit con mensaje: `FIX: Sincronizar offsets AnimadorOrbe4D durante tránsito autónomo (WI-XXX)`
- [ ] Cerrar issue/WorkItem

---

## ROLLBACK PLAN (si algo falla)

Si después de cambios algo se rompe:

```powershell
# Revertir cambios
git checkout computadora/interfaz/animador_orbe_4d.py
git checkout computadora/interfaz/ventana_principal.py

# Verificar que vuelva a funcionar
python -m computadora
```

---

## NOTAS TÉCNICAS

1. **¿Por qué `int()` en ventana_principal.py?**
   - `_render_offset_x/y` son `float` (suavidad de interpolación)
   - AnimadorOrbe4D usa coordenadas de píxel (enteros)
   - `int()` redondea al píxel más cercano sin pérdida visual

2. **¿Por qué default = 0?**
   - Cuando NO hay movimiento: offset = 0 (comportamiento previo)
   - Backward compatible: código existente no se rompe

3. **¿Afecta a performance?**
   - NO: Una suma `int + int` es O(1)
   - El overhead es negligible (<1ns per pixel)

4. **¿Qué pasa con otras geometrías?**
   - Spikes, aura, core, particles: TODAS se renderizan con mismo `cx, cy`
   - El fix afecta TODAS las capas uniformemente
   - NO hay capas individuales con offset diferente

5. **¿Futuro mantenimiento?**
   - Si se agrega nueva capa de renderizado en AnimadorOrbe4D
   - AUTOMÁTICAMENTE usará el `cx, cy` correcto (con offset)
   - NO se necesitarán cambios adicionales

---

## COMMIT MESSAGE

```
FIX: Sincronizar offsets AnimadorOrbe4D durante tránsito autónomo

PROBLEMA:
- Durante movimiento autónomo (esquive/regreso a hogar), la ventana se expande
- Los anillos sagrados se renderizan con offset calculado correctamente
- Pero AnimadorOrbe4D (ferrofluido 4D) recalculaba center SIN offset
- Resultado visual: anillos y ferrofluido aparecían separados (~72px)

SOLUCIÓN:
- Pasar offset_x, offset_y como parámetros a AnimadorOrbe4D.renderizar()
- AnimadorOrbe4D aplica offset al calcular cx, cy
- Todas las capas (núcleo, aura, spikes, partículas) se renderizan alineadas

CAMBIOS:
- animador_orbe_4d.py: Agregar offset_x, offset_y parámetros
- ventana_principal.py: Pasar self._render_offset_x/y a renderizar()

VALIDACIÓN:
- Movimiento autónomo: anillos y ferrofluido alineados ✅
- Colapso ventana: offset reset a 0, orbe centrado ✅
- Backward compatible: defaults = 0 ✅

REFERENCIA:
- Investigación: .audit/INVESTIGACION_BUG_CENTERING_MALJUT.md
- Diagrama: .audit/COORDINATE_FLOW_DIAGRAM.md
```

