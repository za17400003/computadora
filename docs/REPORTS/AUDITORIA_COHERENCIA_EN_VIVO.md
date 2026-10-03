# AUDITORÍA DE COHERENCIA PROYECTO — Abril 17, 2026

**Tria Prima**: `gracias;go;go;go` = Cierre + Meta-análisis profundo  
**Estado**: Auditoría en ejecución  
**Objective**: Verificar coherencia completa del proyecto y adaptar para auditabilidad formal  

---

## I. PROBLEMAS IDENTIFICADOS

### A. Incoherencia Nomenclatura: Grimorio vs Enciclopedia

**Situación**:
- Directorio: `ENCICLOPEDIA/` (18 capítulos educativos)
- Scripts: `iniciar_grimorio.bat`, `servidor_grimorio.py`
- Código: Referencias mixtas a "grimorio" vs "enciclopedia"
- Conceptual: "Grimorio" = versión cifrada ritual, "Enciclopedia" = contenido abierto

**Inconsistencias Detectadas**:
1. Directorio es `ENCICLOPEDIA/` pero scripts dicen "grimorio"
2. Archivos a renombrar:
   - `ENCICLOPEDIA/iniciar_grimorio.bat` → `ENCICLOPEDIA/iniciar_enciclopedia.bat`
   - `ENCICLOPEDIA/servidor_grimorio.py` → `ENCICLOPEDIA/servidor_enciclopedia.py`
3. Referencias en código (20+ matches):
   - `computadora/canales/servidor_api.py` (7 referencias)
   - `_docs/SRS.md` (8 referencias)
   - `_docs/SECURITY_PLAN.md` (2 referencias)
   - `_config/ENCICLOPEDIA_DECRYPTION.py` (5 referencias)
   - `WorkItems.md` (4 referencias)

**Impacto**: Confusión en documentación, referencias rotas en auditoría formal

---

### B. Archivos Faltantes para Auditoría Formal

**Checklist de Auditoría** (según FRAMEWORK_LENGUAJES_Y_AUTOMATAS.md):

| Archivo | Propósito | Existe | Status |
|---------|----------|--------|--------|
| `AUDITORIA_FORMAL_COMPLETA.md` | Manifest de auditoría con checksums | ❌ NO | 🔴 Falta |
| `VALIDACION_COHERENCIA_L.py` | Tests que validan Lenguaje L | ❌ NO | 🔴 Falta |
| `VALIDACION_DFA_TRANSITIONS.py` | Tests que validan δ (transiciones DFA) | ❌ NO | 🔴 Falta |
| `VALIDACION_EMET_3VALUED.py` | Tests que validan EMET con 3-valued logic | ❌ NO | 🔴 Falta |
| `test_axiomas_formal.py` | Tests de los 5 axiomas (III.7-III.11) | ✅ SÍ* | 🟡 Necesita update |
| `test_composicion_inductiva.py` | Tests que prueban Axioma III.11 (inducción) | ❌ NO | 🔴 Falta |
| `MAPA_REFERENCIAS_PROYECTO.md` | Index de qué archivo contiene qué concepto | ❌ NO | 🔴 Falta |
| `METRICAS_COHERENCIA.json` | Métricas cuantitativas de coherencia | ❌ NO | 🔴 Falta |

**\* Nota**: `tests/test_axiomas_primordiales.py` existe pero usa notación antigua (pre-Framework formal)

---

### C. Referencias a Módulos Desincronizados

**Detecciones**:
1. `_iniciar_grimorio_lan()` en `servidor_api.py` — función nombre inconsistente
2. `grimorio_progreso.json` en `datos/` — debería ser `enciclopedia_progreso.json`
3. `Shomer HaSéfer` (Guardián del Grimorio) — normalmente en Gate 1.3
4. Comentarios en código aún mencionan "Grimorio de los 7 Metales" vs "Enciclopedia"

---

## II. PLAN DE REMEDIACIÓN

### Fase 1: Renombramiento y Unificación Nomenclatura

