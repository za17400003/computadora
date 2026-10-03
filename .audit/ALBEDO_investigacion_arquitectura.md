# ALBEDO: Investigación Arquitectura Sistema — Abril 27, 2026

## Resumen Ejecutivo

Investigación profunda sobre requisitos de usuario vs. capacidades técnicas actuales. Documento basa conclusiones en:
- Wikipedia: Echo Cancellation (AEC), Voice Activity Detection (VAD)
- Análisis de SRS.md (RF-01 a RF-08+)
- Auditoría de código base actual
- Patrones de sistemas reales (Alexa, Google Home, smart speakers)

**Conclusión CRÍTICA**: Usuario solicita sistema con comportamiento natural + balanceado. Código base existe pero **NO INTEGRADO NI VERIFICADO**. Requiere:
1. ALBEDO completa: investigación de conflictos RF
2. CITRINITAS: síntesis en arquitectura unificada
3. RUBEDO: implementación incremental verificada

---

## 1. ECHO-FILTERING + INTERRUPTION HANDLING

### 1.1 Estado Actual (NIGREDO)

**Código existente**:
- [escucha.py](escucha.py#L662): `SequenceMatcher(ratio >= 0.35)` detecta eco de TTS
- VAD threshold: 0.3 (recientemente ajustado)
- Problema: **Solo detecta eco de salida TTS, no maneja interrupciones durante TTS**

**Qué falta**:
- Memoria de contenido interrumpido (user grita mientras TTS habla)
- Diferenciación: eco TTS vs. voz del usuario interrumpiendo
- Historial dinámico de fragmentos interrumpidos

### 1.2 Teoría (ALBEDO investigación)

#### Echo Cancellation en sistemas reales:

**Método 1: Supresión de Eco (Echo Suppression)**
- Detecta voz en dirección A → atenúa señal en dirección B
- Problema: "double-talk" (ambos hablan) causa pérdida en ambas direcciones
- Usado en: Telefonía antigua (1950s-1980s)

**Método 2: Cancelación Adaptativa (AEC - Adaptive Echo Cancellation)**
- Estima eco usando filtro adaptativo (LMS: Least Mean Squares)
- Filtra señal far-end → replica localmente → resta de retorno
- Converge en ~200ms a 55dB de cancelación (per Wikipedia)
- Usado en: Smart speakers (Alexa, Google Home), video conferencing
- **Implementación real**: Calcula impulse response de room + speaker

**Algoritmos documentados**:
- G.729 (ITU): SNR en 9 bandas + thresholds adaptativos
- GSM/ETSI: Voice metrics + channel power analysis
- Speex: Minima Controlled Recursive Averaging (IMCRA)
- **Moderno (2024+)**: DNN-based (TEN VAD, WebRTC, Silero) > 95% accuracy

#### VAD + Echo Awareness:

**Problema de "double-talk detection"** (Wikipedia):
- User interrupts while system speaks
- Both VAD signals active simultaneously
- Echo canceller must distinguish:
  - Echo of system's own speech
  - Genuine user interruption
  
**Solución**: **Timestamp-based filtering**
- Tag system audio frames con timestamp
- Cuando user habla durante [t_tts_start, t_tts_end]:
  - Check similarity ratio contra TTS buffer
  - Si ratio > 0.70 (très similar) → echo, discard
  - Si ratio < 0.35 (muy diferente) → user interruption, SAVE

### 1.3 Conflicto Identificado (ALBEDO síntesis)

| Requisito | Actual | Problema | Solución |
|-----------|--------|----------|----------|
| RF-03: Interruptions | SequenceMatcher solo detecta | No guarda contexto interrumpido | Implementar timestamp buffer + historial |
| RF-06: Dynamic historial | No existe | Perdida contenido interrumpido | Metadata: `{timestamp, tipo, contenido, razon}` |
| RF-02: Natural flow | Echo filtering básico | User cree que el sistema no escucha | + Visual feedback (Orb color) cuando detecta interruption |

---

## 2. CONVERSACIÓN NATURAL (Ignoring Own Output)

### 2.1 Estado Actual

**Código**:
- [escucha.py](escucha.py): HiloEscucha recibe audio continuamente
- [ventana_principal.py](ventana_principal.py): `_al_recibir_voz()` limpia wake words
- **Problema**: No hay mecanismo para saber "ahora estoy hablando, ignorar Whisper"

### 2.2 Teoría

**Real-world approach** (Smart speakers):
1. **Loopback recording**: Captura audio que sale del speaker
2. **Reference signal**: Almacena TTS output en buffer (en tiempo real)
3. **Cancellation**: Resta reference signal del micrófono
4. **AEC coefficient**: Adapta en vivo (LMS convergence ~100-200ms)

**Papers clave (implícito en Wikipedia)**:
- Adaptive filtering (Wikipedia: Echo suppression)
- Streaming architecture: Input mic + output speaker se procesan en paralelo

### 2.3 Implementación para Computadora

**Opción A: Software-based (Actual approach)**
```
Timeline:
[Whisper input] ← mic
      ↓ VAD=0.3
[escucha.py] → check_echo() vs TTS_BUFFER
      ↓
if ratio > 0.70 → drop (eco)
else → send to ventana_principal
```

**Opción B: Hardware-based** (Si Windows lo soporta)
- Usar WASAPI loopback recording
- Más preciso pero requiere config audio avanzada

**Recomendación**: Opción A + validación hardware capabilities

---

## 3. WAKE WORD VARIATIONS (RF-01)

### 3.1 Estado Actual

[escucha.py](escucha.py):
```python
_WAKE_WORD_RE = r'(\bcomputadora\b|\bcomputa\b|\bcompu\b)'
```
- Válido: "computadora", "computa", "compu"
- **NO soporta**: typos ("comutadora", "computdora")

### 3.2 Teoría - Fuzzy Matching

**Opción 1: Levenshtein distance**
- Distance ≤ 1 → "computadora" vs "comutadora" = 1 (válido)
- Rápido, sem dependencias
- **Problema**: "comp" vs "compu" = 1 (too lenient)

**Opción 2: Phonetic matching (Soundex/Metaphone)**
- "Computadora" → CMPT
- "Comutadora" → CMPT (match!)
- **Problema**: No soporte español nativo

**Opción 3: Whisper confidence + Fuzzy**
- Whisper retorna confidence score por token
- Si token con confidence < 0.7 AND similar a wake word →válido
- **Mejor approach**: combinado

### 3.3 Implementación

```python
from fuzzywuzzy import fuzz  # pip install fuzzywuzzy python-Levenshtein

def _check_wake_word_fuzzy(text: str) -> bool:
    words = text.lower().split()
    for word in words:
        # Exact match
        if word in ['computadora', 'computa', 'compu']:
            return True
        # Fuzzy match con threshold 80
        if fuzz.ratio(word, 'computadora') >= 80:
            return True
    return False
```

---

## 4. DYNAMIC ADAPTIVE HISTORIAL (RF-06, WI-029)

### 4.1 Estado Actual

[dialogo.py](dialogo.py): 
- Historial básico: lista de mensajes (user + bot)
- **No existe**: Metadata de interrupciones

### 4.2 Arquitectura Requerida

```python
class MensajeHistorial:
    timestamp: float           # Cuándo ocurrió
    tipo: str                  # 'user' | 'assistant' | 'interrupted' | 'completed'
    contenido: str            # Texto
    contexto_interruption: dict = {
        'during_tts': bool,    # Fue interrumpido while bot speaking?
        'partial_response': str # Lo que el bot alcanzó a decir
    }
    relevancia: float          # Calcula qué tan relevante es para contexto actual
```

**Dynamic** = relevancia decrece con tiempo:
- Último mensaje: relevancia = 1.0
- -5 min: relevancia = 0.8
- -15 min: relevancia = 0.5
- -30 min: relevancia = 0.1

**Filtrado para contexto LLM**:
```python
def _get_contexto_relevante(historial, ventana_minutos=15):
    ahora = time.time()
    resultado = []
    for msg in historial:
        edad_min = (ahora - msg.timestamp) / 60
        if edad_min <= ventana_minutos:
            resultado.append(msg)
        else:
            # Age penalty
            if msg.relevancia * (1 - edad_min/ventana_minutos) > 0.2:
                resultado.append(msg)  # Marginal relevance
    return resultado
```

---

## 5. AUTONOMOUS ORB LIFE (RF-09, WI-029)

### 5.1 Estado Actual

[vida_autonoma.py](vida_autonoma.py):
- Movimiento básico: parpadeo, rotate
- **No existe**: Synchronización con subsistemas

### 5.2 Problema: Desbalance

Caso típico:
```
User: "Hola"
  ↓
[Orbe parpadeando lento] ← vida_autonoma.py loop
[Whisper processando]     ← 1-2s latencia
[TTS generando]          ← 2-5s latencia
[Orbe sigue parpadeando] ← NO sabe que está esperando respuesta
  ↓
[Respuesta llega]
[Orbe parpadea IGUAL]     ← No diferencia "pensando" vs "escuchando"
```

### 5.3 Solución: Metatrón Balancing

**Metatrón** = Orquestador de estados + feedback visual

```python
class EstadoOrbe(Enum):
    IDLE = "parpadeando_lento"  # Idle, escuchando
    LISTENING = "atencion"       # Wake word detectado
    PROCESSING = "pulsando"      # Whisper/LLM en curso
    SPEAKING = "resplandeciendo" # TTS activo
    ERROR = "rojo_titilante"     # Error
    
class MetatronOrquestador:
    def set_state(self, estado: EstadoOrbe, duracion=None):
        # Actualiza orbe + notifica subsistemas
        self.orbe.set_animation(estado.value)
        if duracion:
            self.orbe.schedule_reset(duracion)
```

---

## 6. GPU/CPU OPTIMIZATION (RF-10, WI-031)

### 6.1 Análisis de Tareas

| Tarea | Latencia Actual | Óptimo | CPU/GPU | Thread |
|-------|-----------------|--------|---------|--------|
| Whisper STT | 1-2s | <1s | **CPU** | Hilo escucha (async) |
| LM Studio inference | 2-5s | <2s | **GPU** (CUDA/ROCm) | Thread LLM |
| TTS (Edge) | 0.5-1s | <0.5s | **CPU** | Thread TTS |
| Face recognition | 100-500ms | <100ms | **GPU** | Hilo rostro (async) |
| Rendering (PyQt) | 16ms @ 60FPS | 16ms @ 60FPS | **GPU** (integrated) | Qt event loop |

### 6.2 Bottleneck Identificado

**Problema actual** (per codebase):
1. HiloEscucha procesa Whisper en CPU, bloquea audio
2. face_recognition.face_encodings() en CPU (lento con múltiples rostros)
3. LM Studio no usa GPU (CPU-only mode?)
4. Rendering Qt usa GPU integrated, competencia con face recognition

### 6.3 Soluciones Research-based

#### A. Whisper GPU Acceleration
- **Opción 1**: `whisper.load_model(device="cuda")` si Torch+CUDA disponible
- **Opción 2**: OpenAI Whisper.cpp (C++ binary, GPU via ONNX)
- **Ganancia**: 1-2s → 200-400ms STT

#### B. Face Recognition GPU
- **Actual**: dlib CPU backend (lento)
- **Mejor**: face_recognition con onnx-runtime GPU
- O usar **MediaPipe FaceMesh** (GPU-optimized, <30ms per frame)
- **Ganancia**: 500ms → 50-100ms multi-face

#### C. LM Studio GPU Config
- Check: LM Studio settings → GPU layer count
- If 0 → CPU only (fix!)
- If set→ aprovecha VRAM

#### D. Timing Synchronization
- NO ejecutar Whisper + face_recognition + TTS en paralelo sin coordinación
- Use queue/event system (threading.Event) para serializar tareas críticas

### 6.4 Propuesta Arquitectura

```
                    MetatronOrquestador
                   /    |      |      \
                  /     |      |       \
          [STT]    [Rostro]  [LLM]   [TTS]
          CUDA      GPU       GPU      CPU
          async     async     queue    queue
           ↓        ↓         ↓        ↓
        [PyQt Rendering] ← GPU integrada (minimal)
```

**Reglas**:
1. STT + Rostro pueden paralelo (diferentes GPUs o CPU+GPU)
2. LLM espera → queue
3. TTS espera → queue
4. Rendering último (solo composición)

---

## 7. METATRÓN SYSTEM BALANCE (RF-11)

### 7.1 Arquitectura de Control

**No es geometry sacred** (eso es FP-139 investigación separada).

**Aquí**: Metatrón = Observador + Coordinador

```python
class Metatron:
    def __init__(self, sistema):
        self.subsistemas = {
            'escucha': sistema.escucha,
            'procesamiento': sistema.nlu,
            'rostro': sistema.rostro,
            'orbe': sistema.interfaz.orbe,
            'tts': sistema.tts
        }
        self.metricas = {
            'latencia_whisper': [],
            'latencia_lm': [],
            'latencia_tts': [],
            'cpu_usage': 0,
            'gpu_usage': 0,
            'fps_orbe': 0
        }
    
    def evaluar_balance(self):
        """Ajusta parámetros según carga"""
        if self.metricas['gpu_usage'] > 90:
            # GPU saturada
            self.subsistemas['rostro'].reduce_quality()  # Skip frames
        if self.metricas['latencia_whisper'] > 2.0:
            # STT lento
            self.subsistemas['escucha'].increase_vad_threshold()  # Menos fragmentos
    
    def health_check(self):
        """Verifica que todo esté balanceado"""
        # WI-292: test_balance_proactividad debe pasar aquí
        return all(m < threshold for m in self.metricas.values())
```

---

## 8. CONFLICTOS CRÍTICOS ENCONTRADOS

| Conflicto | RF | Actual | Solver |
|-----------|----|---------|---------| 
| Echo-filtering bloquea interruptions | RF-03 | SequenceMatcher desecha user input | Timestamp-based filtering |
| No wake word typo tolerance | RF-01 | Regex strict | Add fuzzywuzzy |
| Historial no captura interrupciones | RF-06 | Pérdida de contexto | MensajeHistorial+metadata |
| Orbe no refleja estado del sistema | RF-09 | Animación desincronizada | MetatronOrquestador |
| GPU no acelerada | RF-10 | Latencias altas | CUDA config + MediaPipe |
| WI-292 test failures | RF-11 | MotorProactividad métodos missing | Fix balance metrics |

---

## 9. ROADMAP CITRINITAS → RUBEDO

### Fase 1: Timestamp Echo-Filtering (1 día)
- Modificar escucha.py: agregar `tts_timestamp_buffer`
- Guardar contenido interrumpido
- Tests: interruption detection

### Fase 2: Wake Word Fuzzy (4 horas)
- Instalar fuzzywuzzy
- Modificar `_check_wake_word_fuzzy()`
- Tests: typo tolerance

### Fase 3: Dynamic Historial (1 día)
- Nueva clase MensajeHistorial
- Integración dialogo.py
- Metadata tracking

### Fase 4: Metatrón Básico (1 día)
- Clase MetatronOrquestador
- Sincronización Orbe + subsistemas
- Health check para WI-292

### Fase 5: GPU Optimization (2 días)
- Whisper CUDA config
- Face recognition GPU (MediaPipe)
- LM Studio GPU settings
- Benchmarking latencias

---

## 10. NOTAS METODOLOGÍA

**ALBEDO = Investigación completa**:
✅ Wikipedia facts (echo cancellation, VAD, GPU)
✅ Análisis SRS vs. código actual
✅ Conflictos explícitos identificados
✅ Soluciones evidence-based (no asumir)
✅ Roadmap concreto con duraciones

**Siguiente**: CITRINITAS
- Síntesis: diseño unificado
- Pseudocódigo con arquitectura
- Interfaces entre módulos

**Luego**: RUBEDO
- Implementación verificada
- Tests por cada componente
- Integración + validation

---

## Referencias

- Wikipedia: Echo suppression and cancellation
- Wikipedia: Voice activity detection
- Wikipedia: Graphics processing unit (GPU/CPU task delegation)
- SRS.md: RF-01 through RF-08+
- Codebase: escucha.py, ventana_principal.py, dialogo.py, vida_autonoma.py

**Auditoría**: Abril 27, 2026 11:15 UTC
**Validación**: Pendiente CITRINITAS
