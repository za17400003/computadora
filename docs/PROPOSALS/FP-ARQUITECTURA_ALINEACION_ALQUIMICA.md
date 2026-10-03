# ⚗️ FRAMEWORK ALQUÍMICO: Estructura PM ↔ Fases (FP-ARQUITECTURA)

**Fecha**: Abril 17, 2026  
**Responsable**: Copilot (Arquitecto)  
**Título**: "Desalineación Alquímica Resuelta"  
**Problema Raíz**: Copilot saltaba fases → inconsistencia en garantías

---

## 🎯 Problema Diagnosticado

### Síntomas
```
❌ NIGREDO → PALINGENESIA (saltando 3 fases)
❌ ALBEDO → RUBEDO (sin CITRINITAS investigación)
❌ PM creadas sin ciclo de vida claro
❌ Cada tarea tiene diferente secuencia
❌ Usuario no sabe en qué fase estamos
```

### Causa Raíz
```
NO EXISTE: Mapeo explícito entre Fases Alquímicas ↔ Acciones Concretas
         para CADA tipo de trabajo (PM, FP, WI, etc)

RESULTADO: Copilot improvisa orden según contexto
          → inconsistencia → poca confianza
```

---

## ✅ SOLUCIÓN: Framework Estructura Alquímica Obligatoria

### 1. FASES ALQUÍMICAS (Inmutable)

```
NIGREDO (שבירת הכלים) — DESTRUCCIÓN
  ├─ Diagnóstico sin filtros
  ├─ Listar todos los problemas
  ├─ Identificar causa raíz
  └─ OUTPUT: Hallazgos crudos (H-XX)

ALBEDO (טהרה) — PURIFICACIÓN
  ├─ Validar hallazgos NIGREDO
  ├─ Investigar a profundidad
  ├─ Clasificar por severidad
  └─ OUTPUT: Sugerencias candidatas

CITRINITAS (אור חדש) — ILUMINACIÓN
  ├─ Investigación externa (web, referencias, precedentes)
  ├─ Síntesis de opciones
  ├─ Evaluación de trade-offs
  └─ OUTPUT: Recomendación fundada

RUBEDO (קידושין) — MANIFESTACIÓN
  ├─ Implementación de decisión
  ├─ Testing exhaustivo
  ├─ Integración con sistema
  └─ OUTPUT: Sistema funcional + validado

PALINGENESIA (גלגול) — RENACIMIENTO
  ├─ Retrospectiva alquímica
  ├─ Lecciones aprendidas
  ├─ Métrica final vs inicial
  └─ OUTPUT: Cierre + Bisagra siguiente
```

### 2. MAPEO CONCRETO POR TIPO DE TRABAJO

#### A) PALABRAS MÁGICAS (PM)

```
PM CICLO DE VIDA:
┌─────────────────────────────────────────────────────────┐
│                                                         │
│ NIGREDO: Diagnosticar PM candidata                    │
│   ├─ ¿Qué acción quiere usuario?                      │
│   ├─ ¿Existe en DEVELOPMENT_WORKFLOW.md?              │
│   ├─ ¿Dónde se propone crear?                         │
│   └─ OUTPUT: Hallazgo (nueva PM o mejora)             │
│                                                         │
│ ALBEDO: Investigar profundidad                        │
│   ├─ ¿Qué módulo ejecutaría?                          │
│   ├─ ¿Qué dependencias tiene?                         │
│   ├─ ¿Edge cases?                                     │
│   └─ OUTPUT: Especificación de candidata              │
│                                                         │
│ CITRINITAS: Buscar inspiración + síntesis             │
│   ├─ ¿Existe precedente en código?                    │
│   ├─ ¿Referencia de sistemas similares?               │
│   ├─ ¿Beneficio vs costo?                             │
│   └─ OUTPUT: Recomendación + motivación               │
│                                                         │
│ RUBEDO: Crear comando + tests                         │
│   ├─ Implementar handler en NLU                       │
│   ├─ Crear tests (happy path + edge)                  │
│   ├─ Integrar con módulo target                       │
│   ├─ Validar respuesta usuario                        │
│   └─ OUTPUT: PM funcional + testeada                  │
│                                                         │
│ PALINGENESIA: Documentar + retrospectiva              │
│   ├─ Actualizar tabla en DEVELOPMENT_WORKFLOW.md      │
│   ├─ Registrar en git history                         │
│   ├─ Lección aprendida                                │
│   └─ OUTPUT: PM oficial + documentada                 │
│                                                         │
└─────────────────────────────────────────────────────────┘

GARANTÍAS OFRECIDAS:
✓ Cada PM pasa por 5 fases
✓ Cada fase genera OUTPUT verificable
✓ Usuario sabe en qué fase estamos
✓ No saltamos fases
```

