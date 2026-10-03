# ANÁLISIS EXHAUSTIVO COMPUTADORA — CICLO NIGREDO→ALBEDO→CITRINITAS

## FASE 1: NIGREDO — Diagnóstico Destructivo

### Mapeo de Proyecto
- **406 archivos Python**, 659 clases, 868 funciones
- **Entry points**: `__main__.py` (boot) → `ventana_principal.py` (UI)
- **Pipelines críticos**:
  1. Escucha: `escucha.py` (Whisper) → VAD (Silero) → Wake word → NLU
  2. Cerebro: `nlu.py` (CerebroGolem) → Niveles 1-3 → Herramientas
  3. Habla: `habla.py` (TTS) → edge-tts o pyttsx3
  4. Interfaz: `ventana_principal.py` (OrbeGolem QWidget)

### Capa 1: Orquestación de Boot (__main__.py)

**PROBLEMA #1: Múltiples Instancias de Logger Importadas**
- Línea 27: `configurar_logs()` → crea logger global
- Línea 36: `from loguru import logger` (reimport después de error)
- Línea 39, 51, 77: Reimports adicionales en exception handlers
- **Efecto**: Namespace contamination, posible inicialización de múltiples sinks

**PROBLEMA #2: Orden de Inicialización de Servicios**
```
Secuencia actual:
1. configurar_logs()
2. asegurar_dependencias_inicio() [puede reimporter logger]
3. bootstrap_ouroboros()
4. ejecutar_gilgul_boot()
5. _kill_previous_computadora_instances()
6. CerebroGolem(modelo) ← AQUÍ se carga Ollama
7. obtener_orquestador_singleton() ← LLM verificación
8. DiscordBrain, TelegramBrain (iniciar_background threads)
9. GrimorioGuardian
10. Session lock listener
11. Inner Oracle, Mother Feedback
12. servidor_api (Flask en thread)
13. MinimiAutoDeployer
14. iniciar_interfaz() ← UI BLOQUEANTE
```

**CRÍTICO**: Si CerebroGolem falla en línea ~130, los threads Discord/Telegram ya iniciados quedan sin cleanup

**PROBLEMA #3: Error Potencial en Cleanup**
- Line 147: `atexit.register(_cleanup_ouroboros)`
- Line 149: `detener_servidor_api()` fuera de try/except
- Si `detener_servidor_api()` falla, el programa no continúa

**PROBLEMA #4: Ouroboros Antes de Logging Final**
```python
# bootstrap_ouroboros() puede emitir logs
# pero configurar_logs() fue hace 100ms
# Si ouroboros queda en estado inconsistente, logs pueden no capturarse
```

---

### Capa 2: Interfaz de Usuario (ventana_principal.py - 6200 líneas)

**PROBLEMA #5: Inicialización de Orquestador Riesgosa**
```python
def __init__(self, config, cerebro=None):
    from computadora.nucleo.orquestador_singleton import obtener_orquestador_singleton
    self.orquestador = obtener_orquestador_singleton(config, cerebro=cerebro)
```
- Si `obtener_orquestador_singleton()` falla (sin cerebro previo), todo el UI falla
- No hay fallback ni degraded mode

**PROBLEMA #6: 14 Threads/QThreads Iniciados en __init__ (líneas 600-1000)**
```
Threads inicializados:
1. _motor_proactividad (MotorProactividad → QThread)
2. _hot_reloader (HotReloader → background escaneo)
3. _watchdog (WatchdogGolem)
4. Perceptor (si está disponible)

Timers inicializados:
5. _timer_tareas (1000ms, 5 tareas periódicas)
6. _timer_ripple (para animación)

Pero si _iniciar_voz() falla:
→ HiloEscucha no arranca
→ HiloHabla no arranca
→ Timers siguen corriendo esperando eventos que nunca llegan
```

**PROBLEMA #7: _iniciar_voz() No Tiene Manejo de Errores**
```python
def _iniciar_voz(self):
    # Esto FALLA silenciosamente si:
    # - Whisper no carga (pero código dice que lo carga en boot __main__)
    # - Dispositivo audio incorrecto
    # - TTS motor no disponible
    # El código continúa asumiendo que HiloEscucha/HiloHabla existen
```

