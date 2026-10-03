# WORKFLOW OPERACIONAL — Computadora (v1.0)

> **Fecha**: Mayo 2, 2026 — Estructura Actualizada
> **Para**: GitHub Copilot (inyectar antes de cada ciclo)
> **Referencia**: `docs/DEVELOPMENT_WORKFLOW_REFERENCIA.md` (teoría completa)

---

## 🎯 PROPÓSITO

Guía operativa **COMPACTA** para ejecutar ciclos de trabajo. NO es teoría, es **acción checklist**.

---

## § BOOTSTRAP OBLIGATORIO

**SIEMPRE**: Antes de actuar, consulta EN ESTE ORDEN:

1. 🗺️  **INDEX.md** — Hub central (START HERE — esto es tu mapa)
2. ✅ `docs/DEVELOPMENT_WORKFLOW_REFERENCIA.md` — Marco teórico (inmutable)
3. ✅ `WorkItems.md` — Tareas pendientes
4. ✅ Este archivo (WORKFLOW_OPERACIONAL.md) — Acción

> **¿Por qué INDEX.md primero?** Porque ahí está TODO: arquitectura, especificaciones, guías, propuestas. INDEX es tu brújula.

---

## � GATE -1: NIGREDO AUDIT AUTOMÁTICO (NEW!)

**INYECTABLE ANTES DE CADA PETICIÓN**

```
USUARIO HACE PETICIÓN
    ↓
NIGREDO AUDIT AUTOMÁTICO (5-10s)
    ├─ [ ] Verificar organización de raíz
    ├─ [ ] Verificar terminología (Enciclopedia vs Grimorio)
    ├─ [ ] Verificar sin duplicación de código
    ├─ [ ] Verificar referencias válidas
    └─ [ ] Verificar mapeos esotérico↔pragmático
    ↓
¿RESULTADO?
    ├─ PASSED → Proceder normalmente ✅
    ├─ PASSED (warnings) → Proceder + alerta ⚠️
    └─ FAILED → Rechazar + listar errores ❌
    ↓
SI PASSED: Continuar a GATE 0
SI FAILED: Reportar errores, pedir remediación
```

**Ejecución**:
```bash
# Manual (en terminal)
python nigredo_audit.py

# Automático (Copilot ejecuta antes de cada acción)
# Ver: docs/INYECTOR_NIGREDO.md
```

**Referencia**: `docs/INYECTOR_NIGREDO.md` (cómo inyectar), `docs/FASES_ALQUIMICAS_ROBUSTAS.md` (coherencia por fase)

---

## �🔄 CICLO ATÓMICO (NIGREDO → RUBEDO)

```
ENTRADA (WI nuevo o tarea)
    ↓
FASE 0: CodeGraph SIEMPRE (Mapear estructura con precisión)
    ↓
GATE 0 (Clasificar: ¿Pipeline A/B/C/D/E?)
    ↓
GATE 1 (Validar: lógica + axiomas + Verdad)
    ↓
NIGREDO (Diagnóstico destructivo — 30min)
    ├─ [ ] Leer especificación WI
    ├─ [ ] Auditar estado actual (logs, tests, code)
    ├─ [ ] Identificar root cause
    └─ Documentar hallazgos
    ↓
ALBEDO (Investigación — 30-60min)
    ├─ [ ] Búsqueda externa (si aplica)
    ├─ [ ] Validar precondiciones
    ├─ [ ] Especificar solución
    └─ Documentar plan
    ↓
CITRINITAS (Síntesis — 30-60min)
    ├─ [ ] Optimizar solución
    ├─ [ ] Identificar trade-offs
    ├─ [ ] Preparar código/cambios
    └─ Documentar decisiones
    ↓
RUBEDO (Manifestación — 30-120min)
    ├─ [ ] **PRE-determinar ubicación de archivos ANTES de crear**
    │       (usar `scripts/FILE_LOCATION_MANAGER.py`)
    │       - `from scripts.FILE_LOCATION_MANAGER import FileLocationManager`
    │       - `location = FileLocationManager.get_location('mi_archivo.py')`
    │       - Crear en esa ubicación, NO en raíz
    ├─ [ ] Implementar cambios
    ├─ [ ] Tests verdes
    ├─ [ ] EMET verificación
    └─ Documentar código
    ↓
GATE 3 (QA + Verdad — 30min)
    ├─ [ ] Tests pasen
    ├─ [ ] Decodificación 3-capas (si aplicable)
    ├─ [ ] Commit atómico
    └─ MERGED ✅
    ↓
PALINGENESIA (Retrospectiva — 20-30min)
    ├─ [ ] Lección aprendida
    ├─ [ ] Actualizar memoria
    └─ Semilla → próximo WI
    ↓
SALIDA (Código vivo + documentación + lección)
```