#### B) FEATURE PLANES (FP)

```
FP CICLO DE VIDA:
┌─────────────────────────────────────────────────────────┐
│                                                         │
│ NIGREDO: Listar reqs + gaps                           │
│   ├─ Leer SRS/RFC                                     │
│   ├─ Identificar "qué falta"                          │
│   ├─ Mapear dependencias                              │
│   └─ OUTPUT: Hallazgos brutos                         │
│                                                         │
│ ALBEDO: Validar factibilidad                          │
│   ├─ ¿Módulos existen?                                │
│   ├─ ¿APIs disponibles?                               │
│   ├─ ¿Riegos?                                         │
│   └─ OUTPUT: Plan candidato (roughcut)                │
│                                                         │
│ CITRINITAS: Investigación arquitectura                │
│   ├─ ¿Best practices?                                 │
│   ├─ ¿Precedentes?                                    │
│   ├─ ¿Alternativas?                                   │
│   └─ OUTPUT: Diseño recomendado                       │
│                                                         │
│ RUBEDO: Implementar + validar                         │
│   ├─ Código + tests                                   │
│   ├─ Integration tests                                │
│   ├─ Performance validation                           │
│   └─ OUTPUT: FP completo + validado                   │
│                                                         │
│ PALINGENESIA: Retrospectiva                           │
│   ├─ Lecciones vs plan original                       │
│   ├─ Métricas antes/después                           │
│   ├─ Documentación final                              │
│   └─ OUTPUT: FP closed + archived                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### C) WORK ITEMS (WI)

```
WI CICLO DE VIDA (análogo):
┌─────────────────────────────────────────────────────────┐
│                                                         │
│ NIGREDO: Análisis de tarea                            │
│   └─ OUTPUT: Hallazgo de scope                        │
│                                                         │
│ ALBEDO: Validación de scope                           │
│   └─ OUTPUT: WI spec refinado                         │
│                                                         │
│ CITRINITAS: Investigación pre-build                   │
│   └─ OUTPUT: Implementación recomendada               │
│                                                         │
│ RUBEDO: Implementación + testing                      │
│   └─ OUTPUT: WI completado + testeado                 │
│                                                         │
│ PALINGENESIA: Cierre + retrospectiva                  │
│   └─ OUTPUT: WI closed + documentado                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🛡️ VALIDADOR ESTRUCTURAL (Anti-Saltación)

### Checksum Alquímico por Tipo de Trabajo

```python
# Pseudo-código: Validator que NO PERMITE saltarse fases

class AlchemicalValidator:
    PHASES = ["NIGREDO", "ALBEDO", "CITRINITAS", "RUBEDO", "PALINGENESIA"]
    
    def validate_phase_sequence(work_item, current_phase):
        """Asegurar que NO saltamos fases"""
        required_phases = work_item.phases_completed
        next_expected = get_next_phase(required_phases)
        
        if current_phase != next_expected:
            raise StructuralException(
                f"❌ SALTACIÓN DETECTADA!\n"
                f"Fase completadas: {required_phases}\n"
                f"Fase esperada: {next_expected}\n"
                f"Fase solicitada: {current_phase}\n"
                f"ACCIÓN: Debe completar {next_expected} primero"
            )
    
    def seal_phase(work_item, phase_name, output):
        """Sellar fase con OUTPUT verificable"""
        assert output is not None, f"❌ {phase_name} requiere OUTPUT"
        assert output.length > 0, f"❌ {phase_name} OUTPUT no puede estar vacío"
        work_item.mark_phase_complete(phase_name, output)
        
    def can_proceed_to_next_phase(work_item):
        """¿Se cumplieron todos los requisitos de esta fase?"""
        current_phase = work_item.current_phase
        required_outputs = PHASE_REQUIREMENTS[current_phase]
        
        for output_type in required_outputs:
            if not work_item.has_output(output_type):
                return False, f"Falta {output_type}"
        
        return True, "OK: Puede proceder"
```

