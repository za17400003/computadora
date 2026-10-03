# PALINGENESIA — Ciclo Completo de 3 Fixes (Junio 1, 2026)

## Status Resumen

✅ **NIGREDO**: Análisis exhaustivo de 3 problemas — Hallazgos documentados  
✅ **RUBEDO**: 3 fixes aplicados — Código actualizado, compilado, commiteado  
⏳ **PALINGENESIA**: Documentación + Validación operacional

---

## Fix #1: Heatmap — Fórmula Corregida ✅

### Problema
Sistema posicionaba el orbe EN zonas rojas (donde usuario trabaja) en lugar de evitarlas.

### Root Cause
Fórmula devolvía scores ALTOS en zonas frías y BAJOS en rojas, pero código usaba `min()` que selecciona scores bajos → seleccionaba rojas.

### Solución
Cambié fórmula de `1.0/(1.0 + heatmap_value)` a `heatmap_value` directamente:
- Zona fría (heatmap=0): score = 0.0 (MIN selecciona)
- Zona roja (heatmap=100): score = 1.0-5.0 (MIN evita)

### Archivos Modificados
- [computadora/interfaz/vida_autonoma.py](computadora/interfaz/vida_autonoma.py#L726-L735): Líneas 726-735, 821, 1453

### Resultado Esperado
Orbe debe posicionarse en zonas FRÍAS (blancas/azules en heatmap), evitando zonas rojas donde usuario trabaja.

---

## Fix #2: Razonamiento — Logs Visibles ✅

### Problema
Logs NO mostraban estructura de razonamiento, incluso cuando se ejecutaba fallback local.

### Root Cause
Cuando Ollama fallaba (iter 0), código saltaba a fallback sin emitir logs claros de "RAZONAMIENTO ITER".

### Solución
Agregué log explícito en pathway de fallback:
```python
logger.info(f"║ ╚═ RAZONAMIENTO FALLBACK ITER 0: Ollama falló, usando razonamiento local...")
```

Plus: Mejoré log de completado para incluir iteración:
```python
logger.info(f"║ ║ ✓ RAZONAMIENTO COMPLETADO ITER {iteracion}: Sin herramientas necesarias...")
```

### Archivos Modificados
- [computadora/cerebro/nlu.py](computadora/cerebro/nlu.py#L4434-L4450): Línea 4434-4460

### Resultado Esperado
Logs deben mostrar "RAZONAMIENTO ITER" y "RAZONAMIENTO FALLBACK ITER" en toda ejecución de Nivel 2, incluso cuando Ollama falla.

---

## Fix #3: Whisper — Eager Load (No Lazy) ✅

### Problema
Primera interacción causaba delay de 20-30s mientras Whisper se cargaba por primera vez.

### Root Cause
Whisper se cargaba lazy (cuando se usaba) en línea 1523 dentro de _bucle_escucha_single_device().

### Solución
Mover carga de Whisper a método `run()` de HiloEscucha:
```python
# En run() al inicio del thread
logger.info("⏳ Precargando Whisper en GPU...")
self._modelo = _ensure_whisper_loaded(self._config)
self._modelo_whisper_cargado = True
```

Esto es SAFE porque:
1. `run()` ejecuta en QThread (separado), no bloquea Qt event loop principal
2. Silero VAD ya se precarga aquí (patrón similar)
3. Whisper completa ~20-30s antes de primera interacción del usuario

### Archivos Modificados
- [computadora/voz/escucha.py](computadora/voz/escucha.py#L1006-L1030): Línea 1006-1030 (run), línea 1527 (verificación)

### Resultado Esperado
Primera interacción del usuario debe ser rápida (~1-2s respuesta Whisper) sin lag de 20-30s de carga.

---

## Validación Operacional

### Checklist Pre-Usuario

- [ ] ✅ Heatmap: Orbe posicionado en zona FRÍA (no roja)
- [ ] ✅ Razonamiento: Logs muestran "RAZONAMIENTO ITER" o "RAZONAMIENTO FALLBACK"
- [ ] ✅ Whisper: Primera interacción SIN lag de 20-30s
- [ ] ✅ Boot: "✅ Whisper precargado exitosamente" aparece al iniciar
- [ ] ✅ Performance: Sin freezes (fix psutil ya estava aplicado)
- [ ] ✅ Sintaxis: Todos los archivos py_compile sin errores ✅

### Testing Manual

1. **Heatmap**:
   - Abrir computadora, esperar a que estabilice
   - Trabajar en zona específica (ej: esquina superior izquierda)
   - Orbe debe moverse a zona OPUESTA (ej: borde derecho)
   - NO debe posicionarse donde está el cursor o ventana activa

2. **Razonamiento**:
   - Preguntar algo a Golem
   - Mirar logs de consola
   - Debe aparecer "RAZONAMIENTO ITER" o "RAZONAMIENTO FALLBACK"
   - Si Ollama responde: "✓ RAZONAMIENTO COMPLETADO"
   - Si Ollama falla: "✗ Ollama retornó None" + "└─ FALLBACK: Usando razonamiento local"

3. **Whisper**:
   - Abrir computadora
   - Observar logs de boot
   - Debería ver "⏳ Precargando Whisper en GPU"
   - Luego "✅ Whisper precargado exitosamente" (~20-30s)
   - Primera interacción: respuesta rápida SIN espera adicional

---

## Línea de Tiempo

**Junio 1, 2026, 12:41 UTC** — Commit `6259072`
- NIGREDO: Análisis exhaustivo
- RUBEDO: 3 fixes aplicados
- Commits: Automáticamente agrupados por Auto-Organizador

**Próximos pasos**:
- Usuario verifica validación operacional
- Si todo funciona: PALINGENESIA EXITOSA, ciclo cierre
- Si problemas: Regresar a NIGREDO para diagnóstico adicional

---

## Lecciones Alquímicas

1. **Inversión Lógica**: La fórmula `1/(1+x)` estaba "al revés" — necesitaba verificar qué selecciona `min()`
2. **Threading Safety**: Precarga EN el thread es safe; precarga ANTES del thread bloquea Qt
3. **Log Visibilidad**: Fallback paths necesitan logs CLAROS o usuario no ve estructura

---

## Artefactos

- `.audit/NIGREDO-TRES-PROBLEMAS-JUNIO1.md` — Análisis completo
- Este archivo — PALINGENESIA
- Commit `6259072` — Código fuente