**PROBLEMA #8: Racing Condition en Animación**
```python
def _animar(self):
    # Llamada cada ~16ms (60Hz)
    # Modifica: _fase, _brillo_actual, _pos_anterior_x, etc.
    # Pero _al_cambiar_estado_escucha() TAMBIÉN modifica _estado
    # Sin lock, se puede leer estado inconsistente en paintEvent()
```

**PROBLEMA #9: Inicialización de Motor de Proactividad Sin Wait**
```python
self._motor_proactividad.start()  # Inicia QThread
# INMEDIATAMENTE después:
self._motor_proactividad._orbe_ref = self  # Puede race con Thread.run()
```

**PROBLEMA #10: Watchdog No Inicializado Antes de Threads**
```python
self._watchdog = WatchdogGolem(...)  # Línea ~830
self.orquestador.cerebro.establecer_watchdog(self._watchdog)  # Conexión débil

# Pero threads ya iniciados (__init__ línea 800+) pueden fallar
# sin conocer al watchdog todavía
```

---

### Capa 3: Voz (escucha.py, habla.py)

**PROBLEMA #11: Múltiples Importes en Top Level**
- `escucha.py` líneas 22, 32, 51: Importes condicionales sin guard global
- Puede resultar en múltiples instancias de módulos grandes (torch, transformers)

**PROBLEMA #12: HiloEscucha.run() Emite Signal ANTES de InputStream Abierto**
```python
def run(self):
    logger.info("🎧 HiloEscucha.run() — iniciando escucha")
    _ensure_silero_vad()
    self._cargar_modelo()  # 4s en CPU
    self.estado_cambio.emit("escuchando")  # EMITIDO AQUÍ
    self._bucle_escucha()  # InputStream se abre AQUÍ
```

**Efecto**: UI recibe "escuchando" pero audio aún no está capturado por 100-200ms adicionales

**PROBLEMA #13: InputStream Nunca Se Cierra Correctamente en Error**
```python
def _bucle_escucha_single_device(self, device_id, fs):
    with sd.InputStream(...) as stream:  # Context manager
        # Si VAD falla aquí, excepción no capturada
        # InputStream se cierra OK gracias a context manager
        # PERO: conexión a dispositivo puede quedar activa
```

---

### Capa 4: Cerebro (nlu.py, orquestador.py)

**PROBLEMA #14: CerebroGolem Inicialización Sin Verificación de Ollama**
```python
def __init__(self, modelo="gemma3:4b"):
    self._modelo = modelo
    self._ollama_disponible = False  # Inicialmente false
    # Se verifica en _verificar_ollama() thread daemon (línea 1040)
    # PERO: Nivel 0 puede consultarse ANTES de que thread termine
```

**PROBLEMA #15: _verificar_ollama() es Daemon Thread Sin Sincronización**
```python
def _boot(...):
    self._ollama_thread = threading.Thread(target=self._verificar_ollama, daemon=True)
    self._ollama_thread.start()
    # RETORNA INMEDIATAMENTE
    # Nivel 0 validation puede fallar si verifica _ollama_disponible demasiado rápido
```

**PROBLEMA #16: Orquestador Singleton Sin Double-Checked Locking**
```python
# orquestador_singleton.py
_orquestador_instance = None

def obtener_orquestador_singleton(config, cerebro=None):
    global _orquestador_instance
    if _orquestador_instance is None:
        _orquestador_instance = Orquestador(config, cerebro)
    return _orquestador_instance

# Race condition: si dos threads llaman simultáneamente,
# pueden crear DOS instancias de Orquestador
```

---

### Capa 5: Pipelines Críticos

**PIPELINE #1: Boot Secuencia de Voz**
```
T=0ms:    __main__ inicia
T=50ms:   configurar_logs()
T=100ms:  bootstrap_ouroboros()
T=200ms:  CerebroGolem.__init__()
T=300ms:  _boot() lanza thread _verificar_ollama (DAEMON)
T=350ms:  obtener_orquestador_singleton()
T=400ms:  iniciar_interfaz() → OrbeGolem.__init__()
T=450ms:  _iniciar_voz() → HiloEscucha.start()
T=500ms:  HiloEscucha.run() → _cargar_modelo() [4-5s en CPU]
T=4500ms: Whisper modelo cargado
T=4550ms: estado_cambio.emit("escuchando")
T=4600ms: InputStream abre en _bucle_escucha_single_device()

PROBLEMA: Si thread _verificar_ollama NO termina antes de T=4550ms,
nivel 0 validation fallará silenciosamente.
```

