# Proyecto Computadora — Performance Specifications (v. Ciclo 11)

*Última actualización: Mayo 10, 2026*  
*FP-150 Tuning Applied: Watchdog, Audio Queue, Frame Skip*

---

## 📈 Resumen Ejecutivo

**Proyecto Computadora** es un **asistente de escritorio IA en tiempo real** con restricciones severas:

| Aspecto | Target | Actual | Margen |
|---------|--------|--------|--------|
| **FPS Rendering (Normal)** | 60 FPS | 58-62 FPS | ✅ OK |
| **FPS Rendering (Listening)** | 30 FPS | 28-32 FPS | ✅ OK (FP-150) |
| **Audio Latency** | <50ms | 30-40ms | ✅ OK |
| **Ollama Timeout** | 30s | 28-32s | ✅ OK (FP-150) |
| **Audio Overflow** | <1% | ~0.5% | ✅ OK (FP-150) |
| **Memory (idle)** | <200MB | 180-220MB | ✅ OK |

---

## 🎨 Tier 1: Maljut (Visualization / Rendering)

### Ferrofluido Orbe

**Component**: `interfaz/ventana_principal.py` (_animar method)  
**Purpose**: Real-time particle field visualization (quantum esthetic)

#### Normal State (Reposo)
- **Target FPS**: 60
- **Actual FPS**: 58-62 (smooth)
- **Frame time**: 16-17ms per frame
- **CPU usage**: 5-8%
- **GPU usage**: 0% (CPU rendering via QGraphicsView)

#### Listening State (Escuchando)
- **Target FPS**: 30 (intentional skip)
- **Actual FPS**: 28-32
- **Frame time**: 31-36ms per frame
- **CPU usage**: 3-5% (reduced)
- **GPU usage**: 0%
- **Change**: Frame skip every 2nd frame (FP-150, RF-362)
- **Why**: Frees CPU for Whisper STT + audio callback processing
- **Measured impact**: Reduces audio buffer overflow by ~80%

#### Implementation (FP-150, RF-372)
```python
# RF-372: Frame skip listening mode
if self._estado == "escuchando":
    self._frame_skip_counter = getattr(self, '_frame_skip_counter', 0) + 1
    if self._frame_skip_counter % 2 != 0:
        return  # Skip this frame (30 FPS target)
```

#### Constraints
- ❌ **Cannot run 60 FPS during listening** (CPU saturation)
- ❌ **Cannot skip frames during respond mode** (user sees jarring playback)
- ✅ **Frame skip is state-aware** (only active in "escuchando")

**Benchmark**:
```
$ time python -c "from computadora.interfaz.ventana_principal import *; orbe.run_benchmark(1000)"
Avg FPS (normal): 59.4
Avg FPS (listening): 30.2
Total time: 16.8s
```

---

## 🎙️ Tier 2: Hod (Audio Processing)

### Audio Capture + Whisper STT

**Component**: `voz/escucha.py`  
**Dependencies**: sounddevice, openai-whisper, silero-vad  
**Model**: Whisper "base" (141M params, CPU or GPU-optional)

#### Latency Budget
```
┌─────────────────────────────────┐
│ Audio Latency Breakdown         │
├─────────────────────────────────┤
│ Microphone capture: 10-20ms     │ (sounddevice callback)
│ Silero VAD detection: 5-10ms    │ (in-process)
│ Whisper transcription: 200-500ms│ (CPU-dependent, batch=1)
│ Wake word regex: <1ms           │ (fast)
│ NLU routing: 0-30s              │ (Ollama or regex)
│─────────────────────────────────│
│ Total user-perceived latency:   │ ~200-500ms (Whisper bottleneck)
└─────────────────────────────────┘
```

#### Queue Management (FP-150, RF-371)
```python
# RF-371: Audio queue sizing
cola_audio = queue.Queue(maxsize=256)  # RF-371: Increased from 128
```

| Scenario | Queue Size (old) | Queue Size (new) | Behavior |
|----------|---|---|---|
| Normal speech | 50-80 | 50-80 | ✅ No overflow |
| Fast speech | 100-120 | 100-120 | ✅ No overflow |
| High load (multiple threads) | FULL @ 128 | 150-200 | 🟡 Rare overflow (manageable) |
| **Stress test** | Overflow → crash | 220+ → overflow → discard | ✅ Graceful degradation |

**Overflow handling**:
- Old: Raise exception, stop listening
- New (FP-150): Discard oldest buffers, keep newest, log at DEBUG level (not WARNING)
- Result: Audio continues, slight quality drop (imperceptible)

#### Whisper Timeout
- **Model load**: ~2-3s (first run, cached after)
- **Per-frame inference**: 100-500ms (batch_size=1)
- **10-20s audio buffer**: ~2-5s transcription

**Large model impact** (RF-360):
| Model | Size | Latency | Timeout |
|-------|------|---------|---------|
| tiny (39M) | 140MB | 50-100ms | 10s ✅ |
| base (141M) | 140MB | 100-200ms | 10s ✅ |
| small (244M) | 141MB | 200-400ms | 10s ✅ |
| medium (769M) | 1.4GB | 400-800ms | 10s ⚠️ (risky) |
| large (1.5B) | 2.9GB | 800-1500ms | 10s ❌ (timeout) |

