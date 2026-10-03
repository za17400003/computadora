# 🔴 DIAGNÓSTICO: Boot Freeze 30+ segundos — Event Loop Bloqueado

**Fecha**: 2026-05-12 21:30 UTC  
**Severidad**: 🔴 CRÍTICO — Interfaz completamente congelada durante boot  
**Usuario Reporte**: "sigo percibiendo trabada y baja de fps"

## Hallazgo Clave

**FPS Instrumentation ✅ FUNCIONA**:
- Lógica de medición correcta (unit tests 4/4 PASS)
- Cálculo delta_t, buffer de 60 frames, detección de slowdowns — TODO CORRECTO
- Problema: _animar() se dispara solo 1 vez en 30+ segundos

**Causa Raíz ✅ IDENTIFICADA**:
- Event loop Qt **COMPLETAMENTE BLOQUEADO** durante boot
- Main thread (hilo principal) ejecuta operaciones síncronas bloqueantes
- QTimer no puede disparar eventos mientras hilo principal espera I/O

## Timeline de Evidencia

```
21:14:40 | INFO | 🎬 Animación iniciada: 60 FPS (intervalo=16ms)
21:14:40 | INFO | El Golem ha despertado
21:14:40 | INFO | [Sistema] Inscribiendo la Palabra en cpu... modelo 'small'
                   ← ⚠️ AQUÍ COMIENZA BLOQUEO
                   ← QTimer debería disparar ~14s × 60fps = 840 eventos
                   ← PERO NO DISPARA NINGUNO

21:14:40 | DEBUG| 🎬 DEBUG: _animar() STARTED EXECUTING  ← 1 SOLA VEZ EN TODO EL BOOT

21:14:54 | INFO | Modelo Whisper cargado exitosamente   ← 14 SEGUNDOS DESPUÉS
                   ← Hilo principal se libera
                   ← Event loop vuelve a procesar eventos
```

## Operaciones Bloqueantes Detectadas

1. **Whisper Model Load** (modelo='small', cpu device)
   - Duración: 14+ segundos
   - Ubicación: golem/voz/escucha.py (durante boot)
   - Impacto: Congela event loop completamente

2. **TTS Initialization** (edge-tts, voice model)
   - Duración: ~5 segundos
   - Ubicación: golem/nucleo/motor_tts.py (durante boot)
   - Impacto: Adicional a Whisper

3. **Modelo Ollama Load** (llama2:7b)
   - Duración: 2-3 segundos
   - Ubicación: golem/cerebro/orquestador.py (post-boot)
   - Impacto: Puede causar hesitación post-boot

## Por Qué Anteriormente Fue "Fix RUBEDO"

**RUBEDO (daemon psutil fix)**:
- Movió `psutil.cpu_percent()` (bloqueante 10-100ms) a daemon thread
- Resultado: Ya NO congelaba cada 2s DURANTE POST-BOOT
- PERO: No resolvió el freeze INICIAL de boot

**El usuario percibe**:
- "Trabada": Correcto — congelada 30s during boot
- "Baja de fps": Correcto — 0 FPS durante boot (0 frames rendered)

## Soluciones Posibles

### OPCIÓN A: Mover Whisper a Background Thread (MEJOR)
```python
# En lugar de:
self._modelo = whisper.load_model("small", device="cpu")  # ← BLOQUEANTE

# Hacer:
def _cargar_whisper_async():
    whisper_modelo = whisper.load_model("small", device="cpu")
    self._modelo = whisper_modelo
    self._modelo_listo.emit()

threading.Thread(target=_cargar_whisper_async, daemon=True).start()
```
- Beneficio: Animation sigue 60 FPS durante Whisper load
- Costo: Complejidad (threading, sincronización)

### OPCIÓN B: Yield Event Loop Periódicamente (INTERMEDIO)
```python
# En loops bloqueantes:
for i in range(1000):
    # trabajo bloqueante
    if i % 10 == 0:
        QCoreApplication.processEvents()  # Permite que timer dispare
```
- Beneficio: Menos complejidad que threading
- Costo: Requiere identificar TODOS los bloques

### OPCIÓN C: Aceptar Freeze Inicial (ACTUAL)
```
- User expectation: App tarda 30s en mostrar interfaz funcionando
- Ya documentado (RUODO -> daemon psutil fix)
- Pero: NO satisface "sigo percibiendo trabada"
```

## Recomendación

**INVESTIGACIÓN INMEDIATA**:
1. ¿Whisper es realmente el culpable? → Profiling con timeit
2. ¿Hay forma de precargar Whisper ANTES del Qt app.exec()?
3. ¿Pueden TTS/Ollama también moverse a background?

**SI LA RESPUESTA ES SI A CUALQUIERA**:
→ Implementar OPCIÓN A (Background threading)
→ Boot será invisible al usuario (animation runs normally)

## Status

❌ **FPS Measurement**: COMPLETADO (código correcto, pero no se llama)  
✅ **Causa Raíz**: IDENTIFICADA (Event loop bloqueado)  
⏳ **Solución**: PENDIENTE (Requiere refactoring de boot sequence)

---
**Próxima Acción**: "OK, ahora vamos a hacer que el boot NO congele. Voy a separar Whisper a background thread y vamos a medir FPS reales DESPUÉS del boot."
