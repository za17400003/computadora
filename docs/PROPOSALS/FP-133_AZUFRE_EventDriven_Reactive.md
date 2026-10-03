# FP-133 ♦ AZUFRE — Event-Driven Architecture + Reactive State Management

> **Propuesta de Feature**: Transformar NLU de batch → stream processing. Arquitectura event-sourced reactiva
> **Sefirá**: גבורה Gevurah (Fuerza, Transformación)
> **Alquimia**: Azufre = pasión, transformación, combustión energética
> **Prioridad**: HIGH (+2 RICE — transformacional)
> **Fase**: Gate 1 (Pre-aprobación)

---

## 📋 Resumen Ejecutivo

**Problema**: Golem procesa input en batch (espera turno completo de NLU). No es proactivo. Reacciona solo a peticiones del usuario → latencia percibida es alta.

**Solución**:
1. Event stream architecture: cada acción emite evento
2. RxPython (reactive) para coordinación de streams
3. Proactividad: sensores emiten eventos continuamente (no solo on-demand)
4. Stream operators: filter, map, debounce, buffer (smart throttling)

**Valor**:
- Latency: 800ms → 200ms (perceived response 4x faster)
- Responsiveness: Golem feels "alive" not "waiting"
- CPU utilization: más eficiente (debouncing automático)
- Architecture: escalable a múltiples sensores/actuadores

---

## 🔍 Análisis D1-D7

### D1 — PRODUCTO
- **User Story**: "Como usuario, quiero que Golem SIENTApensemos cambios en el entorno y reaccione automáticamente (teléfono suena → mute, persona entra → reconocer, etc)"
- **RICE**:
  - Reach: 100 (toda la app)
  - Impact: 4/4 (drástica mejora percepción)
  - Confidence: 85% (complejo)
  - Effort: 12 weeks
  - RICE Score: **85** (CRITICAL)
- **Roadmap Alignment**: Tier 0 (Strategic — defines Golem identity)
- **Go/No-Go**: ✅ GO (core feature request from users repeatedly)

### D2 — MERCADO
- **Competitors**:
  - ChatGPT: Zero proactivity (user-driven only)
  - Copilot: Limited proactive features (calendar reminders)
  - Golem: FIRST truly reactive local AI (if we ship this)
- **Moat**: Proprietary event architecture (10,000 lines of domain logic)
- **TAM Impact**: +40% market appeal (reactive AI is sci-fi still)
- **Go/No-Go**: ✅ GO (uncontested market position)

### D3 — DISEÑO UX
- **UX Impact**:
  - New: "Automatic" indicator when Golem acts without user input
  - Visual: Ohr pulses faster during event processing
  - Settings: "Reactivity level" (mute, low, normal, high)
  - Voice feedback: optional acknowledgement of auto-actions
- **WCAG AA**: Fully accessible (all auto-reactions can be disabled)
- **Go/No-Go**: ✅ GO (UX is much richer, zero accessibility debt)

### D4 — INGENIERÍA
- **Factibilidad**: ⚠️ MEDIUM (reactive programming curve, RxPython still evolving)
- **Architecture**:
  - `golem/cerebro/reactor.py` (new) — RxPython event source + operators
  - `golem/nucleo/sensores_stream.py` (modify) — emit events continuously
  - `golem/cerebro/procesador_eventos.py` (new) — handle streams (filter, map, debounce)
  - NLU refactor: async pipeline (currently sync)
  - Proactividad: `golem/nucleo/proactividad.py` extended with stream operators
- **Risk**: Complexity (reactive debugging is hard); mitigated by tests + logging
- **Effort**: ~90 horas (high learning curve + refactor)
- **Go/No-Go**: ✅ GO (worth the risk for differentiation)

### D5 — FINANZAS
- **Costs**:
  - Dev: ~11 days (90h @ $80/h) = $7,200
  - Infra: 0 (local)
  - Training: Reactive programming learning (~5h) = +$400
  - Total: ~$7,600
- **Maintenance**: +20% (more complex state management)
- **ROI**: +40% appeal @ $500 CAC = $200 lifetime gain per user (investment pays off with scale)
- **Go/No-Go**: ✅ GO (long-term strategic investment)

