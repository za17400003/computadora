# Proyecto Computadora — Test Coverage Matrix (v. Ciclo 11)

*Última actualización: Mayo 10, 2026*  
*Generado por: PALINGENESIA Meta-Análisis Profundo*

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Cobertura Global** | ~45-50% |
| **Módulos con Tests** | 23/35 (66%) |
| **Módulos sin Tests** | 12/35 (34%) |
| **Tests Totales** | ~90 |
| **Gap Crítico** | 0 (todos los CRÍTICOS tienen tests) |
| **Gap Alto** | 2 módulos |
| **Gap Medio** | 10 módulos |

---

## 🎯 Matriz de Cobertura Detallada

### TIER 1: CRÍTICO (Seguridad + Boot)

| Módulo | Archivo | Tests | Cobertura | Estado | Acciones |
|--------|---------|-------|-----------|--------|----------|
| **NLU** | `cerebro/nlu.py` | test_nlu_*.py | ~70% | ✅ BUENO | Mantener |
| **Escucha** | `voz/escucha.py` | test_whisper.py, test_audio_*.py | ~60% | 🟡 MEDIO | Agregar: stress test, echo filter validation |
| **Habla** | `voz/habla.py` | test_habla.py | ~50% | 🟡 MEDIO | Agregar: edge-tts failure scenarios |
| **Watchdog** | `interfaz/watchdog.py` | test_watchdog_*.py | ~65% | ✅ BUENO | Verificar FP-150 thresholds en tests |
| **Rostro** | `percepcion/rostro.py` | test_vision_emet.py | ~70% | ✅ BUENO | Agregar: anti-spoofing (WI-306) cuando disponible |
| **Boot** | `cerebro/renovacion.py` | test_ciclo_*.py | ~60% | 🟡 MEDIO | Agregar: boot phase transitions |
| **Renovación** | `cerebro/renovacion.py` | test_tikun_*.py | ~55% | 🟡 MEDIO | Agregar: renewal cycle edge cases |

**Estado**: Tier 1 cubierto. Siguiente: Mejorar stress scenarios.

---

### TIER 2: ALTO (Funcionalidad Core)

| Módulo | Archivo | Tests | Cobertura | Estado | Acciones |
|--------|---------|-------|-----------|--------|----------|
| **Orquestador** | `nucleo/orquestador.py` | test_orquestador_*.py | ~45% | 🟡 MEDIO | ⚠️ Agregar: async task queuing |
| **Meta-Workflow** | `nucleo/meta_workflow.py` | test_meta_workflow.py | ~40% | 🟡 MEDIO | Agregar: Sefirot event routing tests |
| **Bus Eventos** | `nucleo/eventos.py` | test_eventos.py | ~35% | 🟠 BAJO | ⚠️ Agregar: subscriber cleanup, deadlock scenarios |
| **Memoria** | `memoria/memoria.py` | test_memoria_*.py | ~50% | 🟡 MEDIO | Agregar: persistence edge cases |
| **Ferrofluido** | `interfaz/ferrofluido_rubedo.py` | ❌ MISSING | 0% | 🔴 CRÍTICO | ⚠️ CREAR: test_fps_rendering, test_ferrofluido_performance |
| **Interfaz (Orbe)** | `interfaz/ventana_principal.py` | test_ui_*.py | ~30% | 🟠 BAJO | ⚠️ CREAR: test_frame_skip_listening (RF-362), test_ui_state_machine |

**Acción prioritaria**: Ferrofluido performance tests (FP-150 RF-362 frame skip needs validation).

---

### TIER 3: MEDIO (Integración + Habilidades)

