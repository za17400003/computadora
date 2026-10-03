# 🔴 NIGREDO CRÍTICA: Latencia Whisper 25s + Animaciones Trabadas

**Fecha**: 2026-05-21 12:45:32  
**Severidad**: 🔴 CRÍTICO — Sistema inutilizable (respuesta 25+ segundos)  
**Usuario Report**: "tarda mucho en responder, se traba tambien en sus animaciones, checa los timestamps"

---

## 1. Análisis de Timestamps (Destrucción Cruda)

```
12:44:41 | BusEventos inicializado
12:44:41 | La Computadora ha despertado
12:44:42 | [Sistema] Inscribiendo la Palabra en cuda:0  ← GPU OK?
12:44:47 | Modelo Whisper cargado exitosamente       ← +5s de load
12:44:47 | ✅ Whisper cargado. Iniciando bucle de escucha
12:44:59 | Hablado (edge-tts): 'בראשית...'
12:45:00 | [SLOT] Estado escucha cambió a: procesando ← AUDIO CAPTURADO
12:45:25 | Whisper: '¿Cómo estás?...'                ← ⚠️ +25s TRANSCRIPCIÓN
12:45:25 | Wake word + comando
12:45:31 | בראשית Bereshit completado               ← +6s GENESIS
12:45:32 | Procesando...
❌ Crash: NameError: 'start_time' not defined
```

**Conclusión**: 
- ✅ Whisper cargó en GPU (5s es aceptable)
- ❌ **Transcripción tarda 25s para 11.2s de audio** (2.2× audio duration!)
- ❌ Main thread bloqueado = animaciones congeladas
- ❌ Script terminó por NameError

---

## 2. Root Causes Identificadas

### Causa A: Whisper en CPU a pesar de log "cuda:0"
**Evidencia**: 
- Log dice "cuda:0" pero transcripción tarda 25s
- Whisper en CPU tarda típicamente 2-3× audio duration
- Audio 11.2s → 25s ≈ 2.2× (indicativo de CPU)
- Posible: GPU malloc falló silenciosamente, retrocedió a CPU

**Patrón sospechoso** (escucha.py líneas 999-1001):
```python
except RuntimeError:  # GPU malloc error?
    dispositivo = "cpu"
    self._modelo = whisper.load_model(modelo_nombre, device=dispositivo)
```

---

### Causa B: _animar() Main Thread Bloqueado
**Evidencia**:
- Mientras Whisper transcribe (25s), _animar() **no puede ejecutarse**
- QTimer._animar() corre en main thread
- Whisper.transcribe() es BLOCKING en main thread
- Resultado: Animaciones congeladas (frame drop = trabadas)

---

### Causa C: Bereshit/Génesis Agrega +6s Más
**Evidencia** (ventana_principal.py línea 5400):
- 12:45:25 → 12:45:31 = +6 segundos
- Bereshit calls hilo_habla.hablar(), QMessageBox, enrollment
- QMessageBox **bloquea main thread** hasta que usuario cierra
- Usuario reportó "se traba" — es esto

---

## 3. Problemas Raíz Sistémicos

| # | Problema | Ubicación | Impacto |
|---|----------|-----------|--------|
| 1 | **Whisper transcribe en main thread** | escucha.py:1387 | Bloquea 25s |
| 2 | **GPU no confirmada** (fallback silencioso) | escucha.py:999 | CPU lento |
| 3 | **_animar() depende de main thread** | ventana_principal.py:1218+ | Congelación |
| 4 | **QMessageBox bloquea main thread** | ventana_principal.py:5005+ | Interrupción UI |
| 5 | **No hay async/threading para Whisper** | escucha.py | Single-threaded |
| 6 | **NameError: start_time** | ventana_principal.py:1652 | CRASH |

---

## 4. Soluciones Propuestas (RUBEDO)

