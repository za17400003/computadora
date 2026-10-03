# NIGREDO — Análisis de 4 Problemas Nuevos (Junio 1, 2026 12:57-12:59)

## Problema 1: Anillos Girando en el Mismo Lado ❓

### Usuario reporta
"todos los anillos girando hacia el mismo lado" — esperaba torque +/-.

### Código Esperado
Línea 1320-1321 de [ventana_principal.py](computadora/interfaz/ventana_principal.py#L1320-L1321):
```python
self._rot_anillo1 += (0.03 * 60) * _rot_mod * delta_t  # CW (+)
self._rot_anillo2 -= (0.02 * 60) * _rot_mod * delta_t  # CCW (-)
```

**¿Cuál es el problema?**
- Si ambos se incrementan: ✅ Código está correcto, debería funcionar
- Si ambos se decrementan: ❌ Ambos irían al mismo lado
- Si hay acumulación de error o reset incorrecto: ❌ Podrían verse igual

### Hipótesis
Necesito VERIFICAR en runtime:
- ¿Qué valores tiene _rot_anillo1 vs _rot_anillo2 durante "procesando"?
- ¿El -=está realmente restando o se está ignorando?
- ¿Los ángulos se están reseteando a 0?

---

## Problema 2: Loop Infinito de Transcripción (CRÍTICO) ❌

### Evidencia en Logs
```
12:58:03 | INFO | 🎙️ _transcribir() INICIADO: 11 chunks
12:58:05 | INFO | 🎙️ _transcribir() INICIADO: 14 chunks
12:58:08 | INFO | 🎙️ _transcribir() INICIADO: 20 chunks
12:58:25 | INFO | 🎙️ _transcribir() INICIADO: 19 chunks
12:58:38 | INFO | 🎙️ _transcribir() INICIADO: 96 chunks  ← EXPLOSION
12:58:59 | INFO | 🎙️ _transcribir() INICIADO: 120 chunks ← MÁS
12:59:11 | INFO | 🎙️ _transcribir() INICIADO: 56 chunks
```

**Diagnóstico**: `_transcribir()` se está llamando **EN PARALELO** sin sincronización, acumulando chunks:
- 11 chunks = ~0.7s de audio
- 14 chunks = ~0.9s
- 96 chunks = ~6s (!)
- 120 chunks = ~7.5s (!)

**Causa Raíz**: Hay múltiples threads llamando `_transcribir()` simultáneamente, o hay un loop que sigue acumulando chunks.

**Impacto**:
- GPU/CPU sobrecargados transcribiendo 96-120 chunks (7.5s de audio por frame)
- Causa FPS drops de 31→28 FPS
- Retraso respuesta: 102 segundos (12:58:03 → 12:59:45)

---

## Problema 3: FPS Drops 50% (28-29 FPS vs 31-32) ❌

### Evidencia
```
12:58:39 | WARNING | Frame slow detected: 64/90 lentos, avg FPS: 22.3
12:58:41 | WARNING | Frame slow detected: 65/120 lentos, avg FPS: 26.5
12:58:42 | WARNING | Frame slow detected: 78/150 lentos, avg FPS: 31.2
...
12:59:07 | WARNING | Frame slow detected: 316/600 lentos, avg FPS: 32.0
```

**Patrón**: 
- 22-26 FPS cuando hay 96+ chunks en transcripción
- 31-32 FPS cuando actividad es normal
- **50% de frames lentos** durante picos de transcripción

### Causa
1. Whisper está siendo llamado con 96/120 chunks = MUCHO trabajo
2. Cpu/GPU bloqueado en Whisper mientras se intenta renderizar UI
3. Resultado: render drops a 28-30 FPS mientras Whisper procesa

---

## Problema 4: Ollama Timeout 102 Segundos (12:58:03→12:59:45) ❌

### Timeline en Logs
```
12:58:03 | INFO | Procesando: 'Hola, ¿cómo te sientes?'  ← INPUT
12:58:03 | INFO | Cerebro activado: nivel2
12:58:13 | WARNING | Ollama streaming retornó 500  ← Intenta de nuevo
12:59:45 | ERROR | Timeout esperando a Ollama  ← 102 segundos después
12:59:45 | INFO | Respuesta: 'Estoy de buen ánimo, señor...'
```

**¿Qué pasó?**
1. Usuario pregunta a las 12:58:03
2. Ollama devuelve error HTTP 500 ("Ollama streaming retornó 500")
3. Sistema intenta fallback a transcripción simple (12:58:25+)
4. Whisper está sobrecargado (96+ chunks)
5. Timeout alcanzado, fallback a respuesta local (12:59:45)

**Causa**: Ollama está LENTO o CAÍDO, pero además Whisper está congestionado.

---

## Relaciones Entre Problemas

```
Loop Transcripción → Chunks 96-120 →  Whisper GPU sobrecargo → FPS drops
        ↓
   Whisper lento → Atraso procesamiento → Ollama timeout → Respuesta tarda 102s
```

**El problema RAÍZ es: _transcribir() se llama múltiples veces sin sincronización.**

---

## Próximas Investigaciones ALBEDO

1. **Anillos**: Búscar en código dónde se resetean _rot_anillo1/_rot_anillo2
2. **Transcripción**: Buscar dónde `_transcribir()` se llama múltiples veces  
3. **Sincronización**: ¿Hay flag de "transcribiendo" que evite llamadas paralelas?
4. **FPS**: Confirmar que Whisper está en thread separado