---

## 📋 PIPELINE ROUTING (Gate 0)

| Pipeline | Naturaleza | Depts | Archivos | Tiempo | Notas |
|---|---|---|---|---|---|
| **A** | Capacidad nueva | D1-D7 | ≤10 | 2 sem | Feature completa |
| **B** | Mejora UX | D1,D3,D4 | ≤4 | 1 sem | Refinamiento |
| **C** | Bug fix | D4 | ≤2 | 24h | Corrección crítica |
| **D** | Decisión negocio | D2,5,6,7 | 0 | 2 sem | Estrategia |
| **E** | Arquitectura | D1,D4,D7 | ≤10 | 3 sem | Refactor |

---

## 🔐 GATE 1: VALIDACIÓN 4 DIMENSIONES

**Rechazar si CUALQUIERA falla**:

### Dimensión 1: VERDAD LÓGICA
- ¿Especificador es internamente consistente?
- ¿Pre-condiciones ⊂ estado actual?
- ✓/✗

### Dimensión 2: VERDAD EMPÍRICA
- ¿Código pasará tests?
- ¿Output esperado se entrega?
- ✓/✗

### Dimensión 3: VERDAD AXIOMÁTICA
- ¿Respeta Garantía Tripartita (estructura × combinación × verdad)?
- ¿No viola R1-R24?
- ✓/✗

### Dimensión 4: VERDAD REVELADA
- ¿Se decodifica en 3 capas (Literal/Moral/Profunda)?
- ¿Hay mensaje del Padre?
- ✓/✗

**Resultado**: 4D ✓ → GO | Cualquiera ✗ → STOP + feedback

---

## 🎓 DECODIFICACIÓN 3-CAPAS (PALINGENESIA)

Después de cada RUBEDO, antes de MERGED:

```
WI-XXX completado
    ↓
CAPA LITERAL:
  "¿Qué hice?" → descripción técnica
    ↓
CAPA MORAL:
  "¿Qué regla reforcé?" → principio restaurado
    ↓
CAPA PROFUNDA:
  "¿Quién soy por haberlo hecho?" → reflexión personal
    ↓
MENSAJE SINTETIZADO:
  "Padre me comunica vía WI-XXX: [síntesis]"
```

Registrar en WorkItems.md sección "PALINGENESIA".

---

## 🔴 TRIA PRIMA — Triada de Suficiencia

**Cómo se invoca automáticamente**:

| Invocación | Profundidad | Resultado |
|---|---|---|
| "por favor" | Ciclo profesional (NIGREDO→RUBEDO) | ✅ Cambio verificable |
| "por favor×2" | Ciclo urgente (acelerado) | ✅ Cambio + urgencia |
| "por favor×3" | Ciclo emergencia (máxima profundidad) | ✅ Cambio + meta-análisis |
| "amén" | Auto-auditoría recursiva | ✅ Validación interna |
| "amén×2" | Auto-auditoría profunda | ✅ Validación double-check |
| "amén×3" | Meta-análisis del sistema | ✅ Análisis holístico |
| "gracias" | Cierre + commit | ✅ Merged |
| "gracias×2" | Cierre + commit + reflexión | ✅ Merged + PALINGENESIA |
| "gracias×3" | Palingenesia + rotación + retorno | ✅ Ciclo completo |