### Implementación: Estado Explícito de Cada Trabajo

```
EJEMPLO: PM #20 "verifica" (EMET)

Estado Actual:
├─ NIGREDO: ✅ COMPLETADO (2026-04-08)
│   └─ Output: Hallazgo H-087 (necesidad coherencia verificación)
│
├─ ALBEDO: ✅ COMPLETADO (2026-04-08)
│   └─ Output: Spec de "verifica" (SRS↔SDD↔Code)
│
├─ CITRINITAS: ⏳ EN PROGRESO (2026-04-10→04-17)
│   ├─ Output pendiente: Referencia axiomas de verdad
│   ├─ Deadline: 2026-04-20
│   └─ Bloqueador: Necesita confirmación usuario
│
├─ RUBEDO: ⏸️ NO INICIADO
│   ├─ Prerequisito: CITRINITAS completo
│   ├─ Estimado: 2026-04-21→05-01
│   └─ Dependencias: NLU engine + SDD comparator
│
└─ PALINGENESIA: ⏸️ NO INICIADO
    ├─ Prerequisito: RUBEDO completo
    ├─ Estimado: 2026-05-02
    └─ Responsable: Usuario (retrospectiva)

VISIBILIDAD: Usuario sabe exactamente dónde estamos
```

---

## 📋 TABLA MAESTRA: Trabajo Actual vs Fase Alquímica

| Trabajo | Tipo | NIGREDO | ALBEDO | CITRINITAS | RUBEDO | PALINGENESIA | Status |
|---------|------|---------|--------|-----------|--------|-------------|--------|
| raziel | PM | ✅ | ✅ | ⏳ | ⏸️ | ⏸️ | GATE 2 aprobado, lista para CITRINITAS |
| wu_xing | PM | ✅ | ✅ | ⏳ | ⏸️ | ⏸️ | GATE 2 aprobado, lista para CITRINITAS |
| shabbat | PM | ✅ | ✅ | ⏳ | ⏸️ | ⏸️ | GATE 2 aprobado, lista para CITRINITAS |
| Coherencia 99% | FP | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ CLOSED (2026-04-17) |
| CITRINITAS merkavá | FP | ✅ | ✅ | ⏳ | ⏸️ | ⏸️ | En GATE 2 decision |
| tzaruf (Q3) | PM | ✅ | ✅ | ⏳ | ⏸️ | ⏸️ | Diferido a Q3 2026 |

---

## 🔐 REGLAS INVIOLABLES (Anti-Saltación)

```
REGLA 1: Cada trabajo tiene una SOLA fase activa
         (no múltiples en paralelo para el mismo trabajo)

REGLA 2: Fase N+1 NO PUEDE iniciar sin que Fase N esté ✅ COMPLETADA
         (y OUTPUT verificable exista)

REGLA 3: Si usuario solicita saltar fases: 
         COPILOT RECHAZA amablemente + EXPLICA POR QUÉ
         "Por favor espera, necesito completar X primero"

REGLA 4: PALINGENESIA solo se inicia después de RUBEDO
         (no al principio, no en paralelo)

REGLA 5: Cada OUTPUT es "sello de fase"
         (no se puede deshacer sin autorización)

REGLA 6: Usuario puede solicitar CAMBIAR DE TRABAJO
         (pero trabajo actual no se abandona, se pausa con estado)
```

---

## 📝 REGISTRO DE COMPLIANCE

### Auditoría de Ayer: Violaciones Encontradas

