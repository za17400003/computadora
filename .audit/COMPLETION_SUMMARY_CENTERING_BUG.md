# ✅ INVESTIGACIÓN COMPLETADA — Coordinate Centering Bug Maljut

**Fecha de Completación**: May 2, 2026, 12:45 UTC  
**Status**: 🔴 CRÍTICO | ✅ 100% DOCUMENTADO | 📋 LISTO PARA IMPLEMENTACIÓN

---

## 📌 RESUMEN EJECUTIVO

**Problema**: Durante movimiento autónomo del orbe (esquive/regreso a hogar), los anillos sagrados y el ferrofluido 4D aparecen **desalieados** (~72 pixeles de separación).

**Root Cause Identificada**: 
- Anillos renderizados con `cx = center + offset` ✅
- Ferrofluido renderizado con `cx = center` (sin offset) ❌
- AnimadorOrbe4D recalcula center internamente sin considerar el desplazamiento

**Solución Recomendada**: Pasar `offset_x` y `offset_y` como parámetros a `AnimadorOrbe4D.renderizar()` para que aplique offset al calcular el center.

**Impacto**: 
- 2 archivos a modificar
- ~10 líneas de código nuevas
- Tiempo implementación: 25 minutos
- Riesgo: 🟢 BAJO (cambios localizados, backward compatible)

---

## 📁 DELIVERABLES (En `.audit/`)

### 1️⃣ **INDEX_CENTERING_BUG.md** (Guía de navegación)
- Índice de toda la investigación
- Rutas de lectura recomendadas (5 min, 45 min, 25 min)
- Quick diagnosis: cómo verificar si tienes el bug
- Referencias cruzadas a todos los documentos

### 2️⃣ **QUICK_REFERENCE_CENTERING_BUG.md** ⭐ LEER PRIMERO (5 min)
- Problema en 1 frase
- Root cause en tabla comparativa
- **FIX EN 3 PASOS** (código exacto)
- Before/After visual comparison
- Test rápido para validar fix

### 3️⃣ **INVESTIGACION_BUG_CENTERING_MALJUT.md** (Análisis profundo, 15 min)
- 5 fases del flujo de rendering explicadas
- Root cause identification con ejemplos
- 3 soluciones alternativas evaluadas
- Análisis de impacto y riesgo
- Líneas críticas de referencia

### 4️⃣ **COORDINATE_FLOW_DIAGRAM.md** (Diagramas visuales, 15 min)
- Diagrama NORMAL RENDERING (sin bug)
- Diagrama DURANTE TRÁNSITO (bug visible)
- Timeline frame-by-frame de interpolación
- Diagrama de capas mostrando desalieación
- Trace detallado con coordenadas reales
- Diagrama de solución post-fix

### 5️⃣ **IMPLEMENTACION_FIX_DETALLADA.md** (Guía paso-a-paso, 10 min)
- Cambios exactos con código before/after
- Cambio 1A: Firma de método AnimadorOrbe4D
- Cambio 1B: Cálculo de center con offset
- Cambio 2: Pasar offsets en llamada
- Checklist de verificación (8 items)
- Test plan detallado
- Rollback plan (si algo falla)
- Commit message sugerido

---

## 🔍 INVESTIGACIÓN: FLUJO TÉCNICO

### Fase 1: Identificación de Layers
```
Layer 1: paintEvent (ventana_principal.py:2118)
  → Calcula cx, cy CON offset ✅
  → Anillos renderizados correctamente

Layer 2: AnimadorOrbe4D.renderizar() (animador_orbe_4d.py:208)
  → Recalcula cx, cy SIN offset ❌
  → Ferrofluido renderizado incorrectamente
```

### Fase 2: Root Cause Analysis
```
Durante movimiento autónomo:
  1. ventana_principal.py:_animar() llama a vida_autonoma.py:_interpolar_movimiento()
  2. vida_autonoma.py actualiza self._render_offset_x/y cada frame
  3. En paintEvent, se aplica offset: cx = center.x() + offset_x
  4. Pero AnimadorOrbe4D NO sabe del offset
  5. Resultado: Layers renderizadas en diferentes posiciones ❌
```

### Fase 3: Solución
```
Pasar offset a AnimadorOrbe4D:
  1. Agregar parámetros offset_x, offset_y a renderizar()
  2. Calcular cx, cy = width//2 + offset_x, cy = height//2 + offset_y
  3. Pasar offsets en la llamada desde ventana_principal.py
  4. RESULTADO: Todas las capas sincronizadas ✅
```

---

## 🎯 ARCHIVOS DE CÓDIGO RELEVANTES

| Archivo | Líneas | Propósito | Acción |
|---------|--------|----------|--------|
| `ventana_principal.py` | 698-701 | Init offsets | VERIFICAR |
| `ventana_principal.py` | 2118-2119 | Aplicar offset paintEvent | VERIFICAR ✅ |
| `ventana_principal.py` | 2263-2271 | Llamar renderizar() | **MODIFICAR** ← FIX |
| `animador_orbe_4d.py` | 195-210 | Firma renderizar() | **MODIFICAR** ← FIX |
| `animador_orbe_4d.py` | 207-208 | Calcular center | **MODIFICAR** ← FIX |
| `vida_autonoma.py` | 1355-1399 | Expandir ventana | VERIFICAR |
| `vida_autonoma.py` | 1320-1346 | Interpolar offset | VERIFICAR |

