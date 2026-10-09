# FP-131 ⊕ SAL — Persistencia y Caché en el Computadora

> **Propuesta de Feature**: Capa de caché unificada + serialización inteligente + recovery de estado
> **Sefirá**: מלכות Maljut (Manifestación)
> **Alquimia**: Sal = conservación, binding, integridad de materia
> **Prioridad**: HIGH (+1 RICE)
> **Fase**: Gate 1 (Pre-aprobación)

---

## 📋 Resumen Ejecutivo

**Problema**: Computadora serializa datos a disco de forma dispersa (18 json.dump() en diferentes módulos). No hay caché en memoria unificada. Al reiniciar, todo se pierde excepto lo persistido → startup lento (~8s) + pérdida de contexto activo.

**Solución**: 
1. Capa de caché en memoria (`memoria_cache.py`) con TTL configurable
2. Serialización optimizada + difing de cambios (solo escribir delta)
3. Recovery de estado al restart: restaurar caché desde checkpoint
4. Métricas de hit/miss ratio

**Valor**: 30-40% más rápido en acceso a datos críticos + menor I/O disco + contexto conversacional mantiene continuidad

---

## 🔍 Análisis D1-D7

### D1 — PRODUCTO
- **User Story**: "Como usuario del Computadora, quiero que recuerde mi último contexto cuando lo reinicio, sin perder continuidad de conversación"
- **RICE**: 
  - Reach: 100 (afecta toda sesión)
  - Impact: 3/4 (mejora percepción de memoria)
  - Confidence: 90%
  - Effort: 6 weeks
  - RICE Score: **75** (MEDIUM-HIGH)
- **Roadmap Alignment**: Tier 2 (Core UX → continuidad de sesión)
- **Go/No-Go**: ✅ GO (aligns with Le'ovdá u'Leshomrá: guardar/preservar)

### D2 — MERCADO
- **Competidores**:
  - ChatGPT: Resets context per session (sin caché) → Computadora advantage
  - Copilot: Persistent memory con cloud sync → expensive
  - Local LLMs (Ollama): Basic file-based cache
- **Moat**: Caché local + abierto (user-auditable) vs proprietary cloud
- **TAM Impact**: +15% retención de usuarios que valoran privacidad
- **Go/No-Go**: ✅ GO (diferenciador claro)

### D3 — DISEÑO UX
- **UX Impact**: 
  - New feature: "Recovery badge" en startup (mostrar qué se recuperó)
  - Settings: toggle caché por tipo de data (conversación, perfiles, etc)
  - Visual: pequeño ícono de "snapshot restored" en UI
- **WCAG AA**: Sin barreras (UI opcional, fully functional sin caché)
- **Go/No-Go**: ✅ GO (UX neutral, solo mejora)

### D4 — INGENIERÍA
- **Factibilidad**: ✅ HIGH (pattern bien-conocido)
- **Arquitectura**:
  - `computadora/memoria/cache.py` (new) — cache in-memory con LRU + TTL
  - `computadora/memoria/checkpoint.py` (new) — serializar caché a JSON snapshot
  - `computadora/nucleo/recovery.py` (modify) — restaurar snapshot en startup
  - Integración: `__main__.py` → restore cache ANTES de start sensores
- **Riesgo**: Stale cache → solved by TTL + explicit invalidation
- **Esfuerzo**: ~40 horas (design + impl + tests)
- **Go/No-Go**: ✅ GO

### D5 — FINANZAS
- **Costos**:
  - Dev: ~5 days (40h @ $80/h) = $3,200
  - Infra: 0 (local-only, no cloud)
  - Maintenance: +10% (monitoring cache health)
- **ROI**: +15% user retention @ $500 CAC = $75 lifetime value gain per user
- **Go/No-Go**: ✅ GO (positive ROI)

### D6 — MARKETING
- **Messaging**: "Computadora nunca olvida tu contexto — recupera conversaciones de días pasados"
- **Positioning**: Privacy-first memory (vs cloud-dependent competitors)
- **ASO/Copy**: "Offline memory" keyword targeting
- **Go/No-Go**: ✅ GO (strong differentiator)

### D7 — LEGAL & SEGURIDAD
- **Privacy**: Caché local = solo en disk del usuario (GDPR compliant)
- **Data Retention**: User-controlled TTL (default 30 days)
- **Encryption**: Caché NOT encrypted (local-only, asume OS-level security). Option: AES encrypt sensitive fields.
- **Go/No-Go**: ✅ GO + recommendation: document encryption trade-offs

---

## 📦 Archivos a Crear/Modificar

| # | Archivo | Tipo | Descripción |
|---|---------|------|-------------|
| 1 | `computadora/memoria/cache.py` | NEW | LRUCache + TTL manager |
| 2 | `computadora/memoria/checkpoint.py` | NEW | Serializar caché → JSON snapshot |
| 3 | `computadora/nucleo/recovery.py` | MOD | Restore snapshot en startup |
| 4 | `computadora/__main__.py` | MOD | Call recovery.restore() en init |
| 5 | `computadora/memoria/__init__.py` | MOD | Export cache + checkpoint |
| 6 | `tests/test_cache_fp131.py` | NEW | Unit + integration tests |

---

## 🧪 Criterios de Aceptación

- [ ] Caché hit ratio ≥ 80% en acceso a datos críticos (encoding rostro, perfiles, etc)
- [ ] TTL respetado (expired entries removed automáticamente)
- [ ] Snapshot restaurado correctamente en 3 restarts consecutivos
- [ ] Disk I/O reducido ≥ 30% vs baseline
- [ ] No memory leaks (profile con pympler)
- [ ] Startup time < 3s (vs 8s actual)
- [ ] All tests pass (100 coverage en cache.py)

---

## 🚀 WorkItems Derivados

| WI | Tarea | Esfuerzo | Preced |
|----|-------|----------|--------|
| WI-295 | Implement `cache.py` LRUCache + TTL | 2d | — |
| WI-296 | Implement `checkpoint.py` snapshot serializer | 1.5d | WI-295 |
| WI-297 | Implement `recovery.py` restore pipeline | 1d | WI-296 |
| WI-298 | Integrate recovery en `__main__.py` | 0.5d | WI-297 |
| WI-299 | Tests + bechmark (cache perf) | 1d | WI-298 |

---

## 🔄 Status

- **Phase**: ALBEDO (Formalización)
- **Next**: Gate 2 (Propietario review) → CITRINITAS (Investigación) → RUBEDO (Implementación)
- **Timeline**: 2w (iterativo con WI-233-244 en background)

