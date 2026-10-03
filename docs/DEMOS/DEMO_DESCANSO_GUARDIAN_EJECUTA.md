# 🌙 PALINGENESIA: Descanso Guardian — Ahora Ejecuta + Recuerda

**Fecha**: Mayo 31, 2026  
**Cambio de Comportamiento**: Computadora ahora ejecuta solicitudes incluso en descanso_guardian tarde, pero con recordatorios amables.

---

## Antes (Comportamiento Antiguo)

```
Usuario (21:30): "Busca el archivo 'reporte.pdf'"

Computadora:
  "Es tarde, señor. ¿Necesita algo urgente? Si no, lo resolveremos mañana con calma."
  
→ Rechazaba la solicitud completamente.
```

---

## Ahora (PALINGENESIA - Nuevo Comportamiento)

```
Usuario (21:30): "Busca el archivo 'reporte.pdf'"

Computadora (interno):
  ✓ Fase = descanso_guardian
  ✓ Hora = 21:30 (>= 20:00, es tarde)
  ✓ Inyectar contexto de descanso: "[CONTEXTO: Es 21h, hora de dormir...]"
  ✓ EJECUTAR la solicitud

Computadora (respuesta):
  "Listo, encontré reporte.pdf en Documentos. 
   (Por cierto, ya son las 21:30... quizás sea hora de descansar cuando termines 😴)"

→ Ejecuta + recuerda ocasionalmente de forma natural.
```

---

## Cómo Funciona

### 1. Detección de Descanso Tarde

En `nlu.py` línea ~1495:

```python
if _fase_circadiana == "descanso_guardian":
    # Es tarde pero EJECUTA de todas formas + recordatorio ocasional
    import datetime
    hora_actual = datetime.datetime.now().hour
    es_realmente_tarde = hora_actual >= 20 or hora_actual < 5
    
    if es_realmente_tarde:
        # Mensaje recordatorio amable pero ejecuta la solicitud
        _ctx_dormir = (
            f"[CONTEXTO: Es {hora_actual:02d}h, hora de dormir. "
            f"El usuario está en descanso_guardian pero ha solicitado ayuda. "
            f"Ejecuta su solicitud CON EFICIENCIA MÁXIMA y sé breve. "
            f"De forma NATURAL y sin insistir, recuérdale ocasionalmente que debería dormir "
            f"(máximo 1-2 veces en la conversación, NO cada mensaje).]"
        )
        self._contexto_descanso_activo = _ctx_dormir
```

### 2. Inyección en Prompt

En `nlu.py` línea ~3680, el contexto se inyecta en los system messages:

```python
# NUEVO: Inyectar contexto de descanso si está activo (recordatorio amable)
if hasattr(self, '_contexto_descanso_activo') and self._contexto_descanso_activo:
    base.append({"role": "system", "content": self._contexto_descanso_activo})
```

Ollama ve en el sistema:
```
[CONTEXTO: Es 21h, hora de dormir. El usuario está en descanso_guardian pero ha solicitado ayuda. 
Ejecuta su solicitud CON EFICIENCIA MÁXIMA y sé breve. De forma NATURAL y sin insistir, 
recuérdale ocasionalmente que debería dormir (máximo 1-2 veces en la conversación, NO cada mensaje).]
```

### 3. Requisitos para Activarse

- ✓ Fase circadiana = `descanso_guardian` (fuera de horario habitual)
- ✓ Hora actual >= 20:00 O hora < 05:00 (realmente tarde o madrugada)
- ✓ Usuario solicita algo (no es "Es tarde" el que se rechaza, es el contexto que se ajusta)

---

## Ejemplos de Conversación Nocturna

### Ejemplo 1: Búsqueda de archivo a las 23:15

```
Usuario:        "¿Dónde está el archivo 'notas_proyecto.txt'?"
Computadora:    "Encontré notas_proyecto.txt en C:\Users\Documentos\proyectos\
                Está siendo usado por VS Code en este momento. 
                Dicho sea de paso, son las 23:15 — considera descansar pronto. 😴"

Usuario:        "Ábrelo con el editor"
Computadora:    "Listo, abierto en el editor. [Ejecuta]"
                (Sin recordar nuevamente — máximo 1-2 veces en conversación)
```

### Ejemplo 2: Programación urgente a las 04:30 (madrugada)

```
Usuario:        "Necesito fixear el bug de login, es urgente"
Computadora:    "Entendido, analizando. [...]
                Encontré el problema en auth.py línea 237.
                Corrección: [código]
                (Son las 4:30 de la mañana — si terminas esto, te recomiendo dormir después 💤)"
```

### Ejemplo 3: No se activa a las 18:30 (no es tarde aún)

```
Usuario (18:30, descanso_guardian pero < 20:00):
        "¿Cómo está el sistema?"
        
Computadora: "Todos los servicios funcionan correctamente. CPU 15%, RAM 42%..."
            (SIN recordatorio — no es hora tard...
```

---

## Control del Usuario

El usuario **siempre tiene control total**:

1. **Puede pedir lo que sea** — Computadora ejecuta (no rechaza)
2. **Recordatorios son amables** — No son advertencias fuertes, sino sugerencias naturales
3. **Máximo 1-2 recordatorios** — Durante la conversación, no en cada mensaje
4. **Puede ignorarlos** — El usuario decide si continúa o duerme

---

## Ajustes Posibles

Si quieres personalizar:

### Cambiar hora de "tarde"
En `nlu.py` línea ~1503:
```python
es_realmente_tarde = hora_actual >= 20 or hora_actual < 5  # ← Ajusta aquí (ej: >= 22)
```

### Cambiar tono del recordatorio
En `nlu.py` línea ~1508, modifica el string `_ctx_dormir`:
```python
_ctx_dormir = (
    f"[CONTEXTO: Es {hora_actual:02d}h, hora de dormir. "
    f"... recuérdale ocasionalmente que debería dormir"  # ← Ajusta el tono aquí
)
```

### Deshabilitar recordatorios (solo ejecutar)
Comenta la línea que inyecta:
```python
# self._contexto_descanso_activo = _ctx_dormir  # ← Comenta para deshabilitar
```

---

## Ventajas

✅ **Funcionalidad mantenida** — Usuario sigue obteniendo ayuda  
✅ **Amable** — Computadora recuerda sin ser molesto  
✅ **Eficiente** — Respuestas breves + directas  
✅ **Inteligente** — Solo activa en horas realmente tardías  
✅ **Flexible** — Fácil ajustar o deshabilitar  

---

**Status**: ✅ IMPLEMENTADO y COMMITEADO  
**Commit**: `ad2e973`  
**Archivo**: [computadora/cerebro/nlu.py](computadora/cerebro/nlu.py)
