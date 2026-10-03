# 🔍 DIAGNÓSTICO ESTRUCTURAL: Por Qué Todo Está Desalineado

**Fecha**: Abril 18, 2026  
**Responsable**: Copilot (auto-diagnosticándose)  
**Problema**: Contaminación terminológica + organización inconsistente  

---

## ❌ PROBLEMA IDENTIFICADO

### 1. CONTAMINACIÓN TERMINOLÓGICA (Esotérico ↔ Pragmático Mezclado)

```
ANTES (CORRECTO):
┌─────────────────────────────────────┐
│ CAPA ESOTÉRICA (Golem + rituales)   │  ← Depurable
│ ┌────────────────────────────────┐  │
│ │ CAPA PRAGMÁTICA (COMPUTADORA)  │  │  ← MANTENER intacta
│ │ ├─ core/main.py                │  │
│ │ ├─ nlp/engine.py (Comandos)    │  │
│ │ └─ search/verified_search.py   │  │
│ └────────────────────────────────┘  │
└─────────────────────────────────────┘

AHORA (CONTAMINADA):
┌─────────────────────────────────────┐
│ "Grimorio" + "Golem" mezclados con  │
│ "Computadora" y "Comandos"          │
│ ❌ Imposible depurar uno sin        │
│    tocar el otro                    │
└─────────────────────────────────────┘
```

### 2. PROBLEMAS ESPECÍFICOS

```
❌ TERMINOLOGÍA:
   - Llamo "Grimorio" cuando debo usar "Búsqueda de Computadora"
   - Llamo "Golem" cuando debo usar "Sistema" o "Núcleo"
   - Llamo "Palabras Mágicas" cuando debo usar "Comandos"
   - Llamo "Akathoth" cuando debo usar "Database" o "Storage"
   
   EFECTO: Usuario no puede depurar esotérico sin afectar pragmático

❌ ORGANIZACIÓN:
   - Creo archivos en raíz (CERTIFICACION_99_100_COHERENCIA.md)
   - Debería estar en _docs/ (FP-CERTIFICACION_99_100_COHERENCIA.md)
   - Creo PALINGENESIA_CICLO_99_100_FINAL.md en raíz
   - Debería estar en _archive/CICLOS/PALINGENESIA_CICLO_99_100_FINAL.md
   
   EFECTO: Raíz desordenada, estructura inmutable violada

❌ REFERENCIAS:
   - Documento habla de "PM #20 verifica (EMET)"
   - Debería hablar de "Comando #20 'verifica' (coherencia check)"
   - Mapeo EMET→Comandos nunca fue formalizado
   
   EFECTO: Imposible saber si documentación refiere a código o ritual
```

---

## ✅ SOLUCIÓN: SEPARACIÓN CLARA CAPAS

### Mapeo Esotérico → Pragmático (FORMAL)

| Concepto Esotérico | Concepto Pragmático | Ubicación Código | Documentación |
|---|---|---|---|
| **Golem** | COMPUTADORA v2.0 (Sistema) | `computadora/` | `_docs/README.md` |
| **Grimorio** | Search Module + Database | `computadora/search/` | `_docs/SDD.md` |
| **Akathoth** | Persistencia + Cache | `computadora/storage/` | `_docs/SDD.md` |
| **Palabras Mágicas (PM)** | Comandos | `computadora/nlp/commands/` | `_docs/COMANDOS.md` (nuevo) |
| **EMET** | Verificación Coherencia | `tests/` | `_docs/TESTING.md` |
| **Sefirot** | 7 Capas Arquitectura | `computadora/` dirs | `_docs/ARCHITECTURE.md` |
| **Rituales (WI)** | Ciclos de Desarrollo | Git history | `_docs/WORKFLOW_OPERACIONAL.md` |
| **Alquimia (Fases)** | Proceso NIGREDO→RUBEDO | Tracker | `_docs/TRACKER_ALQUIMICO_ESTADO_PM_FP.md` |

### Archivos Desorganizados (Encontrados en Raíz)

```
❌ RAÍZ (No deberían estar aquí):
   - CERTIFICACION_99_100_COHERENCIA.md → _docs/REPORTS/CERTIFICACION_99_100.md
   - PALINGENESIA_CICLO_99_100_FINAL.md → _archive/CICLOS/PALINGENESIA_99_100.md
   - ALBEDO_INVESTIGACION_SUGERENCIAS_GATE2.md → _docs/FP-BATCH9_INVESTIGACION_ALBEDO.md
   - FP-ARQUITECTURA_ALINEACION_ALQUIMICA.md → _docs/ARCHITECTURE/ALINEACION_ALQUIMICA.md
   - TRACKER_ALQUIMICO_ESTADO_PM_FP.md → .management/TRACKER_ESTADO_TRABAJOS.md
   
✅ DESTINO CORRECTO (según WORKFLOW_OPERACIONAL.md):
   - Reportes de auditoría → _docs/REPORTS/
   - Ciclos cerrados → _archive/CICLOS/
   - Investigaciones → _docs/FP-*/
   - Arquitectura → _docs/ARCHITECTURE/
   - Gestión de tareas → .management/

RAÍZ debe contener solo:
   - README.md (project info)
   - WORKFLOW_OPERACIONAL.md (guía operativa)
   - WorkItems.md (tareas vivas)
   - config files (pyproject.toml, etc)
   - CONSTITUCIÓN (si es central)
```

---

## 🔧 PLAN DE REMEDIACIÓN (5 Pasos)

### PASO 1: Crear Mapeo Formal (Hoy)
- Documento: `_docs/ARCHITECTURE/CAPAS_ESOTERICO_PRAGMATICO.md`
- Contenido: Tabla mapeo completa + regla "nunca mezclar"

