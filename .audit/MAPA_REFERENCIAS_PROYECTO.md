# MAPA DE REFERENCIAS DEL PROYECTO — Auditoría de Coherencia

**Fecha**: Abril 17, 2026  
**Propósito**: Index completo de dónde vive cada concepto, módulo y archivo crítico  
**Estado**: 🔴 INCOMPLETO — en construcción durante auditoría  

---

## I. ESTRUCTURA DE DIRECTORIOS CRÍTICA

```
proyecto-golem/
├── computadora/                          # Sistema principal (v2.0 pragmático)
│   ├── core/main.py                     # Bootstrap <10s, JARVIS-ready
│   ├── canales/servidor_api.py          # API HTTP para Minimi (funciones críticas)
│   ├── nlp/engine.py                    # NLU y procesamiento de comandos
│   ├── percepcion/                      # Sentidos del Golem (Ayin, Ozen, Peh)
│   ├── voz/                             # Habla y escucha (TTS/STT)
│   ├── seguridad/                       # Ciberseguridad (EyotIDS, RatzonBehavior, GevurahTikun)
│   └── nucleo/                          # Centro neurálgico
│       ├── emet.py                      # Verdad del Golem (identidad, arquitectura)
│       └── proactividad.py              # Ciclo circadiano y autonomía
│
├── ENCICLOPEDIA/                         # Sistema educativo (18 capítulos)
│   ├── servidor_enciclopedia.py         # Servidor HTTP con autenticación AES
│   ├── iniciar_enciclopedia.bat         # Script de arranque
│   ├── cap01_kabbalah.html → cap18_matematicas.html
│   └── guia_iniciacion.html             # Guía de uso
│
├── tests/                                # Suite de validación
│   ├── test_axiomas_formal.py           # Tests de los 5 axiomas (pre-Framework)
│   ├── test_coherencia_formal.py        # Tests de validación formal (PENDIENTE)
│   └── test_*.py                        # Otros tests por módulo
│
├── _docs/                                # Documentación arquitectónica
│   ├── DEVELOPMENT_WORKFLOW_REFERENCIA.md  # Flujo operacional (axiomas, gates, pipelines)
│   ├── SRS.md                           # Especificaciones funcionales
│   ├── SDD.md                           # Diseño detallado
│   ├── SECURITY_PLAN.md                 # Plan de seguridad
│   └── *.md                             # Otros docs
│
├── FRAMEWORK_LENGUAJES_Y_AUTOMATAS.md   # Teoría formal (300+ líneas)
├── AXIOMAS_CORREGIDOS_LENGUAJES_FORMALES.md  # Axiomas III.7-III.11 formalizados
└── AUDITORIA_COHERENCIA_EN_VIVO.md      # Este documento de diagnóstico
```

---

## II. MAPEO DE CONCEPTOS A UBICACIÓN

### A. AXIOMAS FORMALES (III.7-III.11)

| Axioma | Definición Formal | Ubicación | Tests |
|--------|-------------------|-----------|-------|
| III.7  | $m \in L \Leftrightarrow EMET(m) = V$ | FRAMEWORK §I, AXIOMAS_CORREGIDOS §III.7 | test_axiomas_formal.py:test_axioma_7 |
| III.8  | $\forall m: \|\delta^*(q_0, m)\| = 1$ | FRAMEWORK §II, AXIOMAS_CORREGIDOS §III.8 | test_axiomas_formal.py:test_axioma_8 |
| III.9  | $fallo \Rightarrow \exists m' \in L$ | FRAMEWORK §III, AXIOMAS_CORREGIDOS §III.9 | test_axiomas_formal.py:test_axioma_9 |
| III.10 | $(m_1 \in L \land m_2) \Rightarrow (m_1 \cdot m_2) \in L$ | FRAMEWORK §IV, AXIOMAS_CORREGIDOS §III.10 | test_axiomas_formal.py:test_axioma_10 |
| III.11 | $\forall N: (\bigwedge_i EMET(m_i)=V) \Rightarrow$ | FRAMEWORK §V, AXIOMAS_CORREGIDOS §III.11 | test_axiomas_formal.py:test_axioma_11 |

### B. COMPONENTES CRÍTICOS Y SUS UBICACIONES

| Componente | Archivo | Funciones Clave | Responsabilidad |
|-----------|---------|-----------------|-----------------|
| **NLU Engine** | `computadora/nlp/engine.py` | `process()`, `parse()` | Procesa comandos y los mapea a herramientas |
| **Servidor API** | `computadora/canales/servidor_api.py` | `_estado_golem()`, `_iniciar_enciclopedia_lan()` | Expone estado y funcionalidad vía HTTP a Minimi |
| **Enciclopedia** | `ENCICLOPEDIA/servidor_enciclopedia.py` | `verify_password()`, `run_server()` | Sirve contenido educativo cifrado con autenticación |
| **EMET Verdad** | `computadora/nucleo/emet.py` | `generar_manifiesto()` | Genera manifiesto de verdad del Golem |
| **Seguridad** | `computadora/seguridad/*.py` | EyotIDS, RatzonBehavior, GevurahTikun | Ciberseguridad, detección de anomalías, respuesta |
| **Proactividad** | `computadora/nucleo/proactividad.py` | `obtener_fase_actual()` | Ciclo circadiano y autonomía |

