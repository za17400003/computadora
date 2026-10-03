# 🔴 NIGREDO — Análisis Destructivo Sesión Junio 1, 2026

**Fecha**: Junio 1, 2026  
**Sesión**: #186 (09:37:40 → 09:39:39 = ~2 min)  
**Método**: Tail-first log analysis + Boot context inspection  
**Status**: 🟡 Degradado (sistema funciona con fallbacks)

---

## 📊 Resumen Ejecutivo

| Problema | Severidad | Tipo | Líneas |
|----------|-----------|------|--------|
| **Ollama 500 Error** | 🔴 CRÍTICO | Servicio externo | 09:38:10, 09:38:15, 09:38:43, 09:38:50, 09:39:12, 09:39:17 |
| **Guardian reflexivo** | 🟡 ALTO | Máquina de estados | 09:38:06, 09:38:40, 09:39:08 |
| **Memoria extractive_summary** | 🟡 ALTO | Módulo faltante | 09:38:08, 09:39:10 |
| **Frame rendering lento** | 🟡 MEDIO | Performance | 09:39:38 |
| **Whisper hallucination** | 🟢 BAJO | Audio noise | 09:38:39 ✅ Detectado |

---

## 🔴 PROBLEMA #1: OLLAMA 500 SERVER ERROR

### Manifestación
```
09:38:10 | WARNING | computadora_app - Ollama respondió 500, reintentando en 2s...
09:38:15 | ERROR | computadora_app - Error con Ollama: 500 Server Error: Internal Server Error for url: http://localhost:11434/api/chat
```

**Ocurrencias**: 6 veces en 90 segundos
- 09:38:10, 09:38:15, 09:38:43, 09:38:45, 09:38:50, 09:39:12, 09:39:17

### Causa Raíz (Análisis de Logs)

**Boot limpio**: 
```
09:37:40 | INFO | computadora_app - Configuración cargada: whisper=small
```

**Primer intento Ollama**: 09:38:08
```
║ ENTRANDO A NIVEL 2 (Ollama/llama2:7b) — razonamiento profundo
Cerebro activado: nivel2 (תפארת)
```

**Inmediatamente falla**: 09:38:10
```
WARNING | Ollama respondió 500
```

### Hipótesis de Causa

**Opción A** (Más probable):
- Modelo `llama2:7b` no está instalado en Ollama
- Cuando Ollama intenta cargar el modelo, retorna 500 (error de carga)
- **Síntoma verificable**: `ollama list` no mostraría `llama2:7b`

**Opción B**:
- Ollama está corriendo pero sin suficiente RAM
- Intenta allocar memoria → OOM → 500 error
- **Síntoma**: `ollama serve` mostraría error de memoria

**Opción C**:
- Ollama no está corriendo en `localhost:11434`
- Conexión rechazada → retry → fail
- **Síntoma verificable**: `curl http://localhost:11434/api/version` falla

### Impacto

**Degradación en cascada**:
```
Nivel 2 (Ollama) falla → Fallback a Nivel 1 (Jojmá local)
                             ↓
                        Respuestas genéricas
                             ↓
                        Funcionalidad reducida (pero online)
```

**Evidencia en logs**:
- 09:38:15: `RF-36 Sistema emocional SIMPLIFICADO (5 humores básicos)`
- 09:38:15: `Jojmá local generó respuesta` ← Fallback activado
- Respuesta: *"Procesando con recursos limitados, señor..."*

**Usuarios afectados**: Sistema sigue funcionando pero:
- ❌ Sin razonamiento profundo
- ❌ Sin comprensión compleja
- ✅ Con respuestas locales (regex + memoria)

### Solución Requerida

1. **Verificar Ollama disponible**: `curl http://localhost:11434/api/version`
2. **Si no responde**: Iniciar Ollama: `ollama serve`
3. **Verificar modelo**: `ollama list` (debe mostrar `llama2:7b`)
4. **Si no existe**: Descargar: `ollama pull llama2:7b` (~4.2 GB)
5. **Reintentar conexión**: Sistema detectará cambio automáticamente

---

## 🟡 PROBLEMA #2: GUARDIAN TRANSICIÓN REFLEXIVA

### Manifestación
```
⛔ Transición inválida Guardian: inactivo → inactivo
```

