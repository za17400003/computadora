# 📑 INDEX — Coordinate Centering Bug Investigation

**Investigation Date**: May 2, 2026  
**Issue**: Anillos y ferrofluido desalieados durante movimiento autónomo  
**Status**: 🔴 CRÍTICO | ✅ DOCUMENTADO | 📋 LISTO PARA IMPLEMENTAR

---

## 📂 ARCHIVOS DE INVESTIGACIÓN

Todos los archivos están organizados según regla **Behemá v'Rémesh** (FP-139):
- **Auditoría** (`.audit/`): Diagnóstico y investigación ✅
- **Documentación** (`_docs/`): Guías operacionales 
- **Scripts** (`scripts/`): Herramientas

### En `.audit/` (Auditoría — Rémesh)

```
.audit/
├── INVESTIGACION_BUG_CENTERING_MALJUT.md
│   └─ Análisis técnico profundo (5 fases, diagrama flujo)
│      • Root cause identification
│      • Coordinate flow analysis
│      • 3 soluciones alternativas
│      • Impacto y verificación
│      Lectura: 15-20 min | Nivel: TÉCNICO
│
├── COORDINATE_FLOW_DIAGRAM.md
│   └─ Diagramas ASCII detallados (antes/después/timeline)
│      • Normal vs buggy rendering
│      • Timeline frame-by-frame
│      • Diagrama de capas
│      • Trace detallado de interpolación
│      Lectura: 10-15 min | Nivel: VISUAL
│
├── IMPLEMENTACION_FIX_DETALLADA.md
│   └─ Pasos ejecutables del fix (opción A recomendada)
│      • Cambio 1A: firma de método
│      • Cambio 1B: cálculo center
│      • Cambio 2: pasar offsets
│      • Checklist de implementación
│      • Tests y validación
│      Ejecución: 25 min total | Nivel: PRÁCTICO
│
├── QUICK_REFERENCE_CENTERING_BUG.md ← LEER PRIMERO
│   └─ Resumen ejecutivo (1 página, esencial)
│      • Problema en 1 frase
│      • Root cause en tabla
│      • 3 pasos del fix
│      • Before/after visual
│      Lectura: 5 min | Nivel: RESUMEN
│
└── INDEX.md (este archivo)
    └─ Guía de navegación de la investigación
```

---

## 🎯 RUTA DE LECTURA RECOMENDADA

### PARA ENTENDIMIENTO RÁPIDO (5 min)
1. Lee este INDEX.md
2. Lee QUICK_REFERENCE_CENTERING_BUG.md
3. Mira tabla de "FIX EN 3 PASOS" → ¡IMPLEMENTA!

### PARA ENTENDIMIENTO PROFUNDO (45 min)
1. QUICK_REFERENCE_CENTERING_BUG.md (5 min resumen)
2. INVESTIGACION_BUG_CENTERING_MALJUT.md (15 min análisis)
3. COORDINATE_FLOW_DIAGRAM.md (15 min diagramas)
4. IMPLEMENTACION_FIX_DETALLADA.md (10 min pasos)

### PARA IMPLEMENTACIÓN INMEDIATA (25 min)
1. QUICK_REFERENCE_CENTERING_BUG.md § "FIX EN 3 PASOS"
2. IMPLEMENTACION_FIX_DETALLADA.md § "ARCHIVO 1 & 2"
3. Ejecutar cambios
4. Test visual
5. Commit

---

## 📋 PROBLEM STATEMENT

```
USER REPORT:
  "cuando se mueve, los anillos y el ferrofluido se ponen en diferentes lugares"

TECHNICAL ANALYSIS:
  Anillos dibujados en:   (center + offset) ✅
  Ferrofluido dibujado en: (center)         ❌
  
  Separación visual: ~72 pixeles
  Root cause: AnimadorOrbe4D recalcula center SIN considerar offset

SOLUTION:
  Pasar offset_x, offset_y como parámetros a AnimadorOrbe4D.renderizar()
  
  Cambios:
  - animador_orbe_4d.py:    +5 líneas
  - ventana_principal.py:   +2 líneas
  
  Tiempo implementación: 25 minutos
  Riesgo:               🟢 BAJO
  Impacto visual:       🟢 ALTO
```

---

## 🔍 QUICK DIAGNOSIS

**Para verificar que TIENES el bug:**

```python
# Durante movimiento autónomo (esquive o regreso a hogar):
# ¿Los anillos sagrados aparecen en diferente lugar que el ferrofluido?
# Distancia entre capas: > 30 pixeles?

YES → Tienes el bug ❌
NO  → Ya está fijo ✅
```

**Root cause confirmado porque:**
1. ✅ Anillos se dibujan con offset (ventana_principal.py:2118)
2. ✅ AnimadorOrbe4D no aplica offset (animador_orbe_4d.py:208)
3. ✅ Desalieación ocurre SOLO durante tránsito (cuando offset ≠ 0)
4. ✅ No ocurre en rendering normal (offset = 0)