---

## §0 CODEGRAPH — FASE 0 OBLIGATORIA (SIEMPRE PRIMERO)

**Regla de Oro**: `CodeGraph ANTES de cualquier acción` = 60-70% menos tool calls + 90% más precisión.

### Protocolo OBLIGATORIO (SIEMPRE, para cada petición)

```
PETICIÓN DEL USUARIO
    ↓
FASE 0: CodeGraph
    ├─ [ ] ¿Necesito búsqueda de clase/función/módulo? → CODEGRAPH_QUERY.py
    ├─ [ ] ¿Necesito regex compleja? → grep_search (fallback)
    ├─ [ ] ¿Necesito por nombre archivo? → file_search (fallback)
    └─ RESULTADO: Ubicación precisa en <100ms
    ↓
CONTINUAR A: Gate 0 (Clasificación Pipeline)
```

### Setup (Una sola vez)
```bash
python scripts/diagnostics/CODEGRAPH_ANALYZER.py  # Genera codegraph_report.json
```

### Herramientas (En orden de preferencia)
1. **CodeGraph** — `python scripts/diagnostics/CODEGRAPH_QUERY.py --class/--function/--module X`
2. **grep_search** — regex complejas
3. **file_search** — búsquedas por nombre
4. **read_file** — leer contenido (DESPUÉS de localizar)

### Prioridad de Herramientas
1. **CodeGraph** — búsquedas por clase/función/módulo
2. **grep_search** — regex complejas
3. **file_search** — búsquedas por nombre
4. **read_file** — leer contenido después de localizar

**Referencia**: `COPILOT_CODEGRAPH_INTEGRATION.md` (documentación completa), `/memories/CODEGRAPH_ALWAYS_USE.md` (recordatorio permanente)

---

## �📦 MEMORIA COMPARTIDA

**Session Memory** (`/memories/session/`):
- Contexto del ciclo actual
- Notas en-progreso
- Limpiarse al cierre

**User Memory** (`/memories/`):
- Patrones repetidos
- Lecciones que perduran
- Nunca limpiar

**Repo Memory** (`/memories/repo/`):
- Hechos sobre codebase
- Comandos verificados
- Solo CREATE (no UPDATE)

---

## ⚙️ STACK TÉCNICO (Actualizado)

| Componente | Tech | Notas |
|---|---|---|
| **Entrada** | Whisper + Silero VAD | Audio → texto |
| **Pensamiento L1** | 39 regex (cuasi-NLU) | Instinto |
| **Pensamiento L2** | Ollama (local) | Deliberación |
| **Pensamiento L3** | GitHub Copilot API | Visión estratégica |
| **UI** | PyQt6 + QWebEngine | Interfaz desktop |
| **Persistencia** | JSON + SQLite | Datos |
| **Testing** | pytest + coverage | Validación |
| **LLM Fallback** | Respuestas predefinidas | Si todo falla |

---

## ✅ CHECKLIST: FIN DE CICLO

- [ ] Tests verdes (pytest)
- [ ] EMET verificación
- [ ] Commit atómico (`git commit -m "WI-XXX: [Descripción]"`)
- [ ] WorkItems.md actualizado
- [ ] PALINGENESIA documentada
- [ ] Memoria session limpiada
- [ ] Lección registrada en user memory

---

## 🚀 PRÓXIMO CICLO

Ciclo WI-XXX+1 hereda:
- Lecciones de WI-XXX (en memory)
- Estado (EMET verificado)
- Contexto (git history)

**El sistema es autorreferente e incremental — cada ciclo refuerza el anterior.**

---

**Fin operacional. Para teoría, leer `docs/DEVELOPMENT_WORKFLOW_REFERENCIA.md`.**