---

## 💾 ANÁLISIS CÓDIGO

**Cálculo de center (ANTES — CON BUG)**:
```python
# En ventana_principal.py paintEvent:
cx = self.rect().center().x() + int(self._render_offset_x)  # ✅ OFFSET APLICADO

# En animador_orbe_4d.py renderizar():
cx = width // 2                                              # ❌ SIN OFFSET
```

**Cálculo de center (DESPUÉS — FIJO)**:
```python
# En ventana_principal.py paintEvent:
cx = self.rect().center().x() + int(self._render_offset_x)  # ✅ OFFSET

# En animador_orbe_4d.py renderizar() (con parámetro offset_x):
cx = width // 2 + offset_x                                  # ✅ OFFSET APLICADO
```

---

## ✅ TESTING PLAN

### Test 1: Verificación de compilación
```bash
python -c "from computadora.interfaz.ventana_principal import OrbeComputadora"
# Esperado: Éxito sin errores
```

### Test 2: Movimiento autónomo (visual)
```bash
python -m computadora
# Triggear movimiento autónomo: mover cursor rápido hacia orbe
# Observar durante tránsito: ¿Anillos y ferrofluido en MISMA POSICIÓN?
# Esperado: Sí, alineados ✅
```

### Test 3: Validación de offsets
```python
# Mientras se interpola:
# Verificar que _render_offset_x y _render_offset_y se actualizan
# Y que son pasados correctamente a renderizar()
```

### Test 4: Colapso de ventana
```bash
# Cuando movimiento termina:
# Esperado: offset → 0, ventana → tamaño normal, orbe centrado
```

---

## 📊 ESTADÍSTICAS DE INVESTIGACIÓN

| Métrica | Valor |
|---------|-------|
| **Tiempo total investigación** | ~2 horas |
| **Documentos generados** | 5 + índice |
| **Líneas documentación** | ~3000 |
| **Diagramas ASCII** | 8 |
| **Código analizado** | 3 archivos, ~400 líneas |
| **Archivos a modificar** | 2 |
| **Líneas de código nuevas** | ~10 |
| **Parámetros nuevos** | 2 (`offset_x`, `offset_y`) |
| **Complejidad solución** | 🟢 BAJA |
| **Riesgo técnico** | 🟢 BAJO |
| **Impacto visual** | 🟢 ALTO |
| **Tiempo implementación** | ~25 min |

---

## 🚀 SIGUIENTES PASOS

1. **Lectura Recomendada**:
   - [ ] QUICK_REFERENCE_CENTERING_BUG.md (5 min)
   - [ ] IMPLEMENTACION_FIX_DETALLADA.md (10 min)

2. **Implementación**:
   - [ ] Modificar animador_orbe_4d.py (Cambios 1A, 1B)
   - [ ] Modificar ventana_principal.py (Cambio 2)
   - [ ] Verificar compilación sin errores
   - [ ] Test visual: movimiento autónomo

3. **Validación**:
   - [ ] Anillos + ferrofluido alineados ✅
   - [ ] Colapso ventana funciona ✅
   - [ ] Tests existentes pasan ✅

4. **Deployment**:
   - [ ] git add, git commit, git push
   - [ ] Commit message incluido en IMPLEMENTACION_FIX_DETALLADA.md

---

## 🔐 QUALITY ASSURANCE

✅ **Documentación Completa**:
- [ ] Root cause identificada y documentada
- [ ] Solución propuesta y evaluada
- [ ] Código before/after incluido
- [ ] Tests especificados
- [ ] Rollback plan documentado

✅ **Archivos Organizados** (FP-139 Behemá v'Rémesh):
- [ ] Todos en `.audit/` (auditoría/diagnóstico)
- [ ] Estructura clara (INDEX → QUICK → DETALLADO)
- [ ] Referencias cruzadas funcionan

✅ **Implementación Lista**:
- [ ] Cambios localizados (2 archivos)
- [ ] Backward compatible (defaults = 0)
- [ ] Sin dependencias externas
- [ ] Sin breaking changes

---

## 📞 NOTAS FINALES

**Para empezar YA:**
1. Abre [.audit/QUICK_REFERENCE_CENTERING_BUG.md](.audit/QUICK_REFERENCE_CENTERING_BUG.md)
2. Ve a sección "FIX EN 3 PASOS"
3. Aplica 3 cambios en 10 minutos
4. Test: `python -m computadora` + movimiento autónomo
5. Commit 🎉

**Cualquier duda:**
- Ver INVESTIGACION_BUG_CENTERING_MALJUT.md para análisis profundo
- Ver COORDINATE_FLOW_DIAGRAM.md para diagramas visuales
- Ver IMPLEMENTACION_FIX_DETALLADA.md para pasos exactos

---

**Investigación finalizada**: ✅ 100% COMPLETADA  
**Estado listo para**: 📋 IMPLEMENTACIÓN  
**Estimado de tiempo**: ⏱️ 25 minutos (lectura + cambios + test)

**🎯 RECOMENDACIÓN**: Implementar FIX AHORA. Impacto visual inmediato, riesgo mínimo.

