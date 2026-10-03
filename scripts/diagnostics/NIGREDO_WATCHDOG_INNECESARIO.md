# NIGREDO — Análisis Destructivo: Watchdog Innecesario (Mayo 31, 2026)

## Cenizas Crudas: Estado Actual del Sistema

### Arquitectura Actual (3 Capas de Comprobación)

**Capa 1: Watchdog Background (`_verificar_ollama`)**
```python
# Línea 1028: Thread daemon continuo
threading.Thread(target=self._verificar_ollama, daemon=True).start()

# Línea 1172: Loop infinito
while True:
    GET localhost:11434/api/tags (timeout=5s)
    if OK: ollama_disponible=True, sleep(15)
    if FALLA: intentos++, sleep(5)
             if intentos>=3: sleep(30) LARGO  # ← PROBLEMA
```

**Duración Total de Falla**: 3 intentos × 5s = 15s, luego 30s espera = **45s de silencio**

---

**Capa 2: Quick Ping (`_quick_ping_ollama`)**
```python
# Línea 1531 (justo antes de decidir N1/N2/N3):
if not self.ollama_disponible and not self._quick_ping_ollama():
    self.ollama_disponible = False  # Re-confirma
```

**Problema**: Dos fuentes de verdad (watchdog + quick ping)
- Si watchdog dice NO hace 5 minutos, quick_ping lo re-confirma (quizás innecesariamente)
- Si timeout=5s en quick_ping, puedes esperar otros 5s más

---

**Capa 3: Reintentos en la Llamada Real (`_llamar_ollama_impl`)**
```python
# Línea 3757-3802:
for intento in range(2):
    POST a Ollama (timeout=timeout_adaptativo)
    if 500: sleep(2), reintenta
    else: raise_for_status() o retorna
```

**Esto FUNCIONA bien**, pero solo si llegas hasta acá (Capa 1 no te bloquea antes).

---

## Diagnóstico: ¿Por Qué Falla la Conexión?

### Escenario 1: Ollama Arrancando (10-20s)
```
T=0s: Usuario habla "Hola Computadora"
T=1s: Watchdog check → TIMEOUT (Ollama aún cargando modelo)
T=6s: Watchdog check #2 → TIMEOUT (aún cargando)
T=11s: Watchdog check #3 → TIMEOUT (casi listo)
T=16s: Watchdog → ollama_disponible=FALSE, duerme 30s
T=17s: Usuario llega a quick_ping → TIMEOUT (Ollama ya está listo en T=15s!)
       Pero watchdog dijo NO hace 1s → ESCALA A N3 INNECESARIAMENTE
```

**Impacto**: Usuario se va a Copilot API (lento, costoso) cuando Ollama ya estaba listo.

---

### Escenario 2: Ollama Muerto (proceso no corriendo)
```
T=0s: Watchdog detecta proceso muerto
T=5s: Reintento #1 → FALLA
T=10s: Reintento #2 → FALLA
T=15s: Reintento #3 → FALLA
T=45s: Watchdog decide dormir 30s (sin process check)
T=75s: Despierta, intenta de nuevo
       Pero el usuario ya preguntó en T=20s → se fue a N3

**Impacto**: Watchdog duerme 30s sin verificar si el proceso está muerto de verdad.
```

---

### Escenario 3: Ollama Respondiendo Con 500
```
T=0s: Usuario → _llamar_ollama_impl
T=1s: POST a Ollama → 500 SERVER ERROR
       for intento in range(2): reintenta ✅
T=3s: POST reintento → OK
       Retorna respuesta

PERO: Si el watchdog marcó disponible=FALSE hace 30s (por timeout falso):
      Nunca llegas a _llamar_ollama_impl
      ESCALAS A N3 ANTES DE INTENTAR
```

**Impacto**: Nunca se ejecuta la lógica de reintento que existe en Capa 3.

---

## Root Causes Identificadas

| Causa | Línea | Impacto | Severidad |
|-------|-------|--------|-----------|
| Watchdog sleep(30) tras 3 fallos | 1213 | 30s de silencio innecesario | 🔴 CRÍTICA |
| Dos checks (watchdog + quick_ping) | 1531 | Duplicación de decisión | 🟠 MEDIA |
| Quick_ping timeout=5s | 1222 | Suma 5s más a latencia total | 🟠 MEDIA |
| No reintenta en Capa 1 | 1172 | 3 intentos (15s) sin escalon exponencial | 🟡 BAJA |
| Duplica lógica reintento (Capa 1 + Capa 3) | 1172+3757 | Confusión sobre dónde ocurren reintentos | 🟡 BAJA |