### PASO 2: Reorganizar Archivos (Hoy)
```
FP-ARQUITECTURA_ALINEACION_ALQUIMICA.md
  → _docs/ARCHITECTURE/ALINEACION_ALQUIMICA.md

TRACKER_ALQUIMICO_ESTADO_PM_FP.md
  → .management/TRACKER_ESTADO_TRABAJOS.md

CERTIFICACION_99_100_COHERENCIA.md
  → _docs/REPORTS/CERTIFICACION_99_100_COHERENCIA.md

Otros .md en raíz → Revisar cada uno
```

### PASO 3: Actualizar Referencias (Hoy)
- Todos los documentos que hablen de "Golem/Grimorio" en contexto de COMPUTADORA
- Cambiar terminología a "Sistema/Search Module"
- Mantener términos esotéricos SOLO en documentación histórica

### PASO 4: Crear Guía "Comandos vs PM" (Hoy)
- Documento: `_docs/COMANDOS.md`
- Mapeo: PM/comando esotérico → comando pragmático
- Quien usa qué en qué contexto

### PASO 5: Validar Estructura (Hoy)
- Confirmar que raíz solo tiene archivos permitidos
- Confirmar que _docs/ tiene estructura clara
- Confirmar que documentación usa terminología consistente

---

## 📊 ESTRUCTURA CORRECTA DESPUÉS DE REMEDIACIÓN

```
proyecto-golem/
├── README.md                          ← Info proyecto
├── WORKFLOW_OPERACIONAL.md            ← Guía de acción (1 página)
├── WorkItems.md                       ← Tareas vivas
│
├── computadora/                       ← CÓDIGO PRAGMÁTICO
│   ├── core/
│   ├── nlp/
│   ├── search/
│   └── ...
│
├── tests/                             ← VALIDACIÓN
│   ├── test_*.py
│   └── ...
│
├── _docs/                             ← DOCUMENTACIÓN ORGANIZAD
│   ├── README.md                      ← Índice docs
│   ├── SRS.md                         ← Requisitos
│   ├── SDD.md                         ← Diseño técnico
│   ├── SECURITY_PLAN.md               ← Seguridad
│   ├── TESTING_CHECKLISTS.md          ← Testing
│   ├── COMANDOS.md                    ← ✨ NUEVO: Mapeo esotérico→pragmático
│   ├── ARCHITECTURE/
│   │   ├── CAPAS_ESOTERICO_PRAGMATICO.md    ← ✨ NUEVO
│   │   ├── ALINEACION_ALQUIMICA.md
│   │   └── ...
│   ├── FP-*/                          ← Feature Plans
│   │   ├── FP-BATCH9_INVESTIGACION_ALBEDO.md
│   │   └── ...
│   ├── REPORTS/                       ← ✨ NUEVO
│   │   ├── CERTIFICACION_99_100_COHERENCIA.md
│   │   └── ...
│   ├── GATE2_APPROVAL_*.md
│   └── ...
│
├── _archive/                          ← Ciclos cerrados
│   ├── CICLOS/                        ← ✨ NUEVO
│   │   ├── PALINGENESIA_99_100.md
│   │   └── ...
│   └── ...
│
├── .management/                       ← Gestión de tareas
│   ├── TRACKER_ESTADO_TRABAJOS.md     ← ✨ NUEVO (movido)
│   └── TASKS.md
│
└── ... otros dirs
```

---

## 🚨 REGLAS INVIOLABLES NUEVA ESTRUCTURA

```
REGLA 1: Terminología Limpia
- Si hablo de código/API → Uso "Computadora", "Sistema", "Comando"
- Si hablo de historia/conceptos → Puedo usar "Golem", "Grimorio", etc
- NUNCA mezclo en mismo párrafo

REGLA 2: Ubicación de Archivos
- Archivos .md de documentación → _docs/ o subdirs
- Archivos de ciclos cerrados → _archive/
- Archivos de gestión → .management/
- Raíz: solo INFO, WORKFLOW, TASKS, CONFIG

REGLA 3: Referencias Cruzadas
- Si documento habla de código → linkea a _docs/SDD.md o archivo código
- Si documento habla de proceso → linkea a _docs/WORKFLOW_OPERACIONAL.md
- Nunca ambigüedad: "este es código o ritual?"

REGLA 4: Versionado
- Documentación oficial → _docs/
- Versiones cerradas → _archive/
- Estado actual → .management/TRACKER_*

REGLA 5: Copilot Cumple
- Validar ubicación antes de crear archivo
- Validar terminología antes de escribir
- Si dudo → preguntar usuario antes de crear
```

---

## 📋 CHECKLIST REMEDIACIÓN (HOY)

- [ ] Crear `_docs/ARCHITECTURE/CAPAS_ESOTERICO_PRAGMATICO.md`
- [ ] Crear `_docs/COMANDOS.md` (mapeo PM → Comandos)
- [ ] Mover `FP-ARQUITECTURA_*` → `_docs/ARCHITECTURE/`
- [ ] Mover `TRACKER_ALQUIMICO_*` → `.management/TRACKER_ESTADO_TRABAJOS.md`
- [ ] Mover `CERTIFICACION_99_100_*` → `_docs/REPORTS/`
- [ ] Mover `PALINGENESIA_CICLO_*` → `_archive/CICLOS/`
- [ ] Mover `ALBEDO_INVESTIGACION_*` → `_docs/FP-BATCH9_INVESTIGACION_ALBEDO.md`
- [ ] Limpiar raíz (confirmar solo archivos permitidos)
- [ ] Actualizar referencias en documentos modificados
- [ ] Crear documento "Status Remediación" para cierre

---

**PRÓXIMO**: Ejecutar remediación. ✅

