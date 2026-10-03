# NIGREDO — Análisis Exhaustivo de 3 Problemas (Junio 1, 2026)

## Problema 1: Whisper Lento en Primera Interacción ❌

### Hallazgo
**Línea 1013-1014 de [escucha.py](computadora/voz/escucha.py#L1013-L1014)**:
```python
# WI-BERESHIT-DEADLOCK-FIX: NO cargar Whisper aquí (bloquea Qt event loop)
# En su lugar, cargar lazy en primer uso dentro de _bucle_escucha()
```

**Causa Raíz**: Whisper está configurado para LAZY LOAD (cuando se necesita) en lugar de EAGER LOAD (al inicio) porque se asumía que bloquearía Qt event loop.

**Evidencia en Logs del Usuario**:
```
10:50:18 | INFO | computadora_app - ✅ Whisper cargado exitosamente en cuda
  0%|                                                                                      | 0/300 [00:01<?, ?frames/s]
10:50:20 | INFO | computadora_app - ✅ GPU funcional: dummy transcribe en 1.83s
10:50:21 | INFO | computadora_app - Whisper: 'Hola, computadora, ¿cómo estás?'
```

Whisper se carga EN LA PRIMERA INTERACCIÓN (10:50:18-10:50:20), retrasando la respuesta.

---

## Problema 2: Falta Estructura de Razonamiento en Logs ❌

### Hallazgo
**Línea 4434 de [nlu.py](computadora/cerebro/nlu.py#L4434)** — Log que DEBERÍA aparecer:
```python
logger.info(f"║ ╔═ RAZONAMIENTO ITER {iteracion}: Considerando {len(mensajes)} mensajes anteriores...")
```

**Causa Raíz**: El log está dentro de `_pensar_con_herramientas()` que es llamada solo si Ollama responde en línea 1567. Si Ollama falla, entra en fallback (línea 4441-4448) sin mostrar "RAZONAMIENTO ITER".

**Evidencia en Logs del Usuario**:
```
10:50:34 | WARNING | computadora_app - Ollama streaming retornó 500. Intentando llamada sin stream...
10:52:06 | ERROR | computadora_app - Timeout esperando a Ollama
10:52:22 | INFO | computadora_app - Respuesta: 'Estoy de buen ánimo...'
```

**NOTA**: Ollama está fallando → fallback inmediato → NO muestra estructura de razonamiento. Los logs de "RAZONAMIENTO ITER" nunca se ejecutan porque `respuesta is None` en iteración 0, causando fallback a `_pensar_sin_llm()`.

---

## Problema 3: Heatmap Invertido — Posicionamiento en Zonas Rojas ❌

### Hallazgo
**Línea 726-735 y 777 de [vida_autonoma.py](computadora/interfaz/vida_autonoma.py#L726-L777)**:

Mi "fix" anterior tiene lógica INVERTIDA:

```python
# Mi formula (INCORRECTA):
hist_score = 1.0 / (1.0 + self._heatmap[row][col] * 0.01)  # Alto en FRÍO
reciente_score = 1.0 / (1.0 + self._heatmap_reciente[row][col] * 0.05)

# Pero selección usa MIN (busca SCORE BAJO):
mejor = min(validos, key=lambda p: self._score_posicion(p.x(), p.y()))
```

**PROBLEMA**: 
- Zona fría (heatmap=0): score = 1.0 / 1.0 = **1.0**
- Zona roja (heatmap=100): score = 1.0 / 2.0 = **0.5**

`min()` selecciona score BAJO → **SELECCIONA ZONAS ROJAS** ❌

**Debería ser**:
- Zona fría: score **BAJO** (preferida por `min()`)
- Zona roja: score **ALTO** (evitada por `min()`)

**Causa Raíz**: Invertí la fórmula en dirección equivocada. Debería ser:
```python
score = heatmap_value  # O: score = heatmap_value / (1.0 + heatmap_value)
```

Para que MIN elija zonas frías.

---

## Resumen de Causas Raíz

| Problema | Ubicación | Causa | Síntoma |
|----------|-----------|-------|---------|
| 1 | `escucha.py:1013-1014` | Lazy load por miedo a bloquear Qt | Whisper carga en 1ª interacción |
| 2 | `nlu.py:4434 + escucha.py:4441` | Ollama falla → fallback inmediato sin logs RAZONAMIENTO ITER | No muestra estructura |
| 3 | `vida_autonoma.py:726-777` | Fórmula invertida + MIN selecciona score bajo | Va a zonas rojas |

---

## Status Problemas

✅ **NIGREDO completo**: Hallazgos identificados con evidencia  
⏳ **Próximas fases**: ALBEDO (síntesis) → CITRINITAS (soluciones) → RUBEDO (fix) → PALINGENESIA (validación)