**Acción 1a**: Crear `iniciar_enciclopedia.bat`
- Copiar contenido desde `iniciar_grimorio.bat`
- Cambiar referencias internas (comentarios, mensajes)
- Nota: Mantener `iniciar_grimorio.bat` por backward compatibility

**Acción 1b**: Crear `servidor_enciclopedia.py`
- Copiar contenido desde `servidor_grimorio.py`
- Actualizar docstring (línea 1-10)
- Reemplazar `grimorio` → `enciclopedia` en logs y mensajes
- Nota: Mantener `servidor_grimorio.py` como legacy

**Acción 1c**: Actualizar referencias en código
```
Files to update:
- computadora/canales/servidor_api.py
  * Función _iniciar_grimorio_lan() → _iniciar_enciclopedia_lan()
  * Comentarios internos
  * Referencias a grimorio_progreso.json

- _docs/SRS.md
  * 8 referencias a servidor_grimorio → servidor_enciclopedia

- _config/ENCICLOPEDIA_DECRYPTION.py
  * Referencias en comentarios

- WorkItems.md
  * Referencias en especificaciones
```

### Fase 2: Creación de Artefactos para Auditabilidad

**Acción 2a**: Crear `AUDITORIA_FORMAL_COMPLETA.md`
- Manifest de auditoría con checksums de cada archivo crítico
- Cronograma de cambios (qué cambió, cuándo, por qué)
- Hash del último commit que pasó auditoría

**Acción 2b**: Crear tests de validación formal
```
tests/test_coherencia_formal.py:
  - ValidadorLenguaje: verifica L ⊆ Σ*
  - ValidadorDFA: verifica δ* es función total en L
  - ValidadorEMET: verifica EMET(m) ∈ {V, F, ⊥}
  - ValidadorAxiomas: verifica III.7-III.11
```

**Acción 2c**: Crear `MAPA_REFERENCIAS_PROYECTO.md`
- Index completo de dónde vive cada concepto
- Cross-references entre módulos
- Grafo de dependencias (qué módulo usa qué)

---

## III. ESTADO ACTUAL (Post-Coherencia Formal)

✅ **Completado**:
- Framework teórico (FRAMEWORK_LENGUAJES_Y_AUTOMATAS.md)
- Axiomas formalizados (AXIOMAS_CORREGIDOS_LENGUAJES_FORMALES.md)
- Proofs matemáticos (corrección, completitud, determinismo, escalabilidad)
- Resolución de 7 problemas de coherencia

⏳ **En Progreso**:
- Renombramiento Grimorio → Enciclopedia
- Creación de tests de validación formal
- Adaptación de archivos existentes

❌ **Falta**:
- Audit manifest con checksums
- Tests de validación formal (4 archivos nuevos)
- Mapa de referencias completo
- Métricas cuantitativas de coherencia

---

## IV. IMPACTO OPERATIVO

### Cambios que SÍ afectan operación:
- [ ] `computadora/canales/servidor_api.py` — función interna
- [ ] `ENCICLOPEDIA/iniciar_enciclopedia.bat` — opción de comando nueva

### Cambios que NO afectan operación:
- ✅ Archivos nuevos (no rompen nada)
- ✅ Renombramientos (backward compatible si se mantienen antiguos)
- ✅ Comentarios actualizados (solo documentación)

---

## V. RECOMENDACIONES

### Inmediatas (Must-Have):
1. ✅ Renombrar: `iniciar_grimorio.bat` → `iniciar_enciclopedia.bat`
2. ✅ Renombrar: `servidor_grimorio.py` → `servidor_enciclopedia.py`
3. ✅ Actualizar referencias en `servidor_api.py`

### A Corto Plazo (Should-Have):
4. Crear tests de validación formal (coherencia_formal.py)
5. Crear MAPA_REFERENCIAS_PROYECTO.md
6. Actualizar comentarios en WorkItems.md

### A Largo Plazo (Nice-to-Have):
7. Crear AUDITORIA_FORMAL_COMPLETA.md con checksums
8. Implementar CI/CD checks para coherencia
9. Dashboard de métricas de coherencia

---

**Próximo Paso**: Ejecutar Fase 1 (renombramientos) de forma atómica