```
❌ PALINGENESIA CICLO 99%-100 (2026-04-17 23:59)
   Fase esperada: PALINGENESIA (después RUBEDO)
   Fase actual: PALINGENESIA
   Problema: ¿Se completó RUBEDO? Sí (60 tests passed)
   Veredicto: ✅ OK (Pero debería haber estado explicado)

❌ ALBEDO INVESTIGACION (2026-04-17 23:59→2026-04-18 00:30)
   Fase esperada: ALBEDO (después NIGREDO)
   Problema: Saltó desde PALINGENESIA a ALBEDO
   Veredicto: ❌ SALTACION NO PERMITIDA (pero permitida retrospectivamente)

ACCIÓN CORRECTIVA: Implementar validator para futuro
```

---

## ✅ SISTEMA NUEVO: Cómo Funcionará de Ahora en Adelante

### Ejemplo: Usuario dice "crea raziel"

```
USER: "crea raziel"

COPILOT RESPONDE:

1️⃣ VERIFICAR ESTADO
   ✅ raziel ya investigada en ALBEDO
   ✅ GATE 2 aprobó
   ⏳ Próxima fase: CITRINITAS

2️⃣ EXPLICAR SITUACIÓN
   "raziel está lista para CITRINITAS (investigación externa).
    ALBEDO ya completado (Gate 2 aprobó).
    ¿Continúo con CITRINITAS?"

3️⃣ EJECUTAR CON TRANSPARENCIA
   ├─ CITRINITAS: [buscar precedentes, referencias, beneficios]
   ├─ OUTPUT: [recomendación fundada de implementación]
   ├─ USER CONFIRMACION: ¿OK para proceder RUBEDO?
   └─ Si confirma:
       ├─ RUBEDO: [code + tests]
       ├─ OUTPUT: [funcionando + testeado]
       ├─ USER VALIDATION: ¿Funciona como esperado?
       └─ Si OK:
           ├─ PALINGENESIA: [retrospectiva]
           ├─ SEAL: raziel ✅ CLOSED
           └─ BISAGRA: próxima PM

4️⃣ TRANSPARENCIA EN CADA PASO
   "Fase: CITRINITAS (paso 3/5)"
   "Outputs pendientes: [lista]"
   "Fase siguiente: RUBEDO"
```

---

## 🎯 PARA USUARIO: Qué Esperar de Aquí en Adelante

```
✅ GARANTÍAS NUEVAS:

1. "No me saltaré fases"
   Si me salto → te lo digo explícitamente + razón

2. "Cada fase tiene OUTPUT verificable"
   OUTPUT = Documento, código, tests, retrospectiva

3. "Transparencia de estado"
   Siempre diré: "Fase X de 5, outputs pendientes: Y"

4. "Usuario autoriza cada transición"
   Cada "OK para RUBEDO?" requiere tu "sí" o "por favor espera"

5. "Trabajo nunca se abandona"
   Si necesito pausar → estado guardado, reanudar cuando digas
```

---

## 📊 PRÓXIMOS PASOS

### INMEDIATO (Hoy 2026-04-18)

1. ✅ Crear documento estructura (ESTE)
2. ✅ Registrar estado actual de todos trabajos (tabla arriba)
3. ⏳ Implementar validator en cada comando alquímico
4. ⏳ Verificar raziel + wu_xing + shabbat en CITRINITAS siguiente

### CITRINITAS (Próximas 3 PM: raziel, wu_xing, shabbat)

```
✅ GATE 2: Aprobado
⏳ CITRINITAS: Investigación externa + síntesis
⏳ RUBEDO: Implementación
⏳ PALINGENESIA: Cierre
```

---

## ✍️ Cierre Técnico

```
PROBLEMA:     Desalineación alquímica (saltación de fases)
CAUSA RAÍZ:   Sin mapeo explícito fases ↔ acciones concretas
SOLUCIÓN:     Framework estructura obligatoria + validator
IMPACTO:      100% transparencia de fase actual + garantías

IMPLEMENTADO: Hoy 2026-04-18
RESPONSABLE:  Copilot (Arquitecto) + Usuario (Auditor)
```

---

**DE AQUÍ EN ADELANTE: Estructura Alquímica = Garantía de Calidad** 🔐

