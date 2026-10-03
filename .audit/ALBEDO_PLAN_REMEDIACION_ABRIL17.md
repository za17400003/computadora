# 📋 ALBEDO — Plan de Remediación (Investigación + Especificación)

**Status**: ✅ ESPECIFICACIÓN LISTA PARA RUBEDO

---

## CATEGORIZACIÓN DE REFERENCIAS A "GRIMORIO"

### 1. ✅ ACEPTABLES (Contexto Esotérico)
Estos archivos PUEDEN usar "Grimorio" porque es referencia **histórica/conceptual**:
- `ENCICLOPEDIA/*.html` (cap01-cap16) — Contenido de la Enciclopedia de los 7 Metales (esotérico)
- `ENCICLOPEDIA/biblioteca_sendero.json` — Datos sobre etapas alquímicas
- `computadora/cerebro/hechizos_hp.py` — Harry Potter metaphors (OK)
- `.gitattributes` — Comentarios sobre estructura
- `computadora/arquitectura/dimensiones.py:55, 155-452, 717` — `capitulo_grimorio` field (mapeo a capítulos ENCICLOPEDIA, OK)

**NO REQUIEREN CAMBIO**

### 2. 🔴 CRÍTICOS (Deben repararse ANTES de RUBEDO)

#### A. Boot Script Path — MUST FIX
| Archivo | Línea | Problema | Fix | Impacto |
|---------|-------|----------|-----|---------|
| `computadora/__main__.py` | 277 | `from computadora.canales.grimorio_guardian import GrimorioGuardian` | Renombrar a `enciclopedia_guardian` | Boot fallará si módulo no existe |
| `computadora/arquitectura/dimensiones.py` | 90 | `_M_GRIMORIO_GUARDIAN = "grimorio_guardian"` | Cambiar a `_M_ENCICLOPEDIA_GUARDIAN = "enciclopedia_guardian"` | Mapeo roto |

#### B. Archivos/Directorio Obsoletos — MUST DELETE
| Path | Tipo | Razón | Action |
|------|------|-------|--------|
| `ENCICLOPEDIA/servidor_grimorio.py` | Archivo | Versión antigua (duplicado de servidor_enciclopedia.py) | ❌ DELETE |
| `ENCICLOPEDIA/iniciar_grimorio.bat` | Archivo | Versión antigua (duplicado de iniciar_enciclopedia.bat) | ❌ DELETE |

#### C. Tests con Rutas Viejas — MUST FIX
| Archivo | Línea | Error | Fix |
|---------|-------|-------|-----|
| `tests/test_grimorio_guardian.py` | 10 | `from golem.canales.grimorio_guardian` | Change to `from computadora.canales.grimorio_guardian` |
| `tests/test_grimorio_guardian.py` | 11 | `from golem.nucleo.verificador_grimorio` | Change to `from computadora.nucleo.*` (if exists) |
| `tests/test_grimorio_emet_codigo.py` | 25 | `from libro_encantado.servidor_grimorio` | Change to `from ENCICLOPEDIA.servidor_enciclopedia` (check if used) |

#### D. Documentación Mixta — FIX BUT NOT CRITICAL
| Archivo | Línea | Change | Priority |
|---------|-------|--------|----------|
| `_docs/COMANDOS.md` | 157 | "servidor_grimorio" → "servidor_enciclopedia" | 🟡 MEDIUM |
| `_docs/SRS.md` | 2972 | "Shomer HaGrimorio" → "Shomer HaEnciclopedia" (but keep reference) | 🟡 MEDIUM |
| `_docs/SRS.md` | 2994 | "iniciar_grimorio.bat" → "iniciar_enciclopedia.bat" | 🟡 MEDIUM |
| `_docs/SRS.md` | 2997 | "servidor_grimorio.py" → "servidor_enciclopedia.py" | 🟡 MEDIUM |
| `_docs/SRS.md` | 3084, 3090 | "grimorio_guardian" → "enciclopedia_guardian" | 🟡 MEDIUM |
| `_docs/SDD.md` | 1272, 1470 | "grimorio_guardian" → "enciclopedia_guardian" | 🟡 MEDIUM |

---

## PLAN DE EJECUCIÓN RUBEDO (Atómico x 3 commits)

### COMMIT 1: Code Fixes (Critical Path)
```bash
# 1. Rename archivo de guardián (si existe)
mv computadora/canales/grimorio_guardian.py computadora/canales/enciclopedia_guardian.py

# 2. Fix imports en código
computadora/__main__.py línea 277: grimorio_guardian → enciclopedia_guardian
computadora/arquitectura/dimensiones.py línea 90: _M_GRIMORIO_GUARDIAN → _M_ENCICLOPEDIA_GUARDIAN
```

### COMMIT 2: Delete Obsolete Files
```bash
# 1. Eliminar archivos duplicados en ENCICLOPEDIA/
rm -f ENCICLOPEDIA/servidor_grimorio.py
rm -f ENCICLOPEDIA/iniciar_grimorio.bat

# 2. Git log these deletions
```

### COMMIT 3: Test Fixes + Docs
```bash
# Fix old test paths
tests/test_grimorio_guardian.py: golem/ → computadora/
tests/test_grimorio_emet_codigo.py: libro_encantado/servidor_grimorio → ENCICLOPEDIA/servidor_enciclopedia

# Update documentation
_docs/COMANDOS.md línea 157
_docs/SRS.md líneas 2994, 2997, 3084, 3090
_docs/SDD.md líneas 1272, 1470
```

---

## VALIDACIÓN POST-RUBEDO

### Boot Test
```bash
echo "test" | python -m computadora 2>&1 | grep -i "grimorio_guardian|golem\.canales"
# Should return ZERO matches (clean import path)
```

### Grep Test
```bash
grep -r "from golem\." tests/ computadora/
# Should return ZERO matches (old paths removed)

grep -r "grimorio_guardian" computadora/ | grep -v "ENCICLOPEDIA/"
# Should return ZERO matches (except in esoteric ENCICLOPEDIA/)
```

### Tests
```bash
pytest tests/test_grimorio_guardian.py -v
# Should PASS (imports fixed)
```

---

## DEPENDENCIES DETECTED

**None**: No módulos externos afectados. Cambios son intrnos (rename, import path, file deletion).

---

## RISK ASSESSMENT

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Boot fails if guardian module not renamed | 🔴 CRÍTICO | Test boot after COMMIT 1 |
| Tests import from old paths | 🔴 CRÍTICO | Update test paths in COMMIT 3 |
| Duplicate files cause confusion | 🟠 ALTO | Delete obsolete files in COMMIT 2 |
| Docs reference old names | 🟡 MEDIUM | Update docs in COMMIT 3 |

---

## NEXT PHASES

### CITRINITAS (Síntesis)
- Optimizar: ¿Renombrar clase `GrimorioGuardian` a `EnciclopediaGuardian`?
- Trade-off: Afecta más archivos pero es coherente semánticamente

### PALINGENESIA
- Lección: Refactors incompletos dejan inconsistencia
- Semilla: Checklistal post-rename (grep para viejos nombres)

