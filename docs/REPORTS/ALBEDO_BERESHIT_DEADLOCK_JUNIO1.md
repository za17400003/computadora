# ALBEDO: WI-BERESHIT-DEADLOCK-FIX — Purificación y Análisis (Junio 1, 2026)

**Alquimia de Purificación**: NIGREDO → **ALBEDO** → CITRINITAS → RUBEDO

---

## 🧪 Lavado de Opciones

### Opción 1: Lazy-Init Pattern (RECOMENDADA ✅)

**Descripción**:
```python
# Global lazy-init flag
_WHISPER_CARGADO = False
_WHISPER_MODELO = None

def _ensure_whisper_loaded(config):
    """Carga Whisper solo en primer uso."""
    global _WHISPER_CARGADO, _WHISPER_MODELO
    if _WHISPER_CARGADO:
        return _WHISPER_MODELO
    _WHISPER_CARGADO = True
    # Carga bloqueante aquí (aceptable, no es en boot)
    _WHISPER_MODELO = whisper.load_model(...)
    return _WHISPER_MODELO

# En _transcribir():
if not self._modelo:
    self._modelo = _ensure_whisper_loaded(config)
resultado = self._modelo.transcribe(audio)
```

**Ventajas**:
- ✅ UI aparece inmediatamente (~0.5s)
- ✅ Primer audio: 5-10s (aceptable, sólo primera vez)
- ✅ Audios posteriores: <1s (modelo en memoria)
- ✅ Patrón probado (Silero VAD ya lo usa)
- ✅ Complejidad mínima (+60 líneas simples)
- ✅ No requiere threads extra
- ✅ Backward compatible

**Desventajas**:
- ⚠️ Primer audio: pequeño delay (5-10s)
- ⚠️ Usuario NO sabe que está cargando (pod parecer "congelado")

**Métricas**:
- Boot time: 0.5s (vs ∞ antes)
- Memoria: Mismo (carga una vez)
- CPU: Concentrado en primer audio (aceptable)
- Complejidad: Baja

**Criterio de Éxito**: ✅ CUMPLE (elegida)

---

### Opción 2: Daemon Thread Separado (CONSIDERADA)

**Descripción**:
```python
# Thread daemon carga Whisper en background
def run(self):
    # Iniciar daemon para Whisper
    daemon = threading.Thread(
        target=_ensure_whisper_loaded,
        args=(self._config,),
        daemon=True
    )
    daemon.start()
    
    # Iniciar escucha (Whisper cargará en paralelo)
    self.estado_cambio.emit("escuchando")
    self._bucle_escucha()
```

**Ventajas**:
- ✅ UI aparece inmediatamente
- ✅ Whisper carga en paralelo (sin esperar primer audio)
- ✅ Primer audio: no hay delay adicional (si Whisper terminó)

**Desventajas**:
- ❌ Complejidad de threading (race conditions)
- ❌ Sincronización: ¿Qué pasa si usuario habla antes de que Whisper termine?
- ❌ Debugging difícil (deadlocks de daemon threads)
- ❌ Requiere locks para proteger acceso a _modelo
- ❌ CPU spike inmediato post-boot (Whisper + escucha simultáneos)

**Análisis de Race Conditions**:
```python
# Escenario: Usuario habla antes de que daemon termine
T=0.0s: Daemon inicia carga Whisper
T=0.5s: UI aparece, usuario habla
T=0.7s: HiloEscucha.transcribir() llama self._modelo.transcribe()
T=0.7s: ¿_modelo está None aún? ¿Semiacargado? → BUG

# Solución: Locks + event signaling
# Pero eso complica el código significativamente
```

**Métricas**:
- Boot time: 0.5s (UI) + 15-30s (Whisper background)
- Memoria: Mismo
- CPU: Permanente spike (Whisper + escucha)
- Complejidad: Alta (threading + locks)

**Criterio de Rechazo**: ⚠️ Complejidad vs. ganancia marginal

---

### Opción 3: QTimer Background Load (CONSIDERADA)

**Descripción**:
```python
def run(self):
    logger.info("Escucha lista")
    self.estado_cambio.emit("escuchando")
    
    # Cargar Whisper en background via Qt timer
    QTimer.singleShot(100, self._background_load_whisper)
    
    self._bucle_escucha()

def _background_load_whisper(self):
    """Cargar Whisper cuando Qt event loop esté idle."""
    logger.info("Cargando Whisper en background...")
    self._modelo = whisper.load_model(...)
    logger.info("✅ Whisper cargado (background)")
```

**Ventajas**:
- ✅ UI aparece inmediatamente
- ✅ Usa Qt event loop (coherente con arquitectura)
- ✅ Permite UI updates durante carga

**Desventajas**:
- ❌ **Circular dependency**: Qt timer requiere que event loop esté ejecutando
- ❌ Pero `run()` NO tiene acceso a event loop (es QThread separado)
- ❌ `QTimer.singleShot()` en QThread != evento en main thread
- ❌ Requiere signal/slot para comunicar con main thread

