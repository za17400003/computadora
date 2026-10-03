# NIGREDO: UI Desaparece + Logs Congelados Post-Bereshit (Junio 1, 2026)

**Fecha**: 2026-06-01, 09:16:00 UTC  
**Severidad**: 🔴 CRÍTICO (UI no responde, proceso bloqueado)  
**Status**: DIAGNOSTICADO

---

## SÍNTOMAS REPORTADOS

1. **UI desapareció**: Interfaz gráfica no mostrada tras Bereshit
2. **Logs congelados**: Output de logging se detiene abruptamente
3. **Proceso vivo**: Python sigue corriendo pero sin respuesta (11440 threads bloqueados)

---

## PUNTO EXACTO DE FALLO

**Log final**:
```
09:15:55 | INFO | computadora_app - [Sistema] Inscribiendo la Palabra en cuda:0... modelo 'small'
```

**Qué ocurre después**: SILENCIO TOTAL — No hay logs posteriores, UI no aparece

---

## CAUSA RAÍZ IDENTIFICADA

### 🔴 DEADLOCK: Whisper se carga **bloqueante** en hilo principal (Qt)

**Stack de bloqueo**:
```
1. main() [__main__.py L255]
   ↓
2. iniciar_interfaz() [ventana_principal.py L6173]
   ↓
3. QApplication.exec() [main loop Qt — BLOQUEADO]
   ↓
4. OrbeComputadora.__init__() [ventana_principal.py L609]
   ├─ Mucho init bloqueante
   └─ HiloEscucha() creado/iniciado
      ↓
5. HiloEscucha.run() [QThread]
   ├─ _ensure_whisper_loaded() ← **BLOQUEA AQUÍ**
   │  └─ whisper.load_model('small', device='cuda:0')
   │     ├─ Descarga modelo (si no existe)
   │     ├─ Carga en GPU (~10-30s)
   │     └─ BLOQUEA CUDA, NLU, Qt Event Loop
   └─ NO retorna al Qt event loop
```

**Problema específico**:
- Whisper `load_model()` es **bloqueante** (~10-30s en GPU)
- HiloEscucha es un `QThread` pero llama `load_model()` en `run()`
- Qt main thread espera a que todos los threads inicien
- DEADLOCK: Qt event loop bloqueado, HiloEscucha bloqueado esperando Whisper

### Síntomas visibles
- Qt nunca entra a `exec()` completamente
- Ventana nunca se renderiza (Qt no puede procesar eventos)
- Logs se detienen (logging usa Qt internamente en algunos handlers)
- Proceso zombie: 11440 threads + 0 CPU (esperando lock GPU)

---

## IMPACTO

- **Funcionalidad**: 0% — Computadora no inicia
- **Datos**: No dañados (no fue hasta El saved state)
- **Recuperación**: Kill proceso + fix código
- **Recurrencia**: 100% en cada boot (reproducible)

---

## DIAGNOSIS CONFIRMA

✅ Logs terminan exactamente en carga de Whisper  
✅ Proceso está vivo pero congelado (11440 threads)  
✅ Patrón de deadlock clásico (Whisper + Qt + threads)  
✅ Coincide con activación de `HiloEscucha.run()` ~ 09:16:00  

---

## SOLUCIONES PROPUESTAS

### Opción 1: Lazy Loading (MEJOR)
- NO cargar Whisper en `__init__()` de HiloEscucha
- Cargar en primer uso (cuando realmente se necesite transcribir)
- Ventaja: UI aparece inmediatamente, Whisper se carga en background

### Opción 2: QThread Daemon Independiente
- Crear daemon thread SEPARADO para carga de Whisper
- No bloquea HiloEscucha.run()
- Ventaja: HiloEscucha inicia rápido, Whisper carga en paralelo

### Opción 3: Background Task con Signal
- Usar `QTimer.singleShot(100, _cargar_whisper_background)`
- Después de Qt.show()
- Ventaja: Qt event loop puede ejecutar durante carga

---

## RECOMENDACIÓN

**Opción 1 (Lazy Loading)** es mejor porque:
1. UI aparece inmediatamente ✅
2. Sin threads daemon extra ✅
3. Whisper se carga cuando se necesite (~5-10s cuando usuario hable) ✅
4. Patrón probado en Silero VAD (ya usa lazy-init) ✅

---

**FIN NIGREDO**

El sistema fue evaluado destructivamente. Root cause identificada. Solución clara.
