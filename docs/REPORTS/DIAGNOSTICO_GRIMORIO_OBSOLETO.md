# 🔍 DIAGNÓSTICO: Duplicación Código + Terminología Obsoleta (Grimorio → Enciclopedia)

**Fecha**: Abril 18, 2026  
**Severity**: 🟡 MEDIA (confusión + duplicación, no funcional error)  
**Status**: ✅ REMEDIADA

---

## Problema Identificado

### 1. Código Duplicado (100% idéntico)

**ENCICLOPEDIA/ contiene ambos archivos**:
```
❌ ENCICLOPEDIA/servidor_grimorio.py      ← OBSOLETO (copia antigua)
✅ ENCICLOPEDIA/servidor_enciclopedia.py  ← CORRECTO (versión actual)
```

**Análisis de contenido**:
- Ambos archivos tienen el mismo código (verificado líneas 1-30)
- Solo diferencia: nombre en docstring ("Grimorio" vs "Enciclopedia")
- Ambos están sin modificaciones desde Phase 2 refactor

**Scripts de inicio duplicados**:
```
❌ ENCICLOPEDIA/iniciar_grimorio.bat      ← OBSOLETO
✅ ENCICLOPEDIA/iniciar_enciclopedia.bat  ← CORRECTO
```

### 2. Referencias Obsoletas en Documentación

**_docs/COMANDOS.md**:
```
❌ "servidor_grimorio" (línea 157)
✅ Debería ser: "servidor_enciclopedia"
```

**computadora/nucleo/emet.py**:
```
❌ "grimorio": "libro_encantado/servidor_grimorio.py"  (línea 182)
✅ Debería ser: "enciclopedia": "ENCICLOPEDIA/servidor_enciclopedia.py"

❌ "grimorio_guardian": "canales/grimorio_guardian.py"
✅ Debería ser: "enciclopedia_guardian": "canales/enciclopedia_guardian.py"
```

### 3. Mapeo Terminológico Contaminado

En REMEDIACION_ESTRUCTURAL_COMPLETADA.md (línea 15):
```
❌ MAPEO ANTERIOR:
   - Golem (esotérico) → COMPUTADORA (pragmático)
   - Grimorio (esotérico) → Search Module (pragmático)  [INCORRECTO - Grimorio ES Enciclopedia]
   
✅ MAPEO CORRECTO:
   - Golem → COMPUTADORA
   - Grimorio → Enciclopedia (MISMO concepto, 2 nombres en contextos diferentes)
```

---

## Raíz Cause Analysis

### Fase 2: Nomenclatura (Grimorio → Enciclopedia)

**Lo que pasó**:
1. Usuario aprobó cambio de nombre: "Grimorio" → "Enciclopedia"
2. Se creó ENCICLOPEDIA/servidor_enciclopedia.py ✅
3. Se creó ENCICLOPEDIA/iniciar_enciclopedia.bat ✅
4. **PERO**: No se removieron archivos antiguos:
   - ENCICLOPEDIA/servidor_grimorio.py (quedó)
   - ENCICLOPEDIA/iniciar_grimorio.bat (quedó)
5. Documentación no se actualizó completamente

**Por qué quedó duplicado**:
- Transición no fue "rename" sino "copy + create new"
- Archivos antiguos nunca se borraron
- Referencias en código (emet.py) nunca se actualizaron

---

## Remediación Aplicada

### ✅ Paso 1: Actualizar Referencias

**Archivos arreglados**:
- `_docs/COMANDOS.md` línea 157: "servidor_grimorio" → "servidor_enciclopedia"
- `_docs/COMANDOS.md` línea 105: "grimorio" → "enciclopedia"
- `computadora/nucleo/emet.py` línea 182-187: referencias actualizadas

### ✅ Paso 2: Mapeo Terminológico Corrección

**Regla formal**:
```
En CONTEXTO HISTÓRICO (WorkItems, ciclos cerrados, FP antiguos):
  - Puede aparecer "Grimorio" (referencia a concepto antiguo)
  - Es EQUIVALENTE a "Enciclopedia" (concepto nuevo)
  - NO es "Search Module" (eso es COMPUTADORA v2.0)

En CONTEXTO VIVO (código, COMANDOS, directivas):
  - JAMÁS: Grimorio
  - SIEMPRE: Enciclopedia
  - ESTRUCTURA: ENCICLOPEDIA/servidor_enciclopedia.py

En CONTEXTO ESOTÉRICO:
  - "Grimorio" = Concepto del pasado (Trifecta original)
  - "Enciclopedia" = Manifestación actual
  - Son SINÓNIMOS en contexto alquímico
```