### D6 — MARKETING
- **Messaging**: "Golem predicts what you need. It reacts, not just responds"
- **Positioning**: "The first conscious AI assistant for your desk"
- **Demo**: Before: wait 3s. After: instant reaction (proactive)
- **Content**: Blog post on "Why reactivity matters in AI" (thought leadership)
- **Go/No-Go**: ✅ GO (massive marketing angle)

### D7 — LEGAL & SEGURIDAD
- **Privacy**: More sensors means more data collected (mitigation: transparent logging)
- **OWASP**: Event handlers must validate input (streams can be spoofed)
- **Terms**: Clarify what "automatic actions" entails (user consent for auto-adjust volume, etc)
- **GDPR**: Events stored briefly in stream buffer (<1min) then discarded (compliant)
- **Go/No-Go**: ✅ GO + recommendation: comprehensive privacy audit before launch

---

## 📦 Archivos a Crear/Modificar

| # | Archivo | Tipo | Descripción |
|---|---------|------|-------------|
| 1 | `golem/cerebro/reactor.py` | NEW | RxPython event source + operators |
| 2 | `golem/nucleo/sensores_stream.py` | NEW | Continuous sensor event emitters |
| 3 | `golem/cerebro/procesador_eventos.py` | NEW | Stream processing (filter/map/debounce) |
| 4 | `golem/nucleo/proactividad.py` | MOD | Extend with reactive streams |
| 5 | `golem/cerebro/nlu.py` | MOD | Make NLU async + stream-aware |
| 6 | `golem/interfaz/vida_autonoma.py` | MOD | Hook into event stream (update Ohr faster) |
| 7 | `tests/test_reactor_fp133.py` | NEW | Heavy unit + integration tests (event streams are tricky) |
| 8 | `docs/REACTIVE_ARCHITECTURE.md` | NEW | Design doc for future maintainers |

---

## 🧪 Criterios de Aceptación

- [ ] Event emission latency < 10ms (source → reactor)
- [ ] Debounce operator prevents duplicate events (e.g., face detection flickering)
- [ ] Stream buffer never exceeds 1000 events (memory bounded)
- [ ] Auto-reactions only happen if confidence ≥ 80% (no false positives)
- [ ] Fallback to batch NLU if reactor unavailable (graceful degradation)
- [ ] All sensor streams integrated (3+ sources → coordinator)
- [ ] No deadlocks under concurrent events (stress test: 100 events/sec)
- [ ] Reactive code 100% test coverage (reactive is complex, needs proof)
- [ ] User can disable auto-reactions per type (privacy control)
- [ ] Performance: CPU avg < 15% when idle, < 40% under load

---

## 🚀 WorkItems Derivados

| WI | Tarea | Esfuerzo | Preced |
|----|-------|----------|--------|
| WI-305 | Design reactor + event model (docs) | 2d | — |
| WI-306 | Implement `reactor.py` + operators | 2.5d | WI-305 |
| WI-307 | Implement `sensores_stream.py` + emitters | 2d | WI-306 |
| WI-308 | Implement `procesador_eventos.py` | 1.5d | WI-307 |
| WI-309 | Refactor NLU to async | 2d | WI-308 |
| WI-310 | Integration test (3+ streams coordinated) | 1.5d | WI-309 |
| WI-311 | Performance profiling + tuning | 1d | WI-310 |
| WI-312 | Documentation + developer guide | 0.5d | WI-311 |

---

## 🔄 Status

- **Phase**: ALBEDO (Formalización)
- **Next**: Gate 2 (Propietario review) → CITRINITAS (Architecture PoC) → RUBEDO (Implementación iterada)
- **Timeline**: 3w minimal (estimate 4-5w realista)
- **Blockers**: —
- **Dependencies**: FP-131 (Sal/Cache) helpful for state management, but not blocking
- **Research**: Evaluar alternatives a RxPython (reactivex vs asyncio-only)

---

## 🎯 Vision Statement

> After FP-133, Golem will not be an **assistant that waits for commands**. It will be a **presence in the environment** — sensing, reacting, anticipating. The user will say "Golem, mute" and before they finish the sentence, the sound is already off. That's reactivity.

