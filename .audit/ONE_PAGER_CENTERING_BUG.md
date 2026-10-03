# 🎯 ONE-PAGER: Coordinate Centering Bug Fix

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    MALJUT ORB RENDERING ALIGNMENT BUG                      ║
║                         Status: DIAGNOSED & READY                           ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## 🚨 THE PROBLEM

```
VISUAL:                     TECHNICAL:
Expected:   Actual (BUG):   Layer 1 (Rings):     cx = center + offset ✅
  ●─●         ●─●          Layer 2 (Ferrofluido): cx = center ❌
  │◆│   →    │  │          
  ●─●        │◆ │          RESULT: 72px separation ❌
             ●  ●
```

**User Report**: "cuando se mueve, los anillos y el ferrofluido se ponen en diferentes lugares"

---

## 🔍 ROOT CAUSE

| Component | File | Line | Center Calc | With Offset? |
|-----------|------|------|-------------|--------------|
| **Rings** | ventana_principal.py | 2118 | `rect().center() + offset` | ✅ YES |
| **Ferrofluido** | animador_orbe_4d.py | 208 | `width // 2` | ❌ NO |

**Problem**: AnimadorOrbe4D doesn't know about the offset during autonomous movement.

---

## 🛠️ FIX IN 3 STEPS (10 minutes)

### STEP 1: animador_orbe_4d.py (Line 195)

```python
# ADD offset parameters to method signature
def renderizar(
    self, painter, width, height,
    offset_x: int = 0,      # ← NEW
    offset_y: int = 0,      # ← NEW
    draw_state=None, ...
):
```

### STEP 2: animador_orbe_4d.py (Line 208)

```python
# APPLY offset to center calculation
cx = width // 2 + offset_x    # ← CHANGED
cy = height // 2 + offset_y   # ← CHANGED
```

### STEP 3: ventana_principal.py (Line 2263)

```python
# PASS offsets to renderizar() call
self._animador.renderizar(
    painter, self.width(), self.height(),
    offset_x=int(self._render_offset_x),     # ← NEW
    offset_y=int(self._render_offset_y),     # ← NEW
    draw_state=_draw_state,
    color_pri=color_primario,
    ...
)
```

---

## ✅ BEFORE & AFTER

### BEFORE (❌ BUG)
```
During transit: _render_offset_x = -60, _render_offset_y = -40

Rings:       cx = 200 + (-60) = 140  ✅ CORRECT
Ferrofluido: cx = 200 + 0 = 200      ❌ WRONG
             
VISUAL SEPARATION: √(60² + 40²) ≈ 72px ❌
```

### AFTER (✅ FIXED)
```
During transit: _render_offset_x = -60, _render_offset_y = -40

Rings:       cx = 200 + (-60) = 140  ✅
Ferrofluido: cx = 200 + (-60) = 140  ✅ NOW SAME

VISUAL SEPARATION: 0px ✅ PERFECT ALIGNMENT
```

---

## 🧪 QUICK TEST

```bash
# 1. Implement 3 steps above

# 2. Run
python -m computadora

# 3. Trigger autonomous movement
#    (move cursor quickly toward orb to trigger dodge)

# 4. Observe during movement:
#    Do rings and ferrofluido move TOGETHER? 
#    YES ✅ → FIX WORKING
#    NO  ❌ → Something wrong
```

---

## 📊 IMPACT

| Metric | Value |
|--------|-------|
| Files to modify | 2 |
| New lines of code | ~10 |
| Backward compatible | ✅ YES |
| Risk level | 🟢 LOW |
| Time to implement | ⏱️ 25 min |
| Visual improvement | 🟢 HIGH |

---

## 📁 DOCUMENTATION

All investigation files in `.audit/`:

| File | Purpose | Read Time |
|------|---------|-----------|
| **INDEX_CENTERING_BUG.md** | Navigation guide | 5 min |
| **QUICK_REFERENCE_CENTERING_BUG.md** | This but longer | 5 min |
| **INVESTIGACION_BUG_CENTERING_MALJUT.md** | Deep technical analysis | 15 min |
| **COORDINATE_FLOW_DIAGRAM.md** | Visual diagrams | 15 min |
| **IMPLEMENTACION_FIX_DETALLADA.md** | Detailed implementation steps | 10 min |

---

## 🎯 SUCCESS CRITERIA

```
After implementing the 3 steps:

✅ Compilation without errors
✅ Rings + ferrofluido stay aligned during transit
✅ Visual separation < 2px (invisible)
✅ Window collapse works (offset → 0)
✅ Backward compatible behavior
✅ Existing tests pass
```

---

## 🚀 START HERE

**Fast Track (15 min total)**:
1. Read QUICK_REFERENCE_CENTERING_BUG.md
2. Implement 3 steps above
3. Test with autonomous movement

**Thorough (60 min total)**:
1. Start with INDEX_CENTERING_BUG.md
2. Read all investigation files
3. Implement with full understanding

---

## 📞 QUICK ANSWERS

**Q: Does this affect normal rendering?**  
A: NO. When no movement, offset = 0, behavior identical.

**Q: Will existing code break?**  
A: NO. New parameters have defaults = 0, fully backward compatible.

**Q: Why NOW?**  
A: Autonomous movement is fundamental feature. Misalignment visible to users. Fix is trivial, impact is high.

---

## 🔐 NEXT STEP

👉 **Open**: `.audit/QUICK_REFERENCE_CENTERING_BUG.md`  
👉 **Find**: "FIX EN 3 PASOS" section  
👉 **Implement**: 3 code changes  
👉 **Test**: `python -m computadora` + autonomous movement  
👉 **Commit**: Use provided message  

**⏱️ Total Time**: ~25 minutes  
**📊 Payoff**: Perfect visual synchronization  

---

```
╔════════════════════════════════════════════════════════════════════════════╗
║  Investigation Status: ✅ 100% COMPLETE | Code Changes: 🟢 READY           ║
║  Estimated Time: 25 minutes | Risk: 🟢 LOW | Impact: 🟢 HIGH              ║
╚════════════════════════════════════════════════════════════════════════════╝
```

