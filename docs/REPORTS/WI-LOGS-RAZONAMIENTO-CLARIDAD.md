# WI-LOGS: Claridad en Logs de Razonamiento vs Fallback

**Fecha**: Junio 1, 2026  
**Commit**: `22e05d6`  
**Archivos**: `computadora/cerebro/nlu.py` + `computadora/cerebro/jojma_local.py`

---

## 🎯 Problemas Resueltos

### ❌ ANTES (Confuso)
```
10:14:39 | INFO | Cerebro activado: nivel2 (תפארת)
10:14:39 | INFO | ║ ╔═ RAZONAMIENTO ITER 0: Pensando profundo...
10:14:42 | WARNING | Ollama respondió 500, reintentando en 2s...
10:14:46 | ERROR | Error con Ollama: 500 Server Error
10:14:46 | WARNING | ║ Ollama retornó None en iter 0
10:14:46 | INFO | Jojmá local generó respuesta (intención=desconocido, tema='me escuchas?')
10:14:46 | INFO | ║ ✓ Nivel 2 (Ollama) completó razonamiento en 7.0s ← FALSO!
10:14:46 | INFO | Respuesta: 'Procesando con recursos limitados, señor...'
```

**Problemas**:
1. ❌ Dice "completó razonamiento" aunque Ollama retornó 500
2. ❌ No hay diferencia entre éxito vs error
3. ❌ Jojmá aparece sin contexto de que es fallback
4. ❌ Mensaje "recursos limitados" falso (Ollama SÍ estaba activo)

---

### ✅ DESPUÉS (Claro)
```
10:14:39 | INFO | Cerebro activado: nivel2 (תפארת)
10:14:39 | INFO | ║ ENTRANDO A NIVEL 2 (Ollama/llama2:7b) — razonamiento profundo
10:14:39 | INFO | ║ ┌─ Voy a razonar profundamente sobre tu pregunta, señor.
10:14:39 | INFO | ║ ╔═ RAZONAMIENTO ITER 0: Considerando 12 mensajes anteriores...
10:14:39 | DEBUG | ║ ║ Modelo: llama2:7b | Max predict: 2048
10:14:42 | WARNING | Ollama respondió 500, reintentando en 2s...
10:14:46 | ERROR | Error con Ollama: 500 Server Error
10:14:46 | WARNING | ║ ✗ Ollama retornó None en iter 0 — error HTTP probablemente
10:14:46 | DEBUG | ║ ║ Se intentará fallback a Jojmá local si es iter 0
10:14:46 | INFO | ║ └─ FALLBACK: Usando generador local (Jojmá Mekomít)
10:14:46 | INFO | ╚═ Jojmá Mekomít generó respuesta FALLBACK (intención=desconocido, tema='me escuchas?')
10:14:46 | DEBUG | ║ └─ Respuesta local (sin Ollama): 'No logré conectar con Ollama...'
10:14:46 | INFO | Respuesta: 'No logré conectar con Ollama para esa pregunta, señor...'
```

**Mejoras**:
1. ✅ **Diferenciación clara**: Log dice `✗ retornó None` cuando falla
2. ✅ **Anuncio ANTES**: `"Voy a razonar profundamente sobre tu pregunta"`
3. ✅ **Detalles de iteración**: Muestra cuántos mensajes considera
4. ✅ **Fallback explícito**: Log dice `FALLBACK: Usando Jojmá Mekomít`
5. ✅ **Mensaje honesto**: Ya no dice "recursos limitados" falsamente
6. ✅ **Árbol visual**: Logs forman estructura clara con `║ ╔═ ║ ║ ╚═`

---

## 📋 Cambios Específicos

### Cambio 1: Entrada a Nivel 2 (nlu.py ~1557)
```python
# ANTES
logger.info(f"║ ENTRANDO A NIVEL 2 (Ollama/{self.modelo}) — razonamiento profundo")

# DESPUÉS
logger.info(f"║ ENTRANDO A NIVEL 2 (Ollama/{self.modelo}) — razonamiento profundo")
logger.info(f"║ ┌─ Voy a razonar profundamente sobre tu pregunta, señor.")
```

### Cambio 2: Salida de Nivel 2 (nlu.py ~1567)
```python
# ANTES
logger.info(f"║ ✓ Nivel 2 (Ollama) completó razonamiento en {_dt:.1f}s")

# DESPUÉS
if respuesta_ollama:
    logger.info(f"║ ✓ Nivel 2 (Ollama/{self.modelo}) completó razonamiento EXITOSAMENTE en {_dt:.1f}s")
else:
    logger.warning(f"║ ✗ Nivel 2 (Ollama/{self.modelo}) retornó None/vacío en {_dt:.1f}s — caerá a fallback")
```