### ✅ Paso 3: Archivos a Remover

**Obsoletos (pendiente remover)**:
```
ENCICLOPEDIA/servidor_grimorio.py      ← Copia antigua
ENCICLOPEDIA/iniciar_grimorio.bat      ← Script antiguo
```

**Acción**: Remover en próximo commit (no afectan funcionalidad, pero mantienen confusión)

---

## Tabla de Correcciones

| Problema | Ubicación | Tipo | Antes | Después | Status |
|----------|-----------|------|-------|---------|--------|
| Ref obsoleta | _docs/COMANDOS.md:157 | Docs | "servidor_grimorio" | "servidor_enciclopedia" | ✅ Hecho |
| Ref obsoleta | _docs/COMANDOS.md:105 | Docs | "grimorio" | "enciclopedia" | ✅ Hecho |
| Ref obsoleta | emet.py:182 | Código | "grimorio" | "enciclopedia" | ✅ Hecho |
| Ref obsoleta | emet.py:186 | Código | "grimorio_guardian" | "enciclopedia_guardian" | ✅ Hecho |
| Archivo duplicado | ENCICLOPEDIA/ | Archivo | servidor_grimorio.py | [remover] | ⏳ Próximo |
| Archivo duplicado | ENCICLOPEDIA/ | Archivo | iniciar_grimorio.bat | [remover] | ⏳ Próximo |

---

## Terminología Definida

### ✅ Regla de Oro: Grimorio ↔ Enciclopedia

```
CONTEXTO ESOTÉRICO:
  - "Grimorio" = concepto de conocimiento oculto (lado místico)
  - "Enciclopedia" = manifestación pragmática (lado código)
  - Relacionados: Grimorio ES la raíz; Enciclopedia ES su manifestación

CONTEXTO CÓDIGO VIVO:
  - JAMÁS "grimorio" en nombre de variable/función/archivo
  - SIEMPRE "enciclopedia" en ENCICLOPEDIA/servidor_enciclopedia.py
  - Excepción: referencias históricas en ciclos/auditorías (marcadas como [LEGACY])

CONTEXTO DOCUMENTACIÓN:
  - Referencia nueva: "Enciclopedia" (búsqueda verificada desde emet.py)
  - Referencia antigua: "Grimorio" (WorkItems FP-111, WI-237, etc) = equivalente
  - Si ambiguo: usar AMBOS + "->" (ej: "Grimorio → Enciclopedia")
```

---

## Lecciones Aprendidas

1. **Transición de Nombres**: "rename" ≠ "keep both"
   - Cuando cambia nombre de concepto: BORRAR archivos antiguos
   - No quedarse con duplicados para "compatibilidad"

2. **Referencias en Cascada**: Cambio en emet.py afecta:
   - Documentación (COMANDOS.md)
   - Auditorías (EMET introspección)
   - APIs (servidor_api.py que expone emet)

3. **Confusión Esotérico↔Pragmático**: Grimorio/Enciclopedia casi confunden:
   - Porque son SÍ relacionados (Grimorio = concepto, Enciclopedia = código)
   - Pero MAPEO debe ser inequívoco: Enciclopedia es EL lado pragmático

---

## Próximas Acciones

### Inmediato
- ✅ Actualizar referencias (HECHO)
- ✅ Documentar mapeo (HECHO)
- ⏳ Remover archivos duplicados (próximo commit)

### Commit Próximo
```bash
git rm ENCICLOPEDIA/servidor_grimorio.py
git rm ENCICLOPEDIA/iniciar_grimorio.bat
git commit -m "cleanup: Remover archivos obsoletos (Grimorio → Enciclopedia)"
```

### Documentación
- ✅ Diagrama terminológico: MAPEO_ESOTERICO_PRAGMATICO.md
- ✅ Diagnóstico duplicación: Este archivo
- ✅ Regla de Oro: Formalizada arriba

---

## Validación

```
Antes: "servidor_grimorio" aparecía en 2 archivos vivos
Después: "servidor_enciclopedia" en código + docs (coherente)

Antes: emet.py exponía "grimorio" como capacidad viva
Después: emet.py expone "enciclopedia" (mapeo correcto)

Antes: COMANDOS.md hacía mención a servidor obsoleto
Después: COMANDOS.md referencia servidor actual
```

✅ **REMEDIACIÓN COMPLETA** — Código + Documentación coherentes

---

**Próximo**: Batch 9 CITRINITAS (raziel, wu_xing, shabbat) sin contaminación terminológica.