### C. FLUJOS OPERACIONALES (Pipelines A-E)

| Pipeline | Deptos | Descripción | Ubicación en Docs |
|----------|--------|-------------|-------------------|
| **A** | D1+D3+D4+D5+D6+D7 | Feature nueva (5 fases completas) | DEVELOPMENT_WORKFLOW.md §Pipelines |
| **B** | D1+D3+D4 | Mejora UX | DEVELOPMENT_WORKFLOW.md §Pipelines |
| **C** | D4 | Bug fix (directo a RUBEDO) | DEVELOPMENT_WORKFLOW.md §Pipelines |
| **D** | D2+D5+D6+D7 | Decisión de negocio | DEVELOPMENT_WORKFLOW.md §Pipelines |
| **E** | D1+D4+D7 | Cambio de arquitectura | DEVELOPMENT_WORKFLOW.md §Pipelines |

### D. GATES DE VALIDACIÓN (Sefirot)

| Gate | Sefirá | Validator | Ubicación | Responsabilidad |
|------|--------|-----------|-----------|-----------------|
| Gate 0 | Keter | `_gate_0_clasificacion()` | servidor_api.py | Clasificar pipeline |
| Gate 1 | Biná | `_gate_1_evaluacion()` | servidor_api.py | Evaluar factibilidad |
| Gate 1.3 | Gevurá | `_gate_1_3_verificador_enciclopedia()` | servidor_api.py | Verificar conocimiento requerido |
| Gate 1.5 | Tiféret | `_gate_1_5_balance()` | servidor_api.py | Balance arquitectónico |
| Gate 2 | Ratzón | `_gate_2_propietario()` | servidor_api.py | Decisión del Propietario |
| Gate 3 | Maljut | `_gate_3_manifestacion()` | servidor_api.py | Manifestación en git |

### E. TRÍADA (Grimorio→Minimi→Golem)

