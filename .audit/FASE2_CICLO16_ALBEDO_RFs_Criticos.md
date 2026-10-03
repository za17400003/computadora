# ALBEDO CICLO 16 — RFs Críticos para Hardening Fase 2

## Mapeo de RFs por Criticidad de Hardening

Basado en NIGREDO (0% exception coverage, 191 tests happy-path), priorizamos RFs con:
1. **Mayor impacto** en estabilidad del sistema
2. **Mayor riesgo** de fallos catastróficos
3. **Mayor exposición** a inputs adversariales

---

## RF-06: NLU 3-Level Intelligence — ALTA CRITICIDAD

**Riesgo**: 
- L1 regex injection (malformed commands)
- L2 Ollama timeouts, malformed responses
- L3 Copilot gate lock failures
- Token overflow (4000 max)

**Hardening Needed**:
- [ ] Exception: Invalid regex patterns
- [ ] Exception: Ollama connection refused
- [ ] Exception: Copilot rate limit (429)
- [ ] Boundary: Input >10000 tokens → truncate gracefully
- [ ] Boundary: Confidence 0.0 vs 1.0 edge cases
- [ ] Injection: Command injection via NLU ("delete all files")
- [ ] Resource: 100 concurrent requests → queue/timeout

**Test Count (Ciclo 11)**: 10 tests → need +8 hardening tests = 18 total

---

## RF-36: Ruaj Emotional System — ALTA CRITICIDAD

**Riesgo**:
- Graph corruption (invalid transitions)
- Trigger cascade (infinite loops in transitions)
- JSON deserialization failures
- Race condition: emotion_change while querying state

**Hardening Needed**:
- [ ] Exception: Invalid humor state
- [ ] Exception: Trigger not in defined set
- [ ] Exception: Corrupted personalidad.json
- [ ] Boundary: 0 triggers active → neutral humor
- [ ] Concurrency: Read Ruaj while trigger fires
- [ ] Injection: Malformed trigger dict → crash

**Test Count (Ciclo 11)**: 14 tests → need +7 hardening tests = 21 total

---

## RF-54: Audit Logging — CRÍTICA SEGURIDAD

**Riesgo**:
- Audit trail corruption
- Tampering detection bypass
- Log injection attacks
- Disk full → silent failures

**Hardening Needed**:
- [ ] Exception: Write to missing directory
- [ ] Exception: Permission denied (readonly audit log)
- [ ] Exception: Disk full scenario
- [ ] Injection: Newlines in log payload → format bypass
- [ ] Injection: SQL/JSON in user action field
- [ ] Boundary: 90-day retention exact cutoff
- [ ] Concurrency: 100 audit writes/second

**Test Count (Ciclo 10)**: 7 tests → need +8 hardening tests = 15 total

---

## RF-56: Anti-Tampering — CRÍTICA SEGURIDAD

**Riesgo**:
- Hash collision bypass
- Config file replacement attack
- Immutable trail compromise

**Hardening Needed**:
- [ ] Exception: Config not found
- [ ] Exception: Invalid SHA256 format
- [ ] Injection: Modified config + re-hash
- [ ] Boundary: Empty config file
- [ ] Adversarial: Replace config, verify detection

**Test Count (Ciclo 10)**: 5 tests → need +5 hardening tests = 10 total

---

## RF-57: Intrusion Detection — CRÍTICA SEGURIDAD

**Riesgo**:
- False negatives (attack not detected)
- DoS via anomaly alert spam
- Admin notification failures
- IP blocking incorrect ranges

**Hardening Needed**:
- [ ] Boundary: Anomaly at exactly 0.15 threshold
- [ ] Exception: Invalid IP format → block anyway
- [ ] Exception: Admin notification service down
- [ ] Exception: IP firewall command fails
- [ ] Injection: Crafted pattern that evades detection
- [ ] Concurrency: 1000 anomalies/second → alert queue

**Test Count (Ciclo 10)**: 7 tests → need +6 hardening tests = 13 total

---

## RF-29: Circadian Adaptive — MEDIA CRITICIDAD

**Riesgo**:
- Latency calculation underflow (negative values)
- Energy phase transition discontinuity
- Midnight bug (23:59:59 → 0:00:00 transition)

**Hardening Needed**:
- [ ] Boundary: Exactly midnight (00:00:00)
- [ ] Boundary: Exactly phase boundaries (6:00, 12:00, 18:00)
- [ ] Boundary: Energy 0.0 and 1.0 extreme cases
- [ ] Exception: Invalid phase name
- [ ] Injection: Modify system clock (if possible)

**Test Count (Ciclo 12)**: 8 tests → need +5 hardening tests = 13 total

---

## RF-32: Speaker Classification — MEDIA CRITICIDAD

**Riesgo**:
- Voice recognition false positives
- Trust escalation attacks
- Command pattern anomaly bypass

**Hardening Needed**:
- [ ] Boundary: Confidence exactly 0.95
- [ ] Boundary: Trust 0.0 (stranger) edge cases
- [ ] Exception: Voice recognition service down
- [ ] Injection: Spoof voice pattern
- [ ] Concurrency: Same speaker 10 commands simultaneously

**Test Count (Ciclo 12)**: 6 tests → need +5 hardening tests = 11 total

---

## RF-33: Guardian Mode — CRÍTICA NIÑO

**Riesgo**:
- Filter bypass (adversarial content)
- Child detection false negatives
- Auto-activation failures
- Safe alternative substitution broken

**Hardening Needed**:
- [ ] Boundary: High-pitch exactly at threshold
- [ ] Boundary: Vocabulary complexity edge cases
- [ ] Exception: Filter list corrupted
- [ ] Injection: Obfuscated violent content
- [ ] Injection: Mixed safe/unsafe words
- [ ] Adversarial: Content designed to bypass filter

**Test Count (Ciclo 12)**: 6 tests → need +8 hardening tests = 14 total

---

## Summary: Hardening Test Plan (Ciclo 16-18)

| RF | Category | Priority | Current | Hardening | Total |
|----|----------|----------|---------|-----------|-------|
| RF-06 | NLU | HIGH | 10 | +8 | 18 |
| RF-36 | Emotion | HIGH | 14 | +7 | 21 |
| RF-54 | Security | CRITICAL | 7 | +8 | 15 |
| RF-56 | Security | CRITICAL | 5 | +5 | 10 |
| RF-57 | Security | CRITICAL | 7 | +6 | 13 |
| RF-29 | Timing | MEDIUM | 8 | +5 | 13 |
| RF-32 | Voice | MEDIUM | 6 | +5 | 11 |
| RF-33 | Safety | CRITICAL | 6 | +8 | 14 |
| **TOTAL** | | | **63** | **+52** | **115** |

### Next Phase: CITRINITAS (Diseño de plantillas reutilizables)

---

## Alquimia ALBEDO

**ALBEDO Operativo**: Separación de concerns completada
- RFs críticos identificados (8 RFs prioritarios)
- Hardening requirements mapeadas (52 tests faltantes)
- Categorías: NLU, Emotion, Security (3x), Timing, Voice, Safety
- Pipeline claro para Ciclos 16-18

**Estado**: ✅ ALBEDO COMPLETADO → CITRINITAS PRÓXIMO