| Módulo | Archivo | Tests | Cobertura | Estado | Acciones |
|--------|---------|-------|-----------|--------|----------|
| **Red** | `computadora/red.py` | ❌ NONE | 0% | 🔴 CRÍTICO | ⚠️ CREAR: test_red_*.py (network parsing, attacks) |
| **Control Remoto** | `computadora/control_remoto.py` | ❌ NONE | 0% | 🔴 CRÍTICO | ⚠️ CREAR: test_control_remoto_*.py (auth, commands) |
| **Web** | `computadora/web.py` | ❌ NONE | 0% | 🔴 CRÍTICO | ⚠️ CREAR: test_web_*.py (injection tests, navigation) |
| **Metrón** | `computadora/metraton.py` | ❌ NONE | 0% | 🔴 CRÍTICO | CREAR: test_metraton_*.py (geometry, timing) |
| **Vision Emoción** | `percepcion/emocion_rostro.py` | ❌ PARTIAL | ~25% | 🟠 BAJO | Agregar: all emotion classes (joy, anger, etc.) |
| **Cache** | `memoria/cache.py` | test_cache_*.py | ~40% | 🟡 MEDIO | Agregar: LRU eviction edge cases |
| **Habilidades** | `habilidades/*.py` | ✅ VARIOS | ~50-70% | 🟡 MEDIO | Verificar cada una (15+ habilidades) |

**Recomendación**: Tier 3 tiene 4 gaps CRÍTICOS (RED, CONTROL_REMOTO, WEB, METRÓN) → NO son bloqueadores de Ciclo 11, pero necesarios para Ciclo 12+.

---

### TIER 4: BAJO (Utilidades + Experimental)

| Módulo | Archivo | Tests | Cobertura | Estado | Acciones |
|--------|---------|-------|-----------|--------|----------|
| **Config** | `config.py` | test_config.py | ~60% | ✅ BUENO | Mantener |
| **Utils** | `utils/*.py` | test_utils_*.py | ~50% | 🟡 MEDIO | Agregar: error path coverage |
| **Logger** | `logger.py` | test_logger_*.py | ~45% | 🟡 MEDIO | Agregar: log rotation, buffer overflow |
| **Hot Reload** | `cerebro/hot_reload.py` | test_hot_reload.py | ~40% | 🟡 MEDIO | Agregar: concurrent reload scenarios |

---

## 🔥 Gaps Críticos Identificados (ALBEDO Phase Results)

### Gap A: Ferrofluido Rendering Performance (RF-362, FP-150)
- **Afecta**: FPS rendering, Orbe visualization
- **Test Missing**: `test_fps_listening_mode.py`
- **Qué Testear**:
  - Frame skip activación en estado "escuchando"
  - FPS target 30 vs 60 (medible)
  - CPU usage durante listening
  - Transiciones suave entre 60→30→60 FPS
- **Severidad**: 🟠 ALTA (FP-150 feature needs validation)
- **Esfuerzo**: 1 hora
- **Línea**: `ventana_principal.py` línea ~1143

### Gap B: Audio Queue Stress Testing (RF-361, FP-150)
- **Afecta**: Audio overflow handling, queue management
- **Test Missing**: `test_audio_queue_stress.py`
- **Qué Testear**:
  - Queue maxsize 256 under high load (multiple threads)
  - Overflow detection (queue.Full exception)
  - Oldest vs newest buffer discard policy
  - Recovery after overflow
- **Severidad**: 🟠 ALTA (FP-150 feature needs validation)
- **Esfuerzo**: 1 hora
- **Línea**: `escucha.py` línea ~1099

### Gap C: Ollama Timeout Adaptive (RF-360, FP-150)
- **Afecta**: Watchdog circuit breaker, false positive alerts
- **Test Missing**: Integrate into `test_watchdog_*.py`
- **Qué Testear**:
  - Timeout 30s vs old 10s (prevent false NOTIFY triggers)
  - Large model (llama2:7b) latency scenarios
  - NOTIFY threshold 90s (no premature escalation)
  - DEGRADE threshold 240s (conservative)
- **Severidad**: 🟠 ALTA (FP-150 feature needs validation)
- **Esfuerzo**: 0.5 hours (modify existing watchdog tests)
- **Línea**: `watchdog.py` línea ~210