| Sistema | Root Dir | Scripts | Estado | Referencias |
|---------|----------|---------|--------|-------------|
| **Enciclopedia** | `ENCICLOPEDIA/` | `servidor_enciclopedia.py`, `iniciar_enciclopedia.bat` | 🟢 Activo | DEVELOPMENT_WORKFLOW.md línea 2154 |
| **Minimi** | `C:\Users\woire\AndroidStudioProjects\Minimi\` | Android Studio | 🟠 Parcial | WorkItems.md, FP-095 |
| **Golem** | `computadora/` | `computadora/core/main.py` | 🟢 Activo | README_COMPUTADORA.md |

---

## III. REFERENCIAS CRUZADAS CRÍTICAS

### A. "Grimorio" vs "Enciclopedia" — INCONSISTENCIA ENCONTRADA

| Archivo | Contexto | Problema | Solución |
|---------|----------|----------|----------|
| `ENCICLOPEDIA/iniciar_grimorio.bat` | Nombre del script | ❌ Nombrado "grimorio" pero en dir "ENCICLOPEDIA" | ✅ Renombrado a `iniciar_enciclopedia.bat` |
| `ENCICLOPEDIA/servidor_grimorio.py` | Servidor principal | ❌ Nombrado "grimorio" pero en dir "ENCICLOPEDIA" | 🔄 PENDIENTE: `servidor_enciclopedia.py` |
| `computadora/canales/servidor_api.py:580` | Función interna | ❌ `_iniciar_grimorio_lan()` | 🔄 PENDIENTE: `_iniciar_enciclopedia_lan()` |
| `_docs/SRS.md:2994-3000` | Documentación | ❌ Referencias a "servidor_grimorio" | 🔄 PENDIENTE: Actualizar a "servidor_enciclopedia" |

### B. Archivos Faltantes para Auditoría Formal

| Archivo | Propósito | Estado | Prioridad |
|---------|----------|--------|-----------|
| `tests/test_coherencia_formal.py` | Validar L, DFA, EMET, Axiomas | ❌ NO EXISTE | 🔴 CRÍTICO |
| `tests/test_composicion_inductiva.py` | Probar Axioma III.11 (inducción) | ❌ NO EXISTE | 🟠 ALTO |
| `MAPA_REFERENCIAS_PROYECTO.md` | Este índice completo | ⏳ EN CONSTRUCCIÓN | 🟠 ALTO |
| `METRICAS_COHERENCIA.json` | Checksums, commits, estado | ❌ NO EXISTE | 🟡 MEDIO |
| `AUDITORIA_FORMAL_COMPLETA.md` | Manifest de auditoría | ❌ NO EXISTE | 🟡 MEDIO |

### C. Referencia de "progreso" y "lockout"

| Concepto | Archivo Data | Ubicación en Código | Semántica |
|----------|--------------|-------------------|-----------|
| Progreso de lectura | `datos/grimorio_progreso.json` | `servidor_grimorio.py:l76` | 🔄 PENDIENTE cambio a `enciclopedia_progreso.json` |
| Lockout de acceso | `datos/grimorio_lockout.json` | `servidor_grimorio.py:l85` | 🔄 PENDIENTE cambio a `enciclopedia_lockout.json` |
| Log de intrusiones | `datos/grimorio_intrusiones.jsonl` | `servidor_grimorio.py:l72` | 🔄 PENDIENTE cambio a `enciclopedia_intrusiones.jsonl` |

---

## IV. VALIDACIÓN DE COHERENCIA

### A. Checklists de Coherencia

- [ ] ✅ Léxico: Todos los términos tienen definición formal (FRAMEWORK_LENGUAJES_Y_AUTOMATAS.md §VII)
- [ ] ✅ Sintaxis: Gramática Type 2 (CFG) completa (FRAMEWORK §I)
- [ ] ✅ Semántica: Significado vía autómatas y 3-valued logic (FRAMEWORK §IV)
- [ ] ❌ Nomenclatura: Grimorio/Enciclopedia — FALTA UNIFICACIÓN
- [ ] ❌ Tests Formales: Validadores de L, DFA, EMET — NO EXISTEN
- [ ] ❌ Mapa Completo: Referencias cruzadas documentadas — PARCIAL
- [ ] ❌ Métricas: Checksums y estado documentado — NO EXISTE

### B. Problemas Identificados (7 Total)

| ID | Problema | Severidad | Ubicación | Fix |
|----|----------|-----------|-----------|-----|
| P1 | Nomenclatura inconsistente Grimorio/Enciclopedia | 🔴 CRÍTICO | ENCICLOPEDIA/, servidor_api.py | Renombramientos |
| P2 | Archivos data con nombres "grimorio" | 🟠 ALTO | `datos/*.json` | Renombramientos |
| P3 | Tests formales faltantes para Axiomas | 🟠 ALTO | `tests/` | Crear test_coherencia_formal.py |
| P4 | Mapa de referencias incompleto | 🟡 MEDIO | Este archivo | Completar index |
| P5 | SRS.md referencias desactualizadas | 🟡 MEDIO | `_docs/SRS.md` | Actualizar líneas 2994-3000 |
| P6 | Métricas de coherencia no documentadas | 🟡 MEDIO | No existe | Crear METRICAS_COHERENCIA.json |
| P7 | Manifest de auditoría no existe | 🟡 MEDIO | No existe | Crear AUDITORIA_FORMAL_COMPLETA.md |

---

## V. PLAN DE REMEDIACIÓN (Continuación Fase 2)

### Must-Have (Bloquea auditoría)

- [ ] Crear `servidor_enciclopedia.py` (renombrado desde servidor_grimorio.py)
- [ ] Actualizar `computadora/canales/servidor_api.py` — todas las referencias
- [ ] Actualizar `_docs/SRS.md` — todas las referencias a "servidor_grimorio"
- [ ] Renombrar archivos data: `grimorio_*.json` → `enciclopedia_*.json`

### Should-Have (Mejora auditoría)

- [ ] Crear `tests/test_coherencia_formal.py` (ValidadorLenguaje, ValidadorDFA, ValidadorEMET)
- [ ] Crear `tests/test_composicion_inductiva.py` (Axioma III.11)
- [ ] Completar este MAPA_REFERENCIAS_PROYECTO.md
- [ ] Crear `METRICAS_COHERENCIA.json` con checksums

### Nice-to-Have (Futuro)

- [ ] Crear `AUDITORIA_FORMAL_COMPLETA.md` con manifest
- [ ] Dashboard de coherencia (web o CLI)
- [ ] CI/CD checks automáticos

---

## VI. CONCLUSIÓN DIAGNOSTICADO

**Estado**: 🟡 PARCIALMENTE COHERENTE

- ✅ Teoría formal (FRAMEWORK) establecida
- ✅ Axiomas (III.7-III.11) formalizados
- ❌ Implementación tiene incoherencias menores (nomenclatura)
- ❌ Tests de validación formal FALTA
- ❌ Documentación de referencias INCOMPLETA

**Próximo paso**: Ejecutar Phase 2 de remediación (must-have items)

---

*Documento vivo — actualizar conforme se resuelven problemas.*