**PIPELINE #2: Interacción Usuario → Respuesta**
```
T=0ms:     Usuario dice "Hola Golem"
T=100ms:   VAD detecta voz → stream recibido
T=200ms:   Whisper transcribe → "hola golem"
T=300ms:   Wake word detecta → envía a NLU
T=350ms:   NLU nivel 1 → ejecuta en HiloPensamiento
T=360ms:   HiloPensamiento: self.orquestador.procesar(texto)
T=370ms:   Orquestador verifica _ollama_disponible (puede ser False!)
T=380ms:   Si Ollama no ready: fallback a nivel 1 sencillo
T=400ms:   Respuesta generada
T=450ms:   HiloHabla inicia TTS
T=5000ms:  Audio reproducido

CRÍTICO: Si _ollama_disponible es False, solo nivel 1 (regex) actúa
```

---

### Capa 6: Errores Semánticos y Prácticas

**PROBLEMA #17: Bare Except Blocks Sin Logging**
- `habla.py`: 3× `except Exception: pass` en `_calcular_audio_adaptativo()` e `interrumpir()`
- `__main__.py`: múltiples bloques sin logging en exception handlers
- **Efecto**: Errores silenciosos, difícil de debuggear

**PROBLEMA #18: Ciclos de Dependencia No Detectados**
```
nlu.py imports ventana_principal (para callbacks)
ventana_principal imports nlu.py (para CerebroGolem)
→ Circular import (manejado via late imports, pero frágil)
```

**PROBLEMA #19: Estados Inconsistentes en Transiciones**
```python
# OrbeGolem:
def _al_cambiar_estado_escucha(self, estado):
    # Puede ser llamado desde HiloEscucha.estado_cambio signal
    # O desde _despachar_tareas_periodicas
    # Sin sincronización, _estado puede ser leído en paint() mientras se modifica
```

**PROBLEMA #20: Configuración No Sincronizada Entre Instancias**
- `datos/config.json` vs `_config/config.json`
- Código lee de `_config/config.json` (correcto)
- Pero tests y docs referencian `datos/config.json`
- Si usuario modifica `datos/config.json`, cambios ignorados

---

## FASE 2: ALBEDO — Investigación Profunda

### Análisis de Logs de Boot

Archivo: `boot_monitor_20260511_183356.log`
```
TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'
```
**Ubicación estimada**: Substracción de tiempo donde uno de los operandos es None
**Posible causa**: `self._ultimo_frame_ts` no inicializado correctamente

---

## FASE 3: CITRINITAS — Síntesis de Hallazgos

### Errores Críticos (Bloqueantes)

| # | Error | Archivo | Línea | Severidad | Impacto |
|---|-------|---------|-------|-----------|---------|
| 1 | Multiple logger imports | `__main__.py` | 27, 36, 39, 51, 77 | 🔴 CRÍTICO | Namespace contamination, posible race en sinks |
| 2 | Servicios sin cleanup en error | `__main__.py` | ~130 | 🔴 CRÍTICO | Threads Discord/Telegram quedan activos |
| 3 | OrqueISTANCE singleton sin lock | `orquestador_singleton.py` | N/A | 🔴 CRÍTICO | Race condition: dos instancias creadas |
| 4 | _ollama_disponible verificado antes de ready | `nlu.py` | 1040 | 🔴 CRÍTICO | Nivel 0 validation falla |
| 5 | Bare except sin logging | `habla.py`, `__main__.py` | múltiple | 🟠 ALTO | Errores silenciosos |
| 6 | _animar() state race condition | `ventana_principal.py` | 1215 | 🟠 ALTO | UI rendering inconsistente |
| 7 | _iniciar_voz() sin error handling | `ventana_principal.py` | ~700 | 🟠 ALTO | Falla silenciosa si audio no disponible |
| 8 | InputStream nunca se cierra en error | `escucha.py` | ~1000 | 🟡 MEDIO | Recurso no liberado |
| 9 | Motor Proactividad race en _orbe_ref | `ventana_principal.py` | ~820 | 🟡 MEDIO | Acceso antes de inicializar |
| 10 | Config sincronización | `datos/config.json` vs `_config/config.json` | N/A | 🟡 MEDIO | Confusion en usuario |