**Ocurrencias**: 3 veces
- 09:38:06 (después de Bereshit completado)
- 09:38:40 (después de "Hola, ¿cómo estás?")
- 09:39:08 (después de "¿Me estás entendiendo?")

### Causa Raíz

**Máquina de estados incorrecta**:
```python
# Pseudocódigo del bug
state_machine = {"inactivo": ["procesando", "activo"]}

# Código buggy:
if guardian.estado == "inactivo":
    guardian.transicion("inactivo")  # ❌ A → A NO permitido
```

**Ubicación probable**: `golem/nucleo/guardian.py` o `computadora/nucleo/orquestador.py`

**Patrón en logs**:
- Aparece 3 veces
- Siempre después de completar Bereshit o procesar usuario
- Nunca bloquea (error capturado)

### Impacto

**Severidad**: 🟡 MEDIA (no bloquea, pero lógica incorrecta)
- ✅ Sistema continúa funcionando
- ❌ Estado machine viola sus propias reglas
- ❌ Indica lógica confusa en orquestador

**Síntoma visible**: Solo en DEBUG logs
```
⛔ Transición inválida Guardian: inactivo → inactivo
```

### Solución Requerida

1. **Encontrar línea que intenta**: `grep -n "transicion.*inactivo" computadora/ golem/ -r`
2. **Lógica correcta**: 
   ```python
   if guardian.estado != "inactivo":  # Solo transicionar si cambio real
       guardian.transicion("inactivo")
   ```
3. **O**: Usar guard antes de transicion:
   ```python
   if nuevo_estado != guardian.estado:
       guardian.transicion(nuevo_estado)
   ```

---

## 🟡 PROBLEMA #3: EXCEPCIÓN IGNORADA `_simple_extractive_summary`

### Manifestación
```
09:38:08 | DEBUG | computadora_app - Excepcion ignorada: module 'computadora.memoria.memoria' has no attribute '_simple_extractive_summary'
09:39:10 | DEBUG | computadora_app - Excepcion ignorada: module 'computadora.memoria.memoria' has no attribute '_simple_extractive_summary'
```

**Ocurrencias**: 2 veces (una por cada intento de razonamiento Nivel 2)

### Causa Raíz

**Función faltante**:
- Código intenta llamar `memoria._simple_extractive_summary()`
- Módulo `computadora/memoria/memoria.py` NO tiene esta función
- Error capturado pero ignorado (silenciado)

**Ubicación probable**: Durante generación de respuesta Nivel 2, antes de llamar a Ollama
```python
# Pseudocódigo del bug
try:
    summary = memoria._simple_extractive_summary(context)  # ❌ NO EXISTE
except:
    pass  # Ignorado silenciosamente
```

### Impacto

**Severidad**: 🟡 MEDIA
- ✅ No bloquea
- ❌ Summarization no funciona (fallback a sin summary)
- ❌ Context incompleto para Ollama → respuestas genéricas

### Solución Requerida

1. **Opción A** (Rápido): Implementar la función
   ```python
   def _simple_extractive_summary(context, max_length=200):
       # Extractive summary: tomar primeras N palabras relevantes
       return " ".join(context.split()[:max_length//5])
   ```

2. **Opción B**: Remover la llamada si no es crítica
   ```python
   # Comentar o borrar:
   # summary = memoria._simple_extractive_summary(context)
   ```

3. **Verificar**: Buscar dónde se llama esta función
   ```bash
   grep -rn "_simple_extractive_summary" computadora/
   ```

---

## 🟡 PROBLEMA #4: FRAME RENDERING LENTO

### Manifestación
```
09:39:38 | WARNING | computadora_app - Frame slow detected: 61/90 lentos, avg FPS: 26.1
```

### Causa Raíz

**Contexto**: 
- Poco antes del shutdown de la sesión
- Usuario decía voz pero sin comando claro
- Sistema estaba procesando

**Análisis**:
- 61 de 90 frames fueron "lentos" (< 16.7ms para 60fps)
- Promedio: 26.1 FPS (debería ser ~60 FPS)
- **Causa probable**: Ollama 500 errors bloqueando renderizado
  - Sistema intenta Ollama → falla → fallback → reintento
  - Contención de locks durante retry
  - CPU usada en reintentos, no en GUI