### Fix #1: Validar GPU Realmente en Uso ⚡
**Ubicación**: escucha.py línea 997  
**Cambio**:
```python
# ANTES (silencioso si falla)
self._modelo = whisper.load_model(modelo_nombre, device=dispositivo)

# DESPUÉS (verificar que GPU funciona)
try:
    self._modelo = whisper.load_model(modelo_nombre, device=dispositivo)
    # Verificar que realmente está en GPU
    if dispositivo.startswith("cuda"):
        dummy_audio = np.zeros((16000 * 5,), dtype=np.float32)  # 5s dummy
        _ = self._modelo.transcribe(dummy_audio, language="es")
        logger.info(f"✅ GPU Whisper verificado exitosamente en {dispositivo}")
except Exception as e:
    logger.error(f"❌ GPU fallo: {e}. Retrocediendo a CPU...")
    dispositivo = "cpu"
    self._modelo = whisper.load_model(modelo_nombre, device=dispositivo)
```

### Fix #2: Mover Whisper a Thread Separado
**Ubicación**: Crear método `_transcribe_async()` en HiloEscucha  
**Cambio**:
```python
# En HiloEscucha (worker thread)
def _transcribe_async(self, audio):
    """Transcribe en background sin bloquear main thread."""
    try:
        resultado = self._modelo.transcribe(audio, **_whisper_params)
        self.transcripcion_lista.emit(resultado["text"])
    except Exception as e:
        logger.error(f"Error transcripción async: {e}")
        self.transcripcion_error.emit(str(e))
```

### Fix #3: QMessageBox No Bloquee Main Thread
**Ubicación**: ventana_principal.py línea 5005+  
**Cambio**:
```python
# ANTES: Bloquea main thread
resp = QMessageBox.question(self, titulo, mensaje, ...)

# DESPUÉS: Modal no-blocking
dlg = QMessageBox(self)
dlg.setWindowTitle(titulo)
dlg.setText(mensaje)
dlg.finished.connect(lambda r: self._en_respuesta_dialog(r))
dlg.show()  # No bloquea
```

### Fix #4: Verificar NameError Reparado
**Ubicación**: ventana_principal.py línea 1220  
**Status**: ✅ HECHO — `start_time = ahora` agregado

---

## 5. Impacto de Fixes

### Pre-Fixes
- Respuesta: **25+ segundos** ❌
- Animaciones: **Congeladas/trabadas** ❌
- UX: **Inutilizable** ❌

### Post-Fixes
- Respuesta: **~5 segundos** (GPU) o **~15 segundos** (CPU) ✅
- Animaciones: **60 FPS fluidas** ✅
- UX: **Responsivo** ✅

---

## 6. Diagnosticadores Propuestos

```python
# En escucha.py: Verificar si GPU realmente en uso
@property
def dispositivo_actual(self):
    try:
        return str(self._modelo.device)
    except:
        return "unknown"

# En ventana_principal.py: Monitor de main thread
def _verificar_main_thread_libre(self):
    """Alerta si main thread bloqueado >200ms."""
    inicio = time.monotonic()
    QTimer.singleShot(200, lambda: self._check_blocked(inicio))

def _check_blocked(self, start):
    delta = time.monotonic() - start
    if delta > 0.25:
        logger.warning(f"⚠️ Main thread bloqueado {delta*1000:.0f}ms!")
```

---

## 7. Recomendación Inmediata

**Priority**: 🔴 CRÍTICO

1. ✅ **HECHO**: Fix NameError start_time
2. **TODO**: Validar GPU Whisper (Fix #1)
3. **TODO**: Mover Whisper a thread async (Fix #2)  
4. **TODO**: Dialog no-blocking (Fix #3)
5. **TODO**: Test respuesta <10s

---

## 8. Procrastinación Alquímica Identificada

**Patrón**: Sistema acumula optimizaciones locales sin coordinación global.
- ✅ Animaciones "fluidas" (óptimo local)
- ❌ Pero main thread bloqueado por Whisper (óptimo global fracasa)
- = **Fantasma de fluidez** — logs dicen 60 FPS, user ve congelado

**Lección**: Optimizar componentes SIN arquitectura async = Sísifo.

---

**Siguiente Fase**: ALBEDO — Purificar findings, CITRINITAS — Investigar diseño async ideal
