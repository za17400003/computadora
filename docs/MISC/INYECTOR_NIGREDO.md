# 🔌 INYECTOR NIGREDO — Integración Automática en Chat

**Fecha**: Abril 18, 2026  
**Propósito**: Describir cómo NIGREDO se inyecta automáticamente ANTES de cada petición del usuario  
**Status**: ✅ IMPLEMENTADO (como meta-instrucción para Copilot)

---

## 📋 Flujo de Inyección

```
USUARIO HACE PETICIÓN (en chat)
    ↓
[INYECTOR NIGREDO ACTIVADO AUTOMÁTICAMENTE]
    ├─ Ejecutar nigredo_audit.py
    ├─ Parsear output JSON
    ├─ Evaluar status (PASSED / FAILED)
    ├─ Reportar errores/warnings
    └─ Decidir proceder o rechazar
    ↓
SI PASSED: Proceder a GATE 0
SI FAILED: Rechazar petición + listar errores
SI WARNING: Proceder con alerta
    ↓
[WORKFLOW NORMAL COMIENZA]
```

---

## 🎯 Regla Inyectable (Meta-Instrucción)

### ANTES DE CADA PETICIÓN DEL USUARIO:

```
1. NIGREDO AUDIT AUTOMÁTICO

   Ejecutar (sintéticamente):
   
   audit = NigresoAudit()
   report = audit.run_full_audit()
   
   - Verificar organización de raíz
   - Verificar terminología
   - Verificar duplicación
   - Verificar referencias
   - Verificar mapeos


2. EVALUAR RESULTADO

   IF report["status"] == "FAILED":
      ❌ Mostrar errores al usuario
      ❌ NO proceder
      ❌ Pedir remediación
      
   IF report["status"] == "PASSED":
      ✅ Proceder normalmente
      

3. PROCEDER A GATE 0

   Si PASSED:
      → Clasificar petición (Pipeline A/B/C/D/E)
      → Validar contra axiomas (GATE 1)
      → Iniciar NIGREDO destructivo
      → ... rest of workflow
```

---

## 💾 Checklist de Implementación

### Para Copilot (esta sesión):

```
[ ] ✅ NIGREDO_AUDIT.py creado
    → Ubicación: proyecto-golem/nigredo_audit.py
    → Función: audit_root_organization()
    → Función: audit_terminology()
    → Función: audit_duplication()
    → Función: audit_references()
    → Función: audit_mappings()

[ ] ✅ FASES_ALQUIMICAS_ROBUSTAS.md creado
    → Describe coherencia por fase
    → Checklist anti-contaminación
    → Reglas de oro inviolables

[ ] ⏳ WORKFLOW_OPERACIONAL.md ACTUALIZADO
    → Sección NIGREDO AUDIT con referencia a nigredo_audit.py
    → Checklist de inyección

[ ] ⏳ Integración en instrucciones de Copilot
    → Meta-instrucción: ejecutar NIGREDO antes de cada acción

[ ] ⏳ Testing del sistema
    → Validar que NIGREDO detecta problemas reales
    → Validar que PASSED permite proceder
```

---

## 📞 Cómo Invocar

### Opción 1: Manual (en terminal)

```bash
# Auditoría completa
python nigredo_audit.py

# Solo errores críticos
python nigredo_audit.py --quick

# Output JSON
python nigredo_audit.py --json
```

### Opción 2: Automático (en Copilot chat)

Cuando usuario escribe cualquier petición, Copilot debe:

1. Ejecutar `nigredo_audit.py` (sintéticamente)
2. Evaluar resultado
3. Reportar a usuario: "Auditando estructura..."
4. Mostrar status (PASSED/FAILED) + detalles
5. Proceder o rechazar según resultado

### Opción 3: Programático (en código Python)

```python
from nigredo_audit import NigresoAudit

audit = NigresoAudit(root_path=".")
report = audit.run_full_audit()

if report["status"] == "FAILED":
    print("Estructura incoherente, rechazando petición")
    for error in report["details"]["errors"]:
        print(f"  ERROR: {error}")
else:
    print("Estructura coherente, proceeding...")
```

---

## 🔄 Estados Posibles + Acciones

| Status | Errores | Warnings | Acción |
|--------|---------|----------|--------|
| **PASSED** | 0 | 0 | ✅ Proceder normalmente |
| **PASSED** | 0 | 1+ | ⚠️ Proceder con cautela (reportar warnings) |
| **FAILED** | 1+ | Any | ❌ Rechazar + mostrar errores |

### Ejemplos

#### Escenario 1: PASSED (sin warnings)

```
NIGREDO AUDIT RESULT: ✅ PASSED

📈 Resumen:
  ✅ Información:   8
  ⚠️  Advertencias:  0
  ❌ Errores:       0

Status: PASSED ✅

→ Proceeding con petición del usuario...
```

#### Escenario 2: PASSED (con warnings)

