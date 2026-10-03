# 🔍 HALLAZGO CRÍTICO: Instrumentación FPS Validada, Pero _animar() No Ejecuta en App Real

**Fecha**: Mayo 12, 2026  
**Estado**: ⚠️ BLOQUEADO — Necesita decisión del usuario

---

## 📊 RESUMEN DE LA INVESTIGACIÓN

### ✅ LO QUE FUNCIONA
1. **Instrumentación FPS correcta**: Tests validan que la lógica mide frame times con precisión
   - 60 FPS → mide 60.0 FPS ✓
   - 30 FPS → mide 30.0 FPS ✓
   - 10 FPS → mide 10.0 FPS ✓
   - Mezclas → calcula promedios correctamente ✓

2. **Código compilable**: ventana_principal.py compila sin errores

3. **Timer configurado**: Log muestra "🎬 Animación iniciada: 60 FPS (intervalo=16ms)" al boot

### ❌ LO QUE NO FUNCIONA
1. **_animar() NO se ejecuta**: 45+ segundos de ejecución SIN un SOLO log de frame rate
2. **No aparece "DEBUG: _animar() STARTED EXECUTING"** a pesar de 45+ segundos
3. **Event loop aparentemente bloqueado o inactivo**

---

## 🔬 DIAGNÓSTICO

### Evidencia de Logs
```
20:59:37 | INFO | 🎬 Animación iniciada: 60 FPS (intervalo=16ms)  ← Timer iniciado
21:00:14 | INFO | TTS cola vacía ù reanudando escucha                 ← Último evento
         | ...  | (SILENCIO COMPLETO 45+ segundos)               ← NO hay "Frame rate" logs
```

### Hipótesis Principales

1. **Ventana no visible → Event loop no procesa timer**
   - `iniciar_interfaz()` llama `orbe.show()` 
   - Pero `sys.exit(app.exec())` bloquea hasta close
   - ¿Está la ventana visible al user o hidden/minimized?

2. **Timer conectado pero receiver incorrecto**
   - Timer está conectado a `self._animar`
   - Pero timeout puede no estar disparándose si:
     - No hay event loop activo
     - Excepción silenciosa en `_animar()`
     - Timer nunca fue realmente iniciado

3. **Logging capturado en background**
   - Ejecución en background job con redirección de stdout
   - Logs buffer puede no flushear
   - `logger.info()` vs `logger.debug()` filtering

---

## 🎯 OPCIONES A PARTIR DE AQUÍ

### Opción A: Forzar Ventana Visible (Más Intruso)
```python
# En iniciar_interfaz():
orbe.show()
orbe.raise_()
orbe.activateWindow()  # Traer al foreground explícitamente
```
**Ventaja**: Visibilidad garantizada, timer probablemente se ejecute  
**Desventaja**: Usuario ve ventana flotante constantemente (no deseado)

### Opción B: Debug Logger Directo (No Depender de Logs)
```python
# En ventana_principal.py _animar():
with open('/tmp/fps_debug.txt', 'a') as f:
    f.write(f"Frame {self._debug_frame_count}\n")
    if self._frame_count_since_log >= 60:
        f.write(f"FPS: {actual_fps:.1f}\n")
```
**Ventaja**: Escribe directamente a archivo, no depende de logger  
**Desventaja**: Overhead de I/O en cada frame (muy lento)

### Opción C: Aceptar "False Positive" Honestamente (Recomendado)
**Declare que "60 FPS" en el log es una ESTIMACIÓN STARTUP**, no una medición real:
```python
# En _iniciar_animacion():
logger.info(f"🎬 Animación iniciada: {fps_target} FPS target (intervalo={intervalo_ms}ms) — medición continua habilitada")
```

Y cuando `_animar()` SE EJECUTE, mostrará:
```
🎬 Frame rate: 45.3 FPS (avg delta_t: 22.1ms)  ← REAL, no target
⚠️  Frame rate: 52.1 FPS (slowdowns: 18%)      ← Si hay problemas
```

**Ventaja**: Honesto, no requiere cambios arquitectónicos  
**Desventaja**: Aún no sabemos por qué no se ejecuta

### Opción D: Examinar Perceptor en Vivo (Investigación Profunda)
- Attachear debugger Qt  
- Verificar si timer está realmente disparando
- Revisar exception handling en `_animar()`
- Checar si event loop está procesando eventos

---

## 💡 RECOMENDACIÓN

**Ir por Opción A (mostrar ventana visible)** como próximo paso diagnóstico:

1. Permite verificar si timer se ejecuta cuando hay UI visible
2. Si FPS logs aparecen, es problema de event loop inactivo con ventana hidden
3. Si NO aparecen logs, es problema más profundo (threading, exception, etc.)

---

## ARCHIVOS MODIFICADOS EN ESTA SESIÓN

- [ventana_principal.py](computadora/interfaz/ventana_principal.py#L1210-L1240)
  - Lines 710-717: Frame time buffer initialization
  - Lines 1210-1240: FPS instrumentation in _animar()
  - Line 1215: DEBUG: logger.info("DEBUG: _animar() STARTED")

- [test_fps_instrumentation_direct.py](tests/test_fps_instrumentation_direct.py) ← NUEVO
  - Test suite validando instrumento (todos ✅ PASAN)

---

## PRÓXIMOS PASOS (REQUIERE CONFIRMACIÓN DEL USUARIO)

```
[ ] A. Hacer ventana visible al startup (test visibilidad/timer)
[ ] B. Usar file-based logging en _animar() (evitar logger buffering)
[ ] C. Aceptar false-positive honestamente, esperar a que ejecute
[ ] D. Investigación profunda con debugger Qt
[ ] E. Otro (especificar)
```

**Bloqueo actual**: Sin visibilidad sobre por qué _animar() no se ejecuta, no puedo medir reales FPS.