**Análisis de Feasibilidad**:
```python
# QTimer.singleShot(0, func) ejecuta en QThread, NO en main thread
# Por lo tanto:
# - Callback ejecuta en QThread (donde estamos ahora)
# - No resuelve el problema de bloqueo

# Alternativa: Emitir signal para main thread
# Pero eso requiere arquitectura más compleja
```

**Métricas**:
- Boot time: 0.5s (UI) + 15-30s (Whisper en background, pero...?)
- Memoria: Mismo
- CPU: Concentrado durante carga
- Complejidad: Media-Alta

**Criterio de Rechazo**: ❌ No resuelve problema, arquitectura circular

---

### Opción 4: Pre-loading en Bereshit Boot (CONSIDERADA)

**Descripción**:
```python
# En __main__.py, ANTES de iniciar Qt:
def main():
    # ... setup backends ...
    
    # PRE-CARGAR Whisper ANTES de Qt.exec()
    logger.info("Pre-cargando Whisper...")
    from computadora.voz.escucha import _ensure_whisper_loaded
    config = ConfiguracionGlobal()
    _ensure_whisper_loaded(config)
    logger.info("✅ Whisper pre-cargado")
    
    # AHORA iniciar Qt
    iniciar_interfaz(config, cerebro, demo_modo)
```

**Ventajas**:
- ✅ Whisper completamente listo cuando UI inicia
- ✅ Primer audio: 0 delay

**Desventajas**:
- ❌ **Reintroduce el problema original**: Boot tarda 15-30s antes de UI
- ❌ Peor UX (UI desaparece 15-30s)
- ❌ No resuelve nada, solo reorganiza el bloqueo

**Métricas**:
- Boot time: 15-30s (vs 0.5s con lazy)
- Memoria: Mismo
- CPU: Pico inicial
- Complejidad: Baja

**Criterio de Rechazo**: ❌ Reintroduce problema original

---

### Opción 5: Modular Speech Recognition (CONSIDERADA PERO FUTURA)

**Descripción**:
```python
# Usar modelo más pequeño/rápido por defecto
config.json:
{
  "whisper": {
    "modelo": "tiny",  # En lugar de "base"
    # Cargas:
    # - tiny: ~1s
    # - base: ~15s
    # - small: ~30s
  }
}
```

**Ventajas**:
- ✅ Reduce tiempo de carga (1s vs 30s)
- ✅ Reduce memoria

**Desventajas**:
- ⚠️ Reduce precisión de transcripción
- ⚠️ No resuelve problema (aún bloquea)
- ⚠️ User debería elegir (config-driven)

**Nota**: Puede combinarse con lazy-init para boot aún más rápido.

**Criterio**: ✅ BUENA IDEA PARA FUTURO (separate PR)

---

## 📊 Tabla Comparativa

| Aspecto | Opción 1 (Lazy) | Opción 2 (Daemon) | Opción 3 (QTimer) | Opción 4 (Pre-load) |
|---------|---|---|---|---|
| **Boot UI** | 0.5s ✅ | 0.5s ✅ | 0.5s ✅ | 15-30s ❌ |
| **Primer audio** | 5-10s ⚠️ | 0s (si timing ok) ⚠️ | ~15s ❌ | 0s ✅ |
| **Complejidad** | Baja ✅ | Alta ❌ | Media ⚠️ | Baja ✅ |
| **Threading** | 0 extra ✅ | 1 daemon ⚠️ | Qt signal ⚠️ | 0 extra ✅ |
| **Debugging** | Fácil ✅ | Difícil ❌ | Medio ⚠️ | Fácil ✅ |
| **Proven** | Sí (Silero) ✅ | No ❌ | No ❌ | Sí (pero worse) ❌ |

---

## 🧹 Purificación Completada

**Conclusiones**:

### 1. Opción 1 (Lazy-Init) ES LA MEJOR
- Mejor balance: UI inmediato + primer audio aceptable
- Patrón probado (existe en codebase ya)
- Complejidad mínima
- Zero risk de race conditions

### 2. Trade-off Aceptado
```
Gano: UI inmediata (+50x mejor que deadlock)
Pierdo: Primer audio 5-10s espera (ACEPTABLE)
```

### 3. Futuro: Optimizaciones Posibles
- Usar modelo `tiny` en lugar de `base` (1s en lugar de 15s)
- Pre-cargar en background SOLO si config.json lo permite
- Daemon thread con proper synchronization (si se justifica)

---

## 🎯 Recomendación Final

**IMPLEMENTAR: Opción 1 (Lazy-Init Pattern)**

**Justificación**:
- Mejor UX (UI inmediata vs. never)
- Mínima complejidad
- Patrón probado
- Zero risk
- Documentable/replicable

---

**FIN ALBEDO**: Todas las opciones analizadas, purificadas, clasificadas. Opción 1 seleccionada. ✅