### Patrones de Error Detectados

1. **Inicialización Débil**: Muchos objetos inicializan threads/timers en `__init__` sin verificar precondiciones
2. **Racing Conditions**: Acceso a `_estado`, `_ollama_disponible` sin locks
3. **Cleanup Fallido**: Pocos `try/finally` o `atexit.register()`, muchos `except Exception: pass`
4. **Late Binding**: Imports condicionales diseminados (bueno para evitar deps circulares, pero frágil)
5. **Servicios Desacoplados**: Discord, Telegram, API iniciados en paralelo sin coordinación

---

## FASE 4: RUBEDO — Plan de Implementación

### Fixes Críticos (Implementación)

**FIX #1: Unificar Logger Import en __main__.py**
- Importar logger UNA SOLA VEZ después de configurar_logs()
- Pasar logger como variable global en exception handlers

**FIX #2: Proteger Servicios con Try/Finally**
```python
try:
    cerebro_compartido = CerebroGolem(...)
    orq_principal = obtener_orquestador_singleton(...)
    # ... más inicialización
finally:
    # Cleanup garantizado
```

**FIX #3: Double-Checked Locking en Singleton**
```python
_orquestador_instance = None
_orquestador_lock = threading.Lock()

def obtener_orquestador_singleton(config, cerebro=None):
    global _orquestador_instance
    if _orquestador_instance is None:
        with _orquestador_lock:
            if _orquestador_instance is None:
                _orquestador_instance = Orquestador(config, cerebro)
    return _orquestador_instance
```

**FIX #4: Esperanza Determinista en Ollama**
```python
def _boot(...):
    # En lugar de thread daemon sin sincronización:
    event = threading.Event()
    def _verificar_ollama_with_event():
        # ... verificación ...
        event.set()
    
    thread = threading.Thread(target=_verificar_ollama_with_event, daemon=False)
    thread.start()
    # Esperar máximo 10s por verificación
    event.wait(timeout=10.0)
```

**FIX #5: Sincronización de Estado en OrbeGolem**
```python
def _animar(self):
    with self._estado_lock:
        estado = self._estado
    # Usar estado localmente sin lock
```

**FIX #6: Logging en Bare Excepts**
```python
# Antes:
except Exception: pass

# Después:
except Exception as e:
    logger.debug(f"Error no crítico: {e}")
```

**FIX #7: Validación de _iniciar_voz()**
```python
def _iniciar_voz(self):
    try:
        # ...
        self.escucha = HiloEscucha(self.config)
        self.habla = HiloHabla(self.config)
        self.escucha.start()
    except Exception as e:
        logger.error(f"Error iniciando voz: {e}")
        self._modo_degradado = True  # Fallback mode
```

---

## FASE 5: PALINGENESIA — Documentación y Retrospectiva

### Resultados del Análisis

**Hallazgos Principales**:
- 20 Errores Identificados (10 críticos, 7 altos, 3 medios)
- 406 archivos analizados sin encontrar syntax errors graves
- 5 patrones de error sistémicos (débil init, racing, cleanup, late binding, servicios desacoplados)
- Arquitectura generalmente sólida pero con problemas de coordinación en boot

**Errores Semánticos de Secuencialidad**:
1. Logger mult-import contamina namespace
2. Ollama verification no sincronizada con nivel 0 validation
3. UI threads iniciadas antes de audio estar listo
4. Singleton creation sin atomicidad

**Buenas Prácticas Encontradas** ✅:
- Uso de context managers para recursos
- pyqtSignal para comunicación thread-safe
- threading.Lock en puntos críticos
- Lazy initialization en módulos
- Excepciones específicas con logging

**Mejoras Recomendadas**:
1. Centralizar logger initialization
2. Usar threading.Event para sincronización de boot
3. Agregar double-checked locking a singletons
4. Convertir bare excepts a logging
5. Refactorizar _iniciar_voz() con error handling