---

## 📊 INVESTIGATION METRICS

| Métrica | Valor |
|---------|-------|
| **Archivos investigados** | 3 |
| **Líneas de código analizadas** | ~400 |
| **Root causes identificadas** | 1 (AnimadorOrbe4D sin offset) |
| **Soluciones propuestas** | 3 (OPCIÓN A recomendada) |
| **Documentación generada** | 5 archivos, ~2000 líneas |
| **Diagramas incluidos** | 8 (ASCII + tablillas) |
| **Tiempo investigación** | ~2 horas |
| **Tiempo implementación** | ~25 minutos |

---

## 🎯 SUCCESS CRITERIA (Verificación)

Después de implementar el fix:

```
[ ] Compilación sin errores
[ ] Anillos + ferrofluido alineados durante tránsito
[ ] Distancia visual entre capas < 2px (invisible)
[ ] Colapso de ventana funciona (offset reset)
[ ] Rendering normal (no tránsito) sin cambios
[ ] Tests existentes pasan
[ ] Backward compatible ✅
```

---

## 🔐 ARCHIVOS A MODIFICAR

```
✅ animador_orbe_4d.py
   L 195: agregar offset_x, offset_y parámetros
   L 208: cx = width//2 + offset_x; cy = height//2 + offset_y

✅ ventana_principal.py
   L 2263: pasar offset_x=int(self._render_offset_x)
           pasar offset_y=int(self._render_offset_y)
```

**Archivos NO modifican:**
```
❌ vida_autonoma.py     (solo lectura — verificar offsets)
❌ dibujante_orbe.py    (solo lectura — anillos ok)
❌ ferrofluido_rubedo.py (solo lectura — particles ok)
```

---

## 📞 REFERENCES & LINKS

### Documentación Generada
- [QUICK_REFERENCE_CENTERING_BUG.md](QUICK_REFERENCE_CENTERING_BUG.md) — Resumen 1-pager
- [INVESTIGACION_BUG_CENTERING_MALJUT.md](INVESTIGACION_BUG_CENTERING_MALJUT.md) — Análisis completo
- [COORDINATE_FLOW_DIAGRAM.md](COORDINATE_FLOW_DIAGRAM.md) — Diagramas flujo
- [IMPLEMENTACION_FIX_DETALLADA.md](IMPLEMENTACION_FIX_DETALLADA.md) — Pasos implementación

### Código Relevante
- [ventana_principal.py#L698-L701](ventana_principal.py#L698-L701) — Inicialización offset
- [ventana_principal.py#L2118-L2119](ventana_principal.py#L2118-L2119) — Aplicar offset paintEvent
- [ventana_principal.py#L2263-L2271](ventana_principal.py#L2263-L2271) — Llamada a renderizar ← MODIFICAR
- [animador_orbe_4d.py#L195-L210](animador_orbe_4d.py#L195-L210) — Firma método ← MODIFICAR
- [animador_orbe_4d.py#L207-L208](animador_orbe_4d.py#L207-L208) — Cálculo center ← MODIFICAR
- [vida_autonoma.py#L1355-L1399](vida_autonoma.py#L1355-L1399) — Expansión ventana
- [vida_autonoma.py#L1320-L1346](vida_autonoma.py#L1320-L1346) — Interpolación offset

---

## 🚀 QUICK START

**Para implementar ahora:**

1. Abre [QUICK_REFERENCE_CENTERING_BUG.md](QUICK_REFERENCE_CENTERING_BUG.md)
2. Salta a sección "FIX EN 3 PASOS"
3. Aplica 3 cambios
4. Test: `python -m computadora`
5. Triggear movimiento autónomo
6. Verificar anillos + ferrofluido alineados ✅

---

## 🔄 HISTORIAL DE INVESTIGACIÓN

```
2026-05-02 11:00 — Inicio investigación (reporte de usuario)
2026-05-02 11:15 — Identificación de flujo rendering
2026-05-02 11:30 — Root cause confirmada (AnimadorOrbe4D sin offset)
2026-05-02 11:45 — Diagramas de flujo coordinate creados
2026-05-02 12:00 — 3 soluciones propuestas
2026-05-02 12:15 — OPCIÓN A seleccionada (pasar offset)
2026-05-02 12:30 — Documentación completa generada
2026-05-02 12:45 — Ready para implementación ✅
```

---

## 📝 NOTES

- Toda la documentación está en `.audit/` (correcto según Behemá v'Rémesh FP-139)
- Cambios son backward-compatible (defaults = 0)
- No hay riesgo técnico (cambios localizados y simples)
- Impacto visual será inmediato (sincronización perfecta)
- Commit message incluido en IMPLEMENTACION_FIX_DETALLADA.md

---

**NEXT STEP**: Lee [QUICK_REFERENCE_CENTERING_BUG.md](QUICK_REFERENCE_CENTERING_BUG.md) y ¡IMPLEMENTA! ⚡