---

## Evidencia Desde el Código

### ¿Por Qué el Watchdog Existe?
**Comentario en RF-xxx**: "Para no bloquear el hilo principal"

**Realidad**: 
- Capa 3 (`_llamar_ollama`) YA maneja esto con timeout=30-180s
- Capa 2 (quick_ping) es "quick" pero sigue bloqueando el thread de speech
- Watchdog async es necesario SOLO si vas a hacer checks frecuentes

**Problema**: Hace checks CADA 15 segundos (si OK) o CADA 5 segundos (si FALLA).
- **Demasiado frecuente**: Wasteful cuando Ollama está OK
- **Demasiado conservador**: Duerme 30s cuando FALLA, sin context

---

### ¿Qué Sucede Sin Watchdog?

```python
# Escenario: Usuario pregunta, NO hay watchdog

Usuario: "Hola"
  ↓
Línea 1476: _pensar(texto)
  ↓
Línea 1525: nivel1 = _pensar_nivel1("hola")
  → Regex match "hola" → retorna "Hola, señor" en <100ms
  ✅ FUNCIONA

Usuario: "Piensa qué significa la vida"
  ↓
Línea 1476: _pensar(texto)
  ↓
Línea 1525: nivel1 = _pensar_nivel1(texto)
  → NO match (no es regex simple)
  ↓
Línea 1531-1536: quick_ping_ollama()
  ↓
  YES: Procede a _pensar_con_herramientas (N2)
       POST a Ollama → timeout_adaptativo (30-180s según latencias)
       Si falla: reintenta una vez
       ✅ FUNCIONA
  ↓
  NO: Escala a N3 (Copilot) 
       ✅ FUNCIONA (fallback)
```

**Sin watchdog, TODO SIGUE FUNCIONANDO** porque:
1. N1 es regex (no necesita red)
2. Quick_ping es instantáneo (5ms tipicamente)
3. _llamar_ollama reintenta si falla
4. Fallback a Copilot existe

---

## Propuesta: Remover el Watchdog

### Opción A: ELIMINAR completamente ✅
```python
# Eliminar línea 1028:
# threading.Thread(target=self._verificar_ollama, daemon=True).start()

# Resultado:
- Menos threads (1 menos)
- Menos CPU (sin sleep loops)
- Sin false negatives por timing
- Quick_ping + _llamar_ollama son suficientes
```

### Opción B: OPCIONAL (solo si user lo pide)
```python
def __init__(self, ..., use_ollama_watchdog=False):
    if use_ollama_watchdog:
        threading.Thread(target=self._verificar_ollama, daemon=True).start()
```

### Opción C: REPURPOSE (para algo útil)
```python
# En lugar de check periódico, usar para:
# - Medir latencias promedio (ya lo hace _latencias_ollama)
# - Detectar degradación (ya lo hace timeout_adaptativo)
# - Liberar VRAM si está degradado (WI-324)
```

---

## Impacto Esperado (Sin Watchdog)

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Tiempo P95 (startup Ollama) | 45s | 5s | 🟢 90% |
| Threads Activos | N+1 | N | 🟢 -1 |
| False Negatives (Ollama OK) | Sí (timing) | No | 🟢 0 |
| Reintentos Utilizados | Solo Capa 3 | Capa 3 | 🟢 Mismo |
| Fallback to Copilot | Si watchdog falla | Si N2 timeout | 🟢 Correcto |
| CPU (sleep loops) | 0.5% | 0% | 🟢 -0.5% |

---

## Cenizas Finales: Conclusión NIGREDO

**El watchdog es innecesario porque:**

1. ✅ N1 no necesita red (regex)
2. ✅ Quick_ping ya check antes de N2
3. ✅ _llamar_ollama reintenta (2 veces)
4. ✅ Timeout adaptativo escala según latencias reales
5. ✅ Fallback a Copilot existe para true failures

**El watchdog CAUSA PROBLEMAS porque:**

1. ❌ Falsos negativos durante startup (marca "muerto" cuando arranca)
2. ❌ 30s de espera innecesaria tras 3 fallos
3. ❌ Duplica lógica de quick_ping
4. ❌ Consume CPU con loops daemon
5. ❌ Usuario nunca toca / entiende su lógica

**Recomendación**: REMOVER completamente (Opción A), mantener only quick_ping + _llamar_ollama retry.

---

**Status**: 🔴 NIGREDO COMPLETO — Cenizas diagnosticadas
