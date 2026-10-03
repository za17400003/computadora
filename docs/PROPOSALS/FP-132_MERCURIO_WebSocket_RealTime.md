# FP-132 ☿ MERCURIO — APIs WebSocket + Event Streaming Real-Time

> **Propuesta de Feature**: Reemplazar REST polling con WebSocket + Server-Sent Events (SSE)
> **Sefirá**: הוד Hod (Intelecto, Comunicación)
> **Alquimia**: Mercurio = fluidez, comunicación, transporte instantáneo
> **Prioridad**: HIGH (+1 RICE)
> **Fase**: Gate 1 (Pre-aprobación)

---

## 📋 Resumen Ejecutivo

**Problema**: Minimi (Android) usa polling cada 3s para logs, estado, eventos → latencia ~3s, server CPU alto, battery drain en cliente.

**Solución**:
1. WebSocket endpoint en `servidor_api.py`
2. Server-Sent Events (SSE) para eventos unidireccionales (logs, alerts)
3. Pub/Sub model: Golem emite eventos, Minimi suscribe (topicos)
4. Fallback a polling si WebSocket cae (graceful degradation)

**Valor**: 
- Latencia: 3s → 50ms (60x más rápido)
- Server CPU: -40%
- Client battery: -25%
- Real-time user experience (logs live, estado instantáneo)

---

## 🔍 Análisis D1-D7

### D1 — PRODUCTO
- **User Story**: "Como usuario de Minimi, quiero ver los logs del Golem EN DIRECTO sin demoras de polling"
- **RICE**:
  - Reach: 80 (afecta Minimi + Golem relay)
  - Impact: 3/4 (drástica mejora latencia)
  - Confidence: 95%
  - Effort: 8 weeks
  - RICE Score: **71** (MEDIUM-HIGH)
- **Roadmap Alignment**: Tier 1 (Core connectivity)
- **Go/No-Go**: ✅ GO (essential for real-time UX)

### D2 — MERCADO
- **Competidores**:
  - ChatGPT desktop: WebSocket bien integrado (fast)
  - Ollama: Polling-based (lento)
  - Local AI assistants: vary widely
- **Moat**: First local AI with true real-time comms
- **TAM Impact**: +20% power users (devs que debuggean en vivo)
- **Go/No-Go**: ✅ GO (competitive advantage)

### D3 — DISEÑO UX
- **UX Impact**:
  - New: "Live indicator" en LogsScreen (pulsing dot = streaming)
  - Smooth animations sin jank por polling delays
  - SettingsScreen: toggle "Real-time logs" (expert mode)
- **WCAG AA**: Fully accessible (indicator optional)
- **Go/No-Go**: ✅ GO (UX improves significantly)

### D4 — INGENIERÍA
- **Factibilidad**: ✅ HIGH (standard tech: aiohttp, websockets)
- **Arquitectura**:
  - `golem/canales/websocket_server.py` (new) — WebSocket endpoint
  - `golem/canales/pubsub.py` (new) — Topic-based pub/sub
  - `golem/canales/servidor_api.py` (modify) — Add WebSocket route
  - Android: Go-compatible WebSocket client (`GolemClient.kt` modify)
  - Fallback logic: if WebSocket down → automatic resume polling
- **Riesgo**: Connection instability → mitigated by heartbeat + auto-reconnect
- **Esfuerzo**: ~60 horas (backend + client + tests)
- **Go/No-Go**: ✅ GO

### D5 — FINANZAS
- **Costs**:
  - Dev: ~7.5 days (60h @ $80/h) = $4,800
  - Infra: 0 (local-only, socket in same network)
  - Maintenance: +15% (connection monitoring)
- **ROI**: +20% power user retention @ $1,200 CAC = $240 lifetime gain per user
- **Go/No-Go**: ✅ GO (strong positive ROI)

### D6 — MARKETING
- **Messaging**: "Golem Relay is instant — see logs LIVE on Minimi"
- **Positioning**: "Real-time assistant sync" (only local AI with this)
- **Demo**: Side-by-side polling (3s lag) vs WebSocket (50ms) video
- **Go/No-Go**: ✅ GO (strong differentiator for power users)

### D7 — LEGAL & SEGURIDAD
- **Security**: WebSocket same network (local LAN), can add TLS if needed
- **Data**: Event streams NOT encrypted by default (assume LAN trust)
- **OWASP**: Validate message format (JSON schema), rate-limit per client
- **Go/No-Go**: ✅ GO + recommendation: document private network requirement

---

## 📦 Archivos a Crear/Modificar

| # | Archivo | Tipo | Descripción |
|---|---------|------|-------------|
| 1 | `golem/canales/websocket_server.py` | NEW | WebSocket server + handlers |
| 2 | `golem/canales/pubsub.py` | NEW | Pub/Sub manager (topics) |
| 3 | `golem/canales/servidor_api.py` | MOD | Integrate WebSocket route |
| 4 | `golem/utilidades/heartbeat.py` | NEW | Connection heartbeat + keepalive |
| 5 | `Minimi/GolemClient.kt` | MOD | WebSocket client + fallback logic |
| 6 | `Minimi/MinimiViewModel.kt` | MOD | Use WebSocket streams |
| 7 | `tests/test_websocket_fp132.py` | NEW | WebSocket + pub/sub unit tests |

---

## 🧪 Criterios de Aceptación

- [ ] WebSocket endpoint responds in <100ms
- [ ] SSE event delivery latency < 50ms on local network
- [ ] Auto-reconnect after disconnection works (test by killing socket)
- [ ] Fallback to polling works if WebSocket unavailable
- [ ] Pub/Sub multi-client subscriptions work correctly (1→N broadcast)
- [ ] No memory leaks with 10+ sustained connections
- [ ] Heartbeat prevents stale connections (timeout after 30s inactivity)
- [ ] Integration tests: 100+ reconnect cycles pass
- [ ] Battery drain reduced ≥ 20% (PoC measurement in Minimi)

---

## 🚀 WorkItems Derivados

| WI | Tarea | Esfuerzo | Preced |
|----|-------|----------|--------|
| WI-300 | Implement WebSocket server + handlers | 2.5d | — |
| WI-301 | Implement Pub/Sub manager | 1.5d | WI-300 |
| WI-302 | Implement heartbeat + auto-reconnect logic | 1d | WI-301 |
| WI-303 | Modify Minimi WebSocket client | 1.5d | WI-302 |
| WI-304 | Integration tests + load test | 1.5d | WI-303 |

---

## 🔄 Status

- **Phase**: ALBEDO (Formalización)
- **Next**: Gate 2 (Propietario review) → CITRINITAS (Research PoC) → RUBEDO (Implementación)
- **Timeline**: 2.5w (parallel to WI-233-244 rama principal)
- **Blockers**: —
- **Dependencies**: WI-233 (Logs API) must be stable first

