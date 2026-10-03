# WI-INTEGRAL: Diagnóstico de 6 Problemas Críticos

**Fecha**: Junio 1, 2026  
**Severidad**: 🔴 CRÍTICO (visual) + ⚠️ IMPORTANTE (lógica)  
**Usuario**: "arregla todo pero añade arreglos a lo siguiente también"  
**Tria Prima**: `por favor` + `gracias` + `amén` = ciclo profundo + autónomo

---

## 📋 Problemas Identificados

### PROBLEMA 1: Log Contradictorio (CRÍTICO LÓGICA)

**Evidencia de logs**:
```
10:33:25 | WARNING | ║ ✗ Ollama retornó None en iter 0
10:33:25 | INFO | ║ └─ FALLBACK: Usando generador local (Jojmá Mekomít)
10:33:25 | INFO | ║ ✓ Nivel 2 (Ollama/llama2:7b) completó razonamiento EXITOSAMENTE ← FALSO!
```

**Causa raíz**:
- Método `_pensar_con_herramientas()` internamente hace fallback a `_pensar_sin_llm()`
- Wrapper superior ve que `respuesta_ollama` no es None (tiene fallback)
- Wrapper registra "EXITOSAMENTE" aunque fue fallback

**Archivo**: `computadora/cerebro/nlu.py` (línea ~1569)

**Solución**: Agregar bandera `_fue_fallback` para comunicar estado verdadero

---

### PROBLEMA 2: Desaparición en Bordes (CRÍTICO VISUAL)

**Síntoma**: Cuando se mueve autónomamente a su meta y llega a un borde, desaparece momentáneamente

**Causa probable**:
- Al llegar al borde, la posición queda fuera de bounds
- Culling/clipping desactiva renderizado
- Transición de animación no suave

**Archivo**: `computadora/interfaz/vida_autonoma.py` (línea ~482+)  
**Componente**: Animador de movimiento autónomo

**Solución**: 
1. Verificar bounds cuando se llega a meta
2. Agregar "zona de seguridad" cerca de bordes
3. Transición suave en entrada/salida

---

### PROBLEMA 3: Heatmap Ignorado (CRÍTICO LÓGICA)

**Síntoma**: Heatmap muestra zona roja (donde trabajas) pero Computadora se posiciona EXACTAMENTE ahí

**Causa probable**:
- Algoritmo de "no estorbar" existe en código pero NO se ejecuta
- O la prioridad está invertida (busca ZONAS ROJAS en vez de evitarlas)
- Carga del heatmap falla silenciosamente

**Archivo**: `computadora/interfaz/vida_autonoma.py` (línea ~548+)  
**Componente**: `_elegir_posicion()` o equivalente

**Solución**:
1. Verificar que heatmap se carga correctamente
2. Invertir lógica: `min(heatmap)` para zonas frías, NO `max(heatmap)`
3. Agregar log de decisión de posición

---

### PROBLEMA 4: Congelamiento 1s (IMPORTANTE PERFORMANCE)

**Síntoma**: ~Cada segundo la interfaz de Computadora se detiene un poquito

**Causa probable**:
- Actualización de recursos del sistema (CPU, RAM, GPU)
- Operación bloqueante en hilo principal
- Lock en acceso a memoria compartida

**Archivo**: `computadora/utilidad/monitor_recursos.py`  
**Frecuencia**: ~1 segundo (interval de actualización)

**Solución**:
1. Mover monitor a thread separado (si no está ya)
2. Reducir frecuencia de actualizaciones
3. Usar lock-free primitives o cola thread-safe

---

### PROBLEMA 5: Razonamiento Autónomo Sin Wake Word (IMPORTANTE LÓGICA)

**Escenario**: Usuario viendo video, Computadora se pone a razonar sola

**Evidencia**:
```
10:31:39 | INFO | Voz propietario reconocida sin wake word (sim=0.77)
10:31:45 | INFO | Conversación activa, sin wake word
10:31:41 | INFO | ENTRANDO A NIVEL 2 (razonamiento profundo)
```

