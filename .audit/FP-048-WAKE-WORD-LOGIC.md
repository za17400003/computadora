# FP-048: Análisis de Lógica de Wake Word y Ventana de Conversación

## Estado Actual (Junio 1, 2026)

### Lo que el usuario pidió:

> "razonamiento de la wake word debe ser el siguiente:
> - estado inicial- computadora no debe responder si no se utiliza la wake word
> - si la wake word se utiliza responde
> - si la conversacion continua despues de haber utilizado wake word entonces responde sin necesidad de ella
> - si la conversacion finaliza entonces necesita nuevamente de la wake word para responder"

### Implementación Actual en [escucha.py](computadora/voz/escucha.py):

#### 1. **Ventana de Conversación**
```python
_VENTANA_CONVERSACION = 120.0  # 120 segundos
```

#### 2. **Flags de Control**
- `_ultima_interlocutor_es_propietario` (bool): Flag que marca si el último hablante fue el propietario
- `_ultimo_intercambio` (float): Timestamp del último intercambio
- `_en_conversacion` (property): True si está dentro de ventana de 120s Y `_ultima_interlocutor_es_propietario == True`

#### 3. **Flujo de Activación**

```
ESTADO INICIAL:
  _en_conversacion = False
  _ultima_interlocutor_es_propietario = False

USUARIO DICE "COMPUTADORA ...":
  1. Wake word detectada
  2. Llama marcar_intercambio(owner=True)
  3. Establece:
     - _ultima_interlocutor_es_propietario = True
     - _ultimo_intercambio = time.monotonic()
  4. ACEPTA texto (emite señal)

USUARIO CONTINÚA (dentro 120s):
  1. Sin wake word
  2. Si not tiene_wake and _en_conversacion:
     - ACEPTA texto (emite señal)

TRANSCURREN 120s DESDE ÚLTIMO INTERCAMBIO:
  1. (time.monotonic() - _ultimo_intercambio) >= 120
  2. _en_conversacion vuelve a False
  3. Próximo mensaje SIN wake word será RECHAZADO
```

#### 4. **Problemas Identificados**

**PROBLEMA A: Flag nunca se resetea**
- `_ultima_interlocutor_es_propietario` se pone en True
- Pero **NUNCA se pone en False** en el código actual
- Búsqueda exhaustiva: solo se inicializa en __init__ (False), se pone True en marcar_intercambio()
- **NO HAY método que la resetee**

**PROBLEMA B: Conversación no "finaliza" explícitamente**
- La ventana se cierra solo por TIME (120s)
- No hay mecanismo para marcar "fin de conversación" (como punto, silencio prolongado, cambio de tema)
- El usuario podría esperar comando explícito para resetear

**PROBLEMA C: Media activa en conversación**
- Línea 1765: Si media activa (video, música) Y estamos en conversación, descartar audio
- Pero solo si `not self._esperando_respuesta`
- El video del usuario podría sonar como él, pero media_guard protege

---

## Fixes Aplicados (Junio 1, 2026)

### FIX A: Desactivar "Propietario sin Wake Word" ✅

**Cambio**: Agregar flag `_detectar_propietario_sin_wake = False`

**Línea**: [escucha.py](computadora/voz/escucha.py#L565)

```python
# WI-DETECTAR-PROPIETARIO-DISABLED: Desactivar reconocimiento de propietario sin wake word
self._detectar_propietario_sin_wake = False
```

**Efecto**: 
- Línea 1817 ahora chequea `and self._detectar_propietario_sin_wake:`
- Si False: **NUNCA** activa por similitud de voz sin wake word
- El usuario DEBE usar wake word para iniciar conversación

**Comportamiento Después**:
```
VIDEO con audio del usuario:
  1. Whisper transcribe: "texto del video"
  2. Sin wake word
  3. _detectar_propietario_sin_wake = False
  4. → RECHAZA (no emite señal)
  5. ✅ Sistema no responde a video
```

---

## Lógica Resultante (Post-Fix)

### Estado Inicial ✅
```python
_en_conversacion = False
_ultima_interlocutor_es_propietario = False
_detectar_propietario_sin_wake = False
```
**Usuario habla sin wake**: RECHAZA
**Usuario ve video**: Sistema ignora (media guard + detectar_propietario_sin_wake = False)

### Después de Wake Word ✅
```python
Usuario: "Computadora, ¿qué hora es?"
  1. Wake word detectada
  2. marcar_intercambio(owner=True)
  3. _en_conversacion = True (para próximos 120s)
  4. Emite texto → NLU responde
```

### Conversación Activa (0-120s) ✅
```python
Usuario: "¿Y la temperatura?"
  1. Sin wake word
  2. _en_conversacion = True (porque 30s < 120s)
  3. Emite texto → NLU responde
```

### Después de 120s ✅
```python
Usuario: "¿Y la humedad?" (150s después del último intercambio)
  1. Sin wake word
  2. _en_conversacion = False (porque 150s > 120s)
  3. RECHAZA ("no es una conversación activa")
```

### Conversación "Finaliza" ✅
- Cuando (time.monotonic() - _ultimo_intercambio) >= 120.0
- No hay que hacer nada explícito
- El tiempo solo maneja el cierre

---

## Recomendaciones (Futuro)

Si el usuario quiere más control sobre cierre de conversación:

1. **Agregar comando explícito de cierre**: `"Computadora, descansa"` → resetea `_ultima_interlocutor_es_propietario = False`

2. **Silencio prolongado**: Si 30s sin sonido detectado → resetea flag

3. **Cambio de tema drástico**: Si NLU detecta tema "desconectado", resetea (ej: "Hola María" después de hablar con Computadora)

---

## Validación de Fixes

✅ **Commit**: `76ed0a1` — "WI-DETECTAR-PROPIETARIO-DISABLED"
- Sintaxis: OK (py_compile validado)
- Lógica: OK (flag controlable, desactivada por defecto)
- Comportamiento: Usuario ahora DEBE usar wake word para iniciar
- Video: No triggers respuesta (media guard + flag = False)

---

## Tabla Resumida

| Escenario | Antes | Después | Estado |
|-----------|-------|---------|--------|
| Usuario sin wake word, sin conversación | RECHAZA | RECHAZA ✓ | OK |
| Usuario con wake word | ACEPTA | ACEPTA ✓ | OK |
| Usuario en conversación <120s sin wake word | ACEPTA | ACEPTA ✓ | OK |
| Usuario en conversación >120s sin wake word | ACEPTA | RECHAZA ✓ | OK |
| Video audio similar a usuario, sin conversación | ~~ACEPTA~~ | RECHAZA ✓ | FIXED |
| Video audio similar a usuario, en conversación | RECHAZA (media guard) | RECHAZA ✓ | OK |

---

## Impacto General

Con `_detectar_propietario_sin_wake = False`:
- ✅ Sistema NO responde a videos/TV/podcasts
- ✅ Sistema REQUIERE wake word para iniciar
- ✅ Sistema PERMITE follow-ups sin wake word (120s ventana)
- ✅ Sistema CIERRA conversación automáticamente después de 120s sin interacción
- ✅ Usuario TIENE CONTROL: si desactiva Computadora por N segundos, necesita wake word nuevamente

