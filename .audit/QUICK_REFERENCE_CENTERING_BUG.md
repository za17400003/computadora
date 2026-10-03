# 📌 QUICK REFERENCE — Coordinate Centering Bug Summary

**Status**: 🔴 IDENTIFICADO, DOCUMENTADO, LISTO PARA IMPLEMENTACIÓN  
**Date**: May 2, 2026  
**Severity**: 🔴 CRÍTICO (Desconexión visual durante movimiento autónomo)

---

## 🎯 EL BUG EN UNA FRASE

> Anillos sagrados renderizados con offset correcto, ferrofluido 4D renderizado sin offset → **desalieación de 72px** durante tránsito autónomo

---

## 🔴 SÍNTOMA VISUAL

```
ESPERADO:           ACTUAL (BUG):
  ●────●              ●────●
  │    │     X         │    │
  │ ◆  │     →         │    ◆
  │    │              •  •  •
  ●────●              •  •  •
  
Anillos + Ferrofluido    Separados ~72px
siempre en mismo lugar
```

---

## 🔍 ROOT CAUSE

| Layer | Cálculo Center | Aplica Offset? | Archivo | Línea |
|-------|-----------------|----------------|---------|-------|
| **Anillos** | `self.rect().center() + offset` | ✅ SÍ | ventana_principal.py | 2118 |
| **Ferrofluido** | `width // 2` | ❌ NO | animador_orbe_4d.py | 208 |

---

## 🛠️ FIX EN 3 PASOS

### PASO 1: Modificar animador_orbe_4d.py (línea 195)

```diff
  def renderizar(
      self,
      painter: QPainter,
      width: int,
      height: int,
+     offset_x: int = 0,
+     offset_y: int = 0,
      draw_state: Any = None,
```

### PASO 2: Actualizar cálculo center en animador_orbe_4d.py (línea 208)

```diff
- cx, cy = width // 2, height // 2
+ cx = width // 2 + offset_x
+ cy = height // 2 + offset_y
```

### PASO 3: Pasar offsets en ventana_principal.py (línea 2263)

```diff
  self._animador.renderizar(
      painter,
      self.width(),
      self.height(),
+     offset_x=int(self._render_offset_x),
+     offset_y=int(self._render_offset_y),
      draw_state=_draw_state,
```

---

## ✅ ANTES & DESPUÉS

### ANTES (❌ BUG)

```
FRAME durante tránsito:
  _render_offset_x = -60
  _render_offset_y = -40

Rendering:
  ✅ Anillos:      cx = 200 + (-60) = 140
  ❌ Ferrofluido:  cx = 200 + 0 = 200
  
  RESULTADO: Anillos en (140,110), Ferrofluido en (200,150)
             Distancia visual: sqrt(60² + 40²) ≈ 72px
```

### DESPUÉS (✅ FIX)

```
FRAME durante tránsito:
  _render_offset_x = -60
  _render_offset_y = -40

Rendering:
  ✅ Anillos:      cx = 200 + (-60) = 140
  ✅ Ferrofluido:  cx = 200 + (-60) = 140  ← AHORA CON OFFSET
  
  RESULTADO: Anillos en (140,110), Ferrofluido en (140,110)
             ALINEACIÓN PERFECTA ✅
```

---

## 📊 IMPACT ANALYSIS

| Métrica | Value |
|---------|-------|
| Archivos afectados | 2 |
| Líneas de código nuevas | ~10 |
| Parámetros nuevos | 2 (`offset_x`, `offset_y`) |
| Backward compatible | ✅ SÍ (defaults = 0) |
| Riesgo técnico | 🟢 BAJO |
| Complejidad implementación | 🟢 TRIVIAL |
| Impacto visual | 🟢 ALTO (fix es crítico) |

---

## 🔍 INVESTIGACIÓN COMPLETA

Documentos generados en `.audit/`:

1. **INVESTIGACION_BUG_CENTERING_MALJUT.md**
   - Análisis detallado del flujo de rendering
   - 5 fases del problema
   - 2 soluciones alternativas
   - Impacto y verificación

2. **COORDINATE_FLOW_DIAGRAM.md**
   - Diagramas ASCII de flujo
   - Timeline de estados
   - Trace detallado de interpolación
   - Diagrama de capas durante tránsito