**Causa probable**:
- Similitud 0.77 con propietario dispara reconocimiento
- Video contiene voz similar al propietario
- Configuración permite respuesta "sin wake word" en ciertos contextos
- Debería detectar "es video" y NO responder

**Archivo**: `computadora/voz/escucha.py` (línea ~?)  
**Lógica**: Wake word check + contexto (¿es video?)

**Solución**:
1. Agregar contexto "¿estoy viendo video?"
2. Aumentar umbral de similitud (0.77 es bajo)
3. Requerir wake word INCLUSO si es propietario

---

### PROBLEMA 6: Anillos Estáticos (IMPORTANTE VISUAL)

**Síntoma**: Anillos de Computadora no se mueven

**Deseado**:
- Anillo externo: torque positivo (CW)
- Anillo siguiente: torque negativo (CCW)
- Anillo siguiente: torque positivo (CW)
- Anillo siguiente: torque negativo (CCW)

**Archivo**: 
- `computadora/interfaz/animador_orbe_4d.py` (probable)
- `computadora/interfaz/dibujante_orbe.py` (probable)

**Estado actual**: Anillos fijos, sin rotación

**Solución**: Implementar animación de rotación alternada

---

## 🔍 Análisis Causal

```
                       RAÍZ
                        │
                ┌───────┴────────┐
                │                │
          LOGS NO SE     VISUALIZACIÓN
         ACTUALIZAN      CONGELADA
          (1,2)          (3,4)
             │               │
             ├── Bug log      ├── Bordes (1s lock)
             │   EXITOSO      │
             │   en fallback   │
             │                ├── Heatmap
             │                │   invertido
             │                │
             │                ├── Anillos
             │                │   no rotan
             │                │
             └─ Razonamiento  └── Desaparición
                 autónomo         en bordes
                 (video→wake)
```

---

## 📊 Prioridad de Arreglos

1. **IMMEDIATO**: Log contradictorio (P0 - lógica falsa)
2. **IMMEDIATO**: Heatmap invertido (P1 - perjudica UX)
3. **INMEDIATO**: Razonamiento autónomo (P1 - inesperado)
4. **RÁPIDO**: Anillos rotan (P2 - visual)
5. **MODERADO**: Bordes desaparición (P2 - visual)
6. **MODERADO**: Congelamiento 1s (P3 - performance)

---

## 🎯 Plan de Ataque (Orden de Ejecución)

### FASE NIGREDO (Diagnóstico — 10 min)
- [ ] Verificar estado actual de logs
- [ ] Buscar código de heatmap
- [ ] Buscar código de razonamiento autónomo
- [ ] Buscar código de anillos

### FASE ALBEDO (Investigación)
- [ ] Leer `vida_autonoma.py` línea 482+
- [ ] Leer `escucha.py` línea ~ (wake word check)
- [ ] Leer `animador_orbe_4d.py`
- [ ] Leer `monitor_recursos.py`

### FASE CITRINITAS (Síntesis)
- [ ] Unificar hallazgos
- [ ] Identificar interdependencias
- [ ] Crear plan de fixes

### FASE RUBEDO (Implementación)
- [ ] Fix log contradictorio
- [ ] Fix heatmap invertido
- [ ] Fix razonamiento autónomo
- [ ] Fix anillos
- [ ] Fix bordes (si tiempo)
- [ ] Fix congelamiento (si tiempo)

### FASE PALINGENESIA (Validación)
- [ ] Tests de cada fix
- [ ] Verificación visual
- [ ] Logs limpios
- [ ] Commits y documentación

---

## 📝 Notas

- Usuario dijo "gracias, amén" → ejecutar profundo + autónomo
- Todos estos problemas podrían estar conectados (e.g., congelamiento causa desaparición en bordes)
- Necesito acceso a files completos para hacer fixes precisos

---

**Status**: DIAGNÓSTICO COMPLETADO  
**Siguiente**: Implementar fixes en cascada