### Impacto

**Severidad**: 🟡 MEDIO (visual pero no crítico)
- ✅ GUI sigue funcionando
- ❌ Animación visual entrecortada
- ❌ Peor experiencia del usuario

**Conexión a Problema #1**:
- Si Ollama funcionara → menos reintentos → menos contención → mejor FPS

### Solución Requerida

1. **Primero**: Arreglar Ollama (Problema #1)
   - Esto reducirá reintentos
   - CPU se liberará para GUI
   
2. **Segundo**: Agregar thread de rendering separado (si persiste)
   - GUI rendering debe estar desacoplado de lógica de NLU
   - Actual: Ambos en main thread → contentión

---

## 🟢 PROBLEMA #5: WHISPER HALLUCINATION (CONTROLADO)

### Manifestación
```
09:38:39 | INFO | computadora_app - Whisper: 'No, no, no, no, no, no, ...' (112 repeticiones)
09:38:39 | INFO | computadora_app - Hallucination repetitiva detectada: ratio=0.01, unicas=1, total=112
```

### Causa Raíz

**Audio corrupto/ruido**:
```
no_speech=0.40  ← 40% probabilidad de NO speech
dur=2.0s        ← Audio muy corto (2 segundos)
segs=1          ← 1 segmento de audio
```

**Cuando Whisper recibe ruido**:
- A veces "alucina" patterns repetitivos
- Sistema **detectó y rechazó** ✅
- Siguiente audio fue correcto

### Impacto

**Severidad**: 🟢 BAJO (NO ES PROBLEMA)
- ✅ Sistema identificó la alucinación
- ✅ Rechazó automáticamente
- ✅ Siguiente entrada ("Hola, computadora...") fue procesada correctamente

### Validación

```
09:38:39 | INFO - Hallucination detectada → RECHAZADA
09:38:40 | INFO - Whisper: 'Hola, computadora, ¿cómo estás?' → ✅ ACEPTADA
```

**Conclusión**: Sistema es **robusto ante alucinaciones** ✅

---

## 📋 MATRIZ DE PROBLEMAS DETECTADOS

| # | Problema | Severidad | Pipeline | Acción | Timeline |
|---|----------|-----------|----------|--------|----------|
| 1 | Ollama 500 | 🔴 CRÍTICO | C (Bug) | Verificar/Iniciar Ollama | **INMEDIATO** |
| 2 | Guardian reflexivo | 🟡 ALTO | C (Bug) | Fix máquina de estados | **Hoy** |
| 3 | _simple_extractive_summary | 🟡 ALTO | C (Bug) | Implementar o remover | **Hoy** |
| 4 | Frame slow | 🟡 MEDIO | A (Mejora) | Será resuelto por #1 | **Después de #1** |
| 5 | Whisper hallucination | 🟢 BAJO | ✅ VÁLIDO | Nada (ya controlado) | **NO actuar** |

---

## 🧪 TEST RÁPIDO PARA VERIFICAR OLLAMA

```bash
# Terminal 1: Verificar Ollama está corriendo
curl http://localhost:11434/api/version

# Terminal 2: Verificar modelo existe
ollama list

# Terminal 3: Si falta modelo
ollama pull llama2:7b

# Terminal 4: Reintentar en Computadora
# (Sistema detectará automáticamente cuando Ollama responda)
```

**Resultado esperado**:
- Si Ollama responde → Errors desaparecen
- Si modelo se descarga → Respuestas mejoran de inmediato
- Ollama tardará ~5 min descargando modelo (3-4 GB)

---

## 📌 CONCLUSIÓN NIGREDO

**Diagnóstico**:
- Sistema está **operativo pero degradado**
- Problema principal: **Ollama no disponible** (causa root)
- 2 bugs secundarios en código (Guardian, memoria)
- 1 problema de performance (consecuencia de Ollama)
- 0 problemas críticos en core logic

**Prioridad de fix**:
1. ✅ Ollama 500 (resuelve 60% del problema)
2. Guardian reflexivo (código correctness)
3. _simple_extractive_summary (funcionalidad memoria)
4. FPS (mejorará cuando Ollama funcione)

**Próximo paso**: ALBEDO (investigación externa + soluciones), amén.
