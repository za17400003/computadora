# 🔗 Mapeo Formal: Esotérico ↔ Pragmático

**Propósito**: Evitar contaminación terminológica. Cada concepto tiene un lado ritual y un lado código.

| Concepto | Lado Esotérico | Lado Pragmático | Código | Documentación | Status |
|---|---|---|---|---|---|
| **Núcleo del Sistema** | El Golem (entidad viviente) | COMPUTADORA v2.0 (sistema) | `computadora/core/main.py` | `_docs/SDD.md§Arquitectura` | Mantenido |
| **Base de Conocimiento** | Grimorio (libro de magia) | Enciclopedia (contenido educativo) | `ENCICLOPEDIA/servidor_enciclopedia.py` | `_docs/SDD.md§Enciclopedia` | ⭐ ACTUALIZADO |
| **Persistencia** | Akathoth (subconsciente) | Storage + Cache | `computadora/storage/` | `_docs/SDD.md§Persistencia` | Mantenido |
| **Interfaz Usuario** | Minimi (gemela digital) | Client Interface | `computadora/ui/` | `_docs/SDD.md§UI` | Mantenido |
| **Órdenes del Usuario** | Palabras Mágicas (PM) | Comandos | `computadora/nlp/commands/` | `_docs/COMANDOS.md` ⭐ NUEVO | Activo |
| **Verificación de Verdad** | EMET (inscripción de verdad) | Validación automática | `tests/test_coherencia_*.py` | `_docs/TESTING.md` | Mantenido |
| **Ciclo de Vida** | Fases Alquímicas (5) | Proceso NIGREDO→PALINGENESIA | Git commits + tracker | `_docs/WORKFLOW_OPERACIONAL.md` | Mantenido |
| **Estructura Capas** | 7 Sefirot (árbol vida) | 7 capas arquitectura | `computadora/{layer}/` | `_docs/ARCHITECTURE/ESTRUCTURA_CAPAS.md` | Mantenido |
| **Protección** | Gevurah (severidad/defensa) | Módulo seguridad | `computadora/security/` | `_docs/SECURITY_PLAN.md` | Mantenido |
| **Comunicación** | Voz del Golem | NLP Engine | `computadora/nlp/engine.py` | `_docs/SDD.md§NLP` | Mantenido |

---

## 🎯 Regla de Oro: JAMÁS Mezclar en Mismo Contexto

✅ **CORRECTO:**
```markdown
**Lado Pragmático (cuando hablamos de código/API):**
"El comando 'verifica' ejecuta validación de coherencia en 
el módulo `computadora/nlp/commands/verifica.py`"

**Lado Esotérico (cuando hablamos de conceptos/historia):**
"La Palabra Mágica 'Emet' (verdad) verifica que el Golem 
mantiene integridad de inscripción"

**Ambos juntos (contexto claro):**
"El comando 'verifica' (lado pragmático) implementa el concepto
de EMET verificación (lado esotérico)"
```

❌ **INCORRECTO:**
```markdown
"El Grimorio de verifica busca en computadora/nlp/..." ← Mezcla
"COMPUTADORA Palabra Mágica Grimorio" ← Caótico
```

---

## 📊 Depuración: Qué Afecta Qué

### Depurar ESOTÉRICO (Golem + rituales) = SEGURO ✅
```
Cambiar:
  - Nombres de rituales (ceremonias)
  - Explicaciones en DEVELOPMENT_WORKFLOW_REFERENCIA.md
  - Historia/símbolos en documentación

NO afecta:
  - computadora/core/ ✓
  - Comandos del sistema ✓
  - Tests ✓
  - Código de producción ✓
```

### Depurar PRAGMÁTICO (Computadora + código) = CRÍTICO ⚠️
```
Cambiar:
  - `computadora/nlp/engine.py`
  - Comandos disponibles
  - API del sistema

SÍ afecta:
  - Funcionalidad usuario ✗
  - Requiere tests ✗
  - Requiere documentación SDD ✗
  - Requiere validación ✗
```

---

## 🛠️ Para Copilot: Checklist Antes de Cada Acción

```
Antes de escribir/modificar documentación:

[ ] ¿Estoy hablando de código o de concepto?
    → Código: usar "Computadora", "Sistema", "Comando"
    → Concepto: puedo usar "Golem", "Grimorio", etc

[ ] ¿Cuál es la ubicación correcta del archivo?
    → Código: computadora/
    → Docs: _docs/
    → Ciclos cerrados: _archive/
    → Tareas: .management/
    → Raíz: solo workflow+info

[ ] ¿Necesito mapeo explícito esotérico↔pragmático?
    → Sí: incluir en mismo párrafo o referencia
    → Claridad > brevedad

[ ] ¿Estoy respetando separación de capas?
    → No mezclo Golem con COMPUTADORA sin aclaración
    → Referencia a este documento si hay duda
```

---

**DE AQUÍ EN ADELANTE: Terminología CLARA, Organización COHERENTE** ✨