3. **IMPLEMENTACION_FIX_DETALLADA.md**
   - Pasos exactos del fix
   - Código before/after
   - Checklist de verificación
   - Test plan completo
   - Rollback plan

---

## 🧪 TEST RÁPIDO

```powershell
# 1. Compilar
python -c "from computadora.interfaz import ventana_principal"

# 2. Ejecutar
python -m computadora

# 3. Triggear movimiento autónomo:
#    - Mover cursor rápido hacia orbe (esquive)
#    - Esperar regreso a hogar
#    - Observar que ANILLOS Y FERROFLUIDO SE MUEVEN JUNTOS ✅

# 4. Verificación visual:
#    - Mientras se interpola, ¿anillos y ferrofluido están
#      en la MISMA POSICIÓN? (distancia < 2px)
#    - Si SÍ → FIX FUNCIONANDO ✅
```

---

## 📍 COORDENADAS CRÍTICAS

```python
# Variable principal
self._render_offset_x = 0.0  # ventana_principal.py:698
self._render_offset_y = 0.0  # ventana_principal.py:699

# Se actualiza en movimiento autónomo
vida_autonoma.py:1383-1388   # _expandir_ventana_transito()
vida_autonoma.py:1330-1346   # _interpolar_movimiento() cada frame

# Se renderiza en:
ventana_principal.py:2118    # paintEvent() — ANILLOS (correcto)
animador_orbe_4d.py:208      # renderizar() — FERROFLUIDO (incorrecto)

# FIX: pasar offset a AnimadorOrbe4D
ventana_principal.py:2263    # Modificar llamada a renderizar()
animador_orbe_4d.py:195      # Modificar firma de método
animador_orbe_4d.py:208      # Modificar cálculo de center
```

---

## ⏱️ TIMELINE ESTIMADO

| Fase | Tiempo | Descripción |
|------|--------|-------------|
| Lectura documentación | 5-10 min | Leer los 3 archivos .audit/ |
| Implementación | 5 min | Cambios en 2 archivos, 10 líneas |
| Testing | 5 min | Compilar y ejecutar test visual |
| Validación | 5 min | Verificar movimiento autónomo |
| Commit | 2 min | git add/commit/push |
| **TOTAL** | **~25 min** | Listo para producción |

---

## 🎯 SUCCESS CRITERIA

- [ ] Anillos y ferrofluido permanecen alineados durante tránsito
- [ ] Distancia visual entre capas < 2px (sub-pixel, invisible)
- [ ] Colapso de ventana funciona (offset → 0)
- [ ] Compilación sin warnings
- [ ] Tests existentes pasan
- [ ] Backward compatible

---

## 📞 PREGUNTAS FRECUENTES

**P: ¿Esto afecta a rendering normal (sin movimiento)?**  
R: NO. Cuando no hay tránsito, `offset = 0`, comportamiento idéntico.

**P: ¿Hay que cambiar AnimadorOrbe4D.\_renderizar\_core/aura/spikes?**  
R: NO. Todos usan el mismo `cx, cy`, se propagan automáticamente.

**P: ¿Y si hay múltiples orbes?**  
R: NO aplicable. Proyecto tiene solo 1 orbe (Maljut).

**P: ¿Afecta a performance?**  
R: NO. Una suma `int + int` es O(1), <1ns overhead.

**P: ¿Qué pasa si el offset es enorme?**  
R: El offset está limitado (clamped) en vida_autonoma.py:1387-1388.

---

## 🔐 VERIFICACIÓN PRE-COMMIT

```bash
# Antes de hacer git commit:

# 1. Verificar que compilar sin errores
python -c "from computadora.interfaz.ventana_principal import OrbeComputadora; print('✅')"

# 2. Verificar que no hay imports rotos
python -m py_compile computadora/interfaz/animador_orbe_4d.py
python -m py_compile computadora/interfaz/ventana_principal.py

# 3. Verificar lineas modificadas
git diff computadora/interfaz/animador_orbe_4d.py
git diff computadora/interfaz/ventana_principal.py

# 4. Verificar que no hay código muerto
# (nunca debería haber líneas con offset_x/y antes del fix)
```

---

## 🚀 IMPLEMENTAR AHORA

Ver `.audit/IMPLEMENTACION_FIX_DETALLADA.md` para pasos exactos.

Tiempo estimado: **25 minutos** desde lectura hasta merged.