### Gap D: Web Module Security (0% coverage)
- **Afecta**: Web navigation, injection attacks
- **Test Missing**: `test_web_security.py`, `test_web_navigation.py`
- **Qué Testear**:
  - XSS prevention (user input escaping)
  - SQL injection (if applicable)
  - URL parsing edge cases
  - Navigation timeouts
- **Severidad**: 🔴 CRÍTICO (Security)
- **Esfuerzo**: 2 hours
- **Línea**: `web.py` ALL

### Gap E: Network Parsing (0% coverage)
- **Afecta**: Network monitoring, device enumeration
- **Test Missing**: `test_red_parsing.py`, `test_red_security.py`
- **Qué Testear**:
  - MAC address parsing
  - IP parsing edge cases
  - Device enumeration robustness
  - Malformed input handling
- **Severidad**: 🔴 CRÍTICO (Security)
- **Esfuerzo**: 2 hours
- **Línea**: `red.py` ALL

### Gap F: Remote Control Authorization (0% coverage)
- **Afecta**: Remote command execution, permission model
- **Test Missing**: `test_control_remoto_auth.py`, `test_control_remoto_commands.py`
- **Qué Testear**:
  - Permission checks before command execution
  - Allowlist validation
  - Unauthorized command rejection
  - Command parsing edge cases
- **Severidad**: 🔴 CRÍTICO (Security)
- **Esfuerzo**: 2 hours
- **Línea**: `control_remoto.py` ALL

---

## ✅ Test Execution Commands

### Run All Tests
```bash
pytest tests/ -v --tb=short
```

### Run Specific Tier
```bash
# Tier 1 (Critical)
pytest tests/test_nlu_*.py tests/test_whisper.py tests/test_watchdog_*.py -v

# Tier 2 (High)
pytest tests/test_orquestador_*.py tests/test_meta_workflow.py tests/test_ui_*.py -v

# Tier 3 (Medium)
pytest tests/test_red*.py tests/test_control_remoto*.py tests/test_web*.py -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=computadora --cov-report=html
# Open htmlcov/index.html
```

### Run FP-150 Validation (New)
```bash
# These tests validate RF-360/361/362 features from FP-150
pytest tests/test_fps_listening_mode.py tests/test_audio_queue_stress.py tests/test_watchdog_*.py -v -k "FP-150 or RF-360 or RF-361 or RF-362"
```

---

## 📋 Próximos Pasos (Ciclo 12+)

### Immediate (This Cycle)
- [ ] Create `test_fps_listening_mode.py` (1h) — RF-362 validation
- [ ] Create `test_audio_queue_stress.py` (1h) — RF-361 validation
- [ ] Update watchdog tests for RF-360 thresholds (0.5h)
- [ ] Run full test suite → ensure FP-150 changes don't regress

### Short Term (Ciclo 12)
- [ ] Fill Gap D: Web security tests (2h)
- [ ] Fill Gap E: Network parsing tests (2h)
- [ ] Fill Gap F: Remote control auth tests (2h)
- [ ] Ferrofluido performance benchmarks (1h)

### Medium Term (Ciclo 13+)
- [ ] Anti-spoofing tests (WI-306 when ready)
- [ ] Integration tests: Escucha → NLU → Habla (1h)
- [ ] Stress tests: All 3 tiers simultaneously (2h)
- [ ] Load tests: 1000+ commands in pipeline (TBD)

---

## 🔗 Cross-references

- **SRS.md**: RF-01 to RF-362 (todas las RFs tienen "Test" field)
- **SDD.md**: §4.17.1-4.17.4 (Etz HaChaim architecture)
- **API.md**: Contratos públicos testables (NEW Ciclo 11)
- **DEVELOPMENT_WORKFLOW.md**: Regla #13 (toda feature debe tener test antes commit)

---

**Fin de Test Coverage Matrix**

*PALINGENESIA Ciclo 11 — Cobertura auditada, Gaps clasificados, Acciones claras*