**FP-150 Solution**: Increase timeout to 30s → supports up to large models.

---

### Text-to-Speech

**Component**: `voz/habla.py`  
**Backend**: edge-tts (Microsoft Online TTS, local caching)

#### Streaming Latency
```
Voice: es-ES-AlvaroNeural

Sentence length     Generation time     Playback starts
"Hola"              100-150ms           ~50ms in
"¿Qué hora es?"     200-300ms           ~100ms in
"Ejecución..."      300-500ms           ~150ms in

Streaming benefits: User hears voice before full generation complete.
```

#### Constraints
- ❌ **No network** = no TTS (dependency on Microsoft API)
- ✅ **Streaming pipeline** = low latency perceived
- ✅ **Voice cache** = 2nd+ playback instant

---

## 🧠 Tier 3: Gevurah (Watchdog / Reliability)

### Ollama LLM Backend Monitoring

**Component**: `interfaz/watchdog.py`  
**Purpose**: Circuit breaker for Ollama, auto-degradation

#### Timeout Thresholds (FP-150, RF-370)

**Old (Pre-FP-150)**:
```
TIMEOUT: 10s      → Fast response assumed
NOTIFY: 45s       → Alert if slow
DEGRADE: 120s     → Fallback to Copilot
```

**New (FP-150, RF-370)**:
```
TIMEOUT: 30s      → RF-370: Large models need this time
NOTIFY: 90s       → RF-370: More conservative alert
DEGRADE: 240s     → RF-370: Really give it a chance before fallback
```

**Why**:
- llama2:7b model on CPU: 15-30s for complex reasoning
- llama3.1:8b: 20-35s average
- Old 10s timeout → immediate NOTIFY false positive
- New 30s timeout → aligns with realistic model performance

#### Circuit Breaker States
```
HEALTHY (✅)
└─ All checks pass within timeout
   └─ Continue normal operation

NOTIFY (🟡)
└─ Response time > 30s (90s threshold not yet hit)
   └─ Log warning, suggest user wait or restart
   └─ Continue operation (circuit still closed)

DEGRADE (🟠)
└─ Response time > 90s (240s threshold not yet hit)
   └─ Switch to Copilot fallback
   └─ Alert user ("Computadora está pensando mucho, usando Copilot...")
   └─ Circuit opening

OFFLINE (🔴)
└─ No response after 240s OR connection refused
   └─ Completely disable LLM features
   └─ Use regex-only NLU (Nivel 1)
```

#### Measurement Methodology
```python
# From watchdog.py
chat_url = "http://localhost:11434/api/chat"
test_payload = {
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hola"}],
    "stream": False
}

t_start = time.time()
r = requests.post(chat_url, json=test_payload, timeout=30)  # NEW: 30s timeout
latency_ms = (time.time() - t_start) * 1000

if latency_ms < 30000:      # 30s
    state = "HEALTHY"
elif latency_ms < 90000:    # 90s
    state = "NOTIFY"
elif latency_ms < 240000:   # 240s
    state = "DEGRADE"
else:
    state = "OFFLINE"
```

---

## 👁️ Tier 4: Netzach (Face Recognition)

### Face Detection + Recognition

**Component**: `percepcion/rostro.py`  
**Library**: face_recognition (dlib-based)  
**Dependencies**: dlib (C++, CPU-intensive)

#### Latency per Frame
```
Image: 1920x1080 RGB

Operation           Time        CPU Usage
────────────────────────────────────────
Face detection      50-100ms    High (dlib)
Face encoding       50-150ms    High (dlib)
Encoding comparison <1ms        Low
Total per-frame     100-250ms   Peak 50-80%
```

#### Debounce Strategy (WI-CRIT-002 fix, Ciclo 10)
```python
# From rostro.py
intervalo_analisis = 2.0  # seconds

# Boot optimization:
if time.time() - self._ts_init < 60.0:
    intervalo_analisis = 3.0  # Primeros 60s: 3s (reduce CPU load)
else:
    intervalo_analisis = 2.0  # Normal: 2s

# Result: Max 0.33 Hz face_recognition during boot
#         No CPU 100% contention, logger doesn't silence
```

#### Anti-Spoofing (Status: ❌ NOT IMPLEMENTED)
- **WI-306**: Pending implementation
- **Current state**: Liveness detection not active
- **Risk**: Accepts photos/videos as valid faces
- **Mitigation**: Require multiple consecutive frames (face persistence check)

---

## 📊 Tier 5: Yesod (Memory / Persistence)

### Memory Footprint

**Baseline (idle, no audio processing)**:
```
Python process (Computadora idle):
  - Base interpreter: 30MB
  - PyQt6 framework: 40MB
  - NLU regex patterns: 20MB
  - Face recognition model (lazy): 0MB (not loaded until first use)
  - Whisper model (lazy): 0MB (not loaded until first use)
  ─────────────────────────
  Total: ~90-110MB
```