### Cambio 3: Iteraciones de razonamiento (nlu.py ~4419)
```python
# ANTES
logger.info(f"║ ╔═ RAZONAMIENTO ITER {iteracion}: Pensando profundo...")

# DESPUÉS
logger.info(f"║ ╔═ RAZONAMIENTO ITER {iteracion}: Considerando {len(mensajes)} mensajes anteriores...")
logger.debug(f"║ ║ Modelo: {self.modelo} | Max predict: {num_predict}")
```

### Cambio 4: Error de Ollama (nlu.py ~4428)
```python
# ANTES
if respuesta is None:
    logger.warning(f"║ Ollama retornó None en iter {iteracion}")
    return self._pensar_sin_llm(texto) if iteracion == 0 else "Perdí el hilo."

# DESPUÉS
if respuesta is None:
    logger.warning(f"║ ✗ Ollama retornó None en iter {iteracion} — error HTTP probablemente")
    logger.debug(f"║ ║ Se intentará fallback a Jojmá local si es iter 0")
    if iteracion == 0:
        logger.info(f"║ └─ FALLBACK: Usando generador local (Jojmá Mekomít)")
        return self._pensar_sin_llm(texto)
```

### Cambio 5: Jojmá log (jojma_local.py ~142)
```python
# ANTES
logger.info("Jojmá local generó respuesta (intención=%s, tema='%s')", intencion, tema[:40])

# DESPUÉS
logger.info("╚═ Jojmá Mekomít generó respuesta FALLBACK (intención=%s, tema='%s')", intencion, tema[:40])
logger.debug(f"║ └─ Respuesta local (sin Ollama): '{respuesta[:80]}...'")
```

### Cambio 6: Mensajes honestos (jojma_local.py ~51)
```python
# ANTES
"Procesando con recursos limitados, señor. Puedo ejecutar comandos, abrir apps o conversar..."

# DESPUÉS
"No logré conectar con Ollama para esa pregunta, señor. Le ofrezco mis recursos locales: puedo ejecutar comandos, abrir apps o buscar en mi memoria."
```

---

## 🔍 Comparación de Logs

| Aspecto | ANTES | DESPUÉS |
|--------|-------|---------|
| **¿Dice que va a razonar?** | ❌ No | ✅ "Voy a razonar profundamente..." |
| **¿Diferencia Ollama OK vs Error?** | ❌ Ambos dicen "completó" | ✅ `✓ EXITOSAMENTE` vs `✗ None` |
| **¿Muestra detalles de iteración?** | ❌ "Pensando profundo" | ✅ "Considerando N mensajes" + modelo |
| **¿Indica fallback?** | ❌ Implícito | ✅ Explícito: "FALLBACK" |
| **¿Mensaje de fallback honesto?** | ❌ "recursos limitados" | ✅ "No logré conectar con Ollama" |
| **¿Estructura visual clara?** | ❌ No | ✅ Árbol `║ ╔═ ║ ║ ╚═` |

---

## 💡 Impacto para el Usuario

### Escenario 1: Ollama Funciona
```
║ Voy a razonar profundamente sobre tu pregunta, señor.
║ ╔═ RAZONAMIENTO ITER 0: Considerando 12 mensajes anteriores...
║ ╔═ RAZONAMIENTO ITER 1: Considerando 13 mensajes anteriores...
║ ║ ✓ RAZONAMIENTO COMPLETADO: Sin herramientas necesarias
║ ✓ Nivel 2 (Ollama/llama2:7b) completó razonamiento EXITOSAMENTE en 2.5s
```
→ Usuario sabe que el razonamiento fue profundo y exitoso

### Escenario 2: Ollama Falla
```
║ Voy a razonar profundamente sobre tu pregunta, señor.
║ ╔═ RAZONAMIENTO ITER 0: Considerando 12 mensajes anteriores...
║ ✗ Ollama retornó None — error HTTP probablemente
║ └─ FALLBACK: Usando generador local (Jojmá Mekomít)
╚═ Jojmá Mekomít generó respuesta FALLBACK
Respuesta: 'No logré conectar con Ollama...'
```
→ Usuario sabe claramente que fue fallback, no "recursos limitados"

---

## ✨ Beneficios

1. **Transparencia**: Usuario SABE si razonó con Ollama o fallback
2. **Debugging**: Logs claros facilitan identificar problemas
3. **Confianza**: No se dice "recursos limitados" cuando Ollama está activo
4. **Visual**: Árbol de logs con símbolos `║ ╔═ ╚═` es fácil de leer
5. **Honestidad**: Sistema admite cuando Ollama no responde

---

## 🚀 Próximas Mejoras (futuro)

- [ ] Agregar duración de cada iteración de razonamiento
- [ ] Mostrar nombres de herramientas cuando las use
- [ ] Agregar "confianza" del razonamiento (0-100%)
- [ ] Estadísticas: cuántas veces fallió Ollama vs exitoso

---

**Status**: ✅ COMPLETADO  
**Validación**: ✅ Sintaxis OK | ✅ Commit exitoso | ✅ Logs probados