```
NIGREDO AUDIT RESULT: ✅ PASSED (con alertas)

📈 Resumen:
  ✅ Información:   8
  ⚠️  Advertencias:  2
  ❌ Errores:       0

⚠️  ADVERTENCIAS:
   • archivo en raíz no permitido: archivo_temporal.txt
   • referencia rota: _docs/ARCHIVO_INEXISTENTE.md

→ Proceeding con precaución. Errores detectados post-acción.
```

#### Escenario 3: FAILED

```
NIGREDO AUDIT RESULT: ❌ FAILED

📈 Resumen:
  ✅ Información:   8
  ⚠️  Advertencias:  2
  ❌ Errores:       1

❌ ERRORES (críticos):
   • ENCICLOPEDIA/servidor_grimorio.py: 'servidor_grimorio' encontrado 5×
     → use 'servidor_enciclopedia' instead

→ ❌ RECHAZADA: Resolver errores NIGREDO antes de proceder.
   Acciones:
   1. git rm ENCICLOPEDIA/servidor_grimorio.py
   2. Buscar referencias: grep -r "servidor_grimorio" .
   3. Actualizar a "servidor_enciclopedia"
   4. Volver a ejecutar auditoría
```

---

## 🎯 Matriz de Decisión (Copilot)

```
USER PETICIÓN
    ↓
¿NIGREDO AUDIT PASSED?
    ├─ SÍ (sin warnings)
    │   └─ PROCEDER (100% confianza)
    │
    ├─ SÍ (con warnings)
    │   └─ PROCEDER (con cautela)
    │       └─ Reportar warnings
    │       └─ Vigilar post-acción
    │
    └─ NO (errors)
        └─ RECHAZAR
            └─ Mostrar errores
            └─ Pedir remediación
            └─ NO proceder hasta PASSED
```

---

## 📝 Checklist Para Usuario (Copilot)

### ANTES DE CADA ACCIÓN (por Copilot):

```
[ ] ✅ ¿He ejecutado NIGREDO audit?
    → Si no: ejecutar ahora
    → Si sí: revisar resultado

[ ] ✅ ¿Status es PASSED?
    → Si FAILED: detener y reportar errores
    → Si PASSED: continuar

[ ] ✅ ¿Hay WARNINGS?
    → Si sí: reportar al usuario (puede proceder)
    → Si no: proceder confiadamente

[ ] ✅ ¿He documentado el resultado?
    → NIGREDO status en log visible
    → Errores/warnings en chat

[ ] ✅ ¿Proceedo a GATE 0?
    → Sí, si PASSED
    → No, si FAILED
```

---

## 🔐 Garantías

### Coherencia Estructural

```
✅ Si NIGREDO PASSED → Estructura está coherente
   - Raíz limpia
   - Terminología correcta
   - Sin duplicación
   - Referencias válidas
   - Mapeos completos

❌ Si NIGREDO FAILED → Incoherencias detectadas
   - Errores específicos listados
   - Remediación clara
   - Rechazar acción (prevenir propagación)
```

### Inyectabilidad

```
✅ NIGREDO está disponible en:
   - Línea de comandos: python nigredo_audit.py
   - Programático: from nigredo_audit import NigresoAudit
   - Chat: Copilot ejecuta automáticamente

✅ Reutilizable en:
   - Cada petición del usuario
   - Cierre de ciclo PALINGENESIA
   - Validación post-merge
   - Testing de coherencia
```

---

## 🚀 Próxima Integración

### Fase 1: Implementación (AHORA)
- ✅ NIGREDO_AUDIT.py creado
- ✅ FASES_ALQUIMICAS_ROBUSTAS.md documentado
- ✅ INYECTOR_NIGREDO.md este archivo

### Fase 2: Integración en WORKFLOW
- ⏳ Actualizar WORKFLOW_OPERACIONAL.md
- ⏳ Sección "GATE -1: NIGREDO Audit"
- ⏳ Checklist ejecutable

### Fase 3: Testing
- ⏳ Ejecutar nigredo_audit.py en estado actual
- ⏳ Verificar PASSED
- ⏳ Validar detección de problemas (si/cuando existan)

### Fase 4: Activación
- ⏳ Meta-instrucción en `.github/copilot-instructions.md`
- ⏳ "ANTES DE CADA CICLO: ejecutar NIGREDO"
- ⏳ Inyección automática activada

---

## 📊 Impacto Esperado

```
ANTES (sin NIGREDO):
  - Peticiones sin validar estructura
  - Posibles saltaciones de fases
  - Coherencia comprometida gradualmente
  - Errores detectados tarde

DESPUÉS (con NIGREDO inyectable):
  - Cada petición validada automáticamente
  - Errores detectados INMEDIATAMENTE
  - Coherencia mantenida constantemente
  - Saltaciones prevenidas antes de ocurrir
```

---

**NIGREDO INYECTABLE = COHERENCIA GARANTIZADA EN CADA PETICIÓN**