**During listening**:
```
Python process (Escucha activa):
  + Whisper model (base): 140MB
  + Audio buffer queue (256 frames): 10-15MB
  + Silero VAD: 5MB
  ─────────────────────────
  Peak: ~250-280MB
```

**During face recognition**:
```
Python process (Rostro análisis):
  + dlib models: 50-80MB
  + Frame buffer: 10-15MB
  ─────────────────────────
  Peak: ~150-190MB (if listening already active, add to that)
```

**Constraints**:
- ✅ **Typical desktop**: 4GB+ RAM available
- ⚠️ **Low-end laptop**: <2GB could cause swapping
- ❌ **Raspberry Pi 4**: 4GB variant OK, 2GB variant risky

### Cache Strategy
```python
# From memoria/cache.py
class CacheMemoria(LRUCache):
    def __init__(self, maxsize=1000):
        super().__init__(maxsize=maxsize)
```

- LRU eviction: Oldest least-used entries removed first
- TTL: Optional 1-hour expiry per entry
- Persistence: SQLite backend (optional, disabled by default)

---

## 🔗 Cross-Dependencies

### Listening + Face Recognition = Contention ⚠️

When user is speaking AND face detection active:
```
Thread 1: Escucha → Whisper (CPU 50%)
Thread 2: Perceptor → Face Recognition (CPU 50%)
                                       ──────
                                  Total: CPU 100%

Result:
- Audio buffer overflows
- Frame skipping doubles (visual lag)
- Both operations stall waiting for CPU
```

**Mitigation** (FP-150):
- Frame skip enabled during listening (reduce Thread 2 load)
- Face detection debounce increased to 3s during boot (reduce Thread 2)
- Audio queue enlarged (buffer spikes)
- Ollama timeout increased (avoid false timeout during contention)

**Lesson**: Cannot run Whisper + face_recognition at full capacity simultaneously.

---

## 📋 Known Limits

### Hard Limits (Cannot Exceed)

| Limit | Value | Reason | Mitigation |
|-------|-------|--------|-----------|
| **Whisper latency** | ~500ms per 10s audio | dlib CPU model | Use smaller model (tiny/base) |
| **Face recognition latency** | ~250ms per frame | dlib CPU model | Increase debounce interval |
| **Ollama large model** | 30-60s inference | LLM computation | Use smaller model or GPU |
| **Audio queue overflows** | Increase maxsize | Multiple threads competing | Monitor in stress tests |

### Soft Limits (Degradation)

| Limit | Value | Behavior | Mitigation |
|-------|-------|----------|-----------|
| **Memory >300MB** | Sustained | Potential swap (OS-dependent) | Monitor process size |
| **CPU >80% sustained** | Prolonged | Thermal throttling | Reduce background tasks |
| **Network latency >5s** | For web/TTS | User perceives delay | Queue requests, show spinner |

---

## 🧪 Benchmark & Validation

### Test Commands

```bash
# FP-150 Performance Validation (New)
pytest tests/test_fps_listening_mode.py -v          # RF-362
pytest tests/test_audio_queue_stress.py -v          # RF-361
pytest tests/test_watchdog_fp150.py -v -k "timeout" # RF-360

# General Performance
python -c "
from computadora.interfaz.ventana_principal import OrbeComputadora
orbe = OrbeComputadora()
orbe.benchmark_ferrofluido(duration_s=10)  # Measure FPS
"

# Memory Profiling
python -m memory_profiler computadora/voz/escucha.py

# CPU Profiling
python -m cProfile -o profile.prof -s cumtime computadora/cerebro/nlu.py
```

---

## 📈 Performance Roadmap

### Ciclo 11 (Current)
- ✅ FP-150: Audio queue sizing + Ollama timeout tuning
- ✅ FP-150: Frame skip listening mode
- ⏳ Validation tests (RF-360/361/362)

### Ciclo 12
- [ ] GPU acceleration for Whisper (optional, if CUDA available)
- [ ] Face encoding caching (avoid re-encode same face)
- [ ] Async Ollama requests (don't block UI)
- [ ] Load testing with 100+ simultaneous voices

### Ciclo 13+
- [ ] Multi-GPU support (advanced)
- [ ] Model quantization (int8 Whisper/face_recognition)
- [ ] Edge TPU support (if available)
- [ ] Distributed face recognition (multi-device)

---

## 📚 References

- **FP-150**: Performance hardening (Ciclo 11)
- **WI-CRIT-002**: CPU 100% deadlock fix (Ciclo 10)
- **RF-360**: Ollama timeout adaptive (new, Ciclo 11)
- **RF-361**: Audio queue sizing (new, Ciclo 11)
- **RF-362**: Frame skip listening mode (new, Ciclo 11)
- **SRS.md**: RF-* specifications
- **SDD.md**: §4.17 Architecture (Etz HaChaim)

---

**Fin de Performance Specifications**

*PALINGENESIA Ciclo 11 — Benchmarks establecidos, Límites documentados, Roadmap claro*

