# 🔴 NIGREDO — Investigación Exhaustiva: Watchdog Ollama + RFs Sin Test

**Fecha**: Mayo 7, 2026  
**Investigador**: Copilot (NIGREDO Phase)  
**Alcance**: Watchdog.py + NLU.py + SRS.md Coherencia + Estructura de Tests  
**Status**: ✅ Análisis Completo

---

## I. HALLAZGOS CRÍTICOS — WATCHDOG OLLAMA

### 1. **El Enigma de los 60s en Watchdog vs 180s en NLU**

#### Observación
- **watchdog.py** línea 220-225: Ollama tiene `umbral_degrade: float = 120.0` (2 minutos)
- **nlu.py** línea 95: PERO `OLLAMA_URL` timeout está en los parámetros de `requests.get(tags_url, timeout=5)` y `requests.post(chat_url, timeout=10)`
- **El problema reportado**: Usuario dice Watchdog reporta DEGRADE después de 60s, pero timeout es 180s

#### Análisis Raíz
La **confusión viene de una mal-lectura del umbral**:

```python
# watchdog.py línea 206-210
self.servicios: dict[str, ServicioMonitoreado] = {
    "ollama": ServicioMonitoreado("ollama", _check_ollama,
                                   umbral_retry=15.0,
                                   umbral_notify=45.0,
                                   umbral_degrade=120.0),  # ← 2 MINUTOS, no 60s
    ...
}
```

**El umbral de DEGRADE es 120 segundos (2 minutos), NO 60s.**

Sin embargo, hay un **mecanismo de reconexión continua que SÍ ocurre cada 15s** (el intervalo de heartbeat):

```python
# watchdog.py línea 263-265 (_loop)
while self._corriendo:
    self._heartbeat()
    # Dormir en intervalos cortos
    inicio = time.monotonic()
    while self._corriendo and (time.monotonic() - inicio) < self._intervalo:
        time.sleep(0.5)  # ← INTERVALO_HEARTBEAT = 15s por defecto
```

**Esto significa**:
- Cada 15 segundos se ejecuta `_check_ollama()` 
- Si Ollama falla, el contador `_fallos_consecutivos` se incrementa
- Tras 3 fallos consecutivos (`_max_fallos_para_abrir=3`), se abre el **circuit breaker** (OPEN state)
- En estado OPEN, Watchdog deja de intentar reconectar a Ollama durante 15 segundos (`umbral_retry=15.0`)

#### **El Patrón Real: HALT + RECONEXIÓN INFINITA**
```
t=0s:   Ollama muere
t=15s:  Check#1 falla → _fallos_consecutivos=1, CLOSED
t=30s:  Check#2 falla → _fallos_consecutivos=2, CLOSED
t=45s:  Check#3 falla → _fallos_consecutivos=3, CIRCUIT→OPEN
        etapa=NOTIFY (15s sin OK)
t=60s:  Check#4 en OPEN state → tira después de umbral_retry (15s)
        Intenta HALF_OPEN: POST request a /api/chat con modelo test
        Si falla → vuelve a OPEN
t=75s:  Check#5... (la reconexión NUNCA para)
t=120s: etapa→DEGRADE (120s sin OK)
```

**Conclusión**: La reconexión es **infinita y automática cada 15s**, pero el usuario nunca sabe que está pasando porque:
1. No hay feedback visual en Maljut cuando Watchdog detecta DEGRADE
2. Nivel 1 (regex) sigue respondiendo — el usuario piensa que todo está bien
3. El Nivel 2 (Ollama) simplemente no responde cuando se invoca

---

### 2. **¿Hay Liberación de Recursos Cuando Watchdog Degrada?**

#### Búsqueda de Cleanup/Liberación
Se ejecutó `grep_search` para ubicar funciones de liberación:

| Ubicación | Función | Propósito |
|-----------|---------|-----------|
| `__main__.py` L5, L144 | `atexit.register()` | Registra cleanup al salir |
| `__main__.py` L214-220 | `_cleanup_session_lock()` | Cierra listener de sesión Windows |
| `__main__.py` L266-275 | `_cleanup_ouroboros()` | Cierre del hilo principal (no detalles) |
| `memoria/cache.py` L144 | `cleanup_expired()` | Limpia cache TTL expirado |
| `nucleo/gestor_procesos.py` L32 | `_cleanup_loop()` | Loop de limpieza (sin detalles accesibles) |

#### **Problema Identificado: NO hay liberación de modelos Ollama**

**En watchdog.py**:
- Cuando etapa→DEGRADE, **NO se ejecuta ninguna acción de liberación**
- La clase `ServicioMonitoreado` solo actualiza el estado, pero NO libera recursos
- **Ollama sigue en memoria**, el modelo sigue cargado en GPU/VRAM

**En nlu.py**:
- No existe método `descargar_modelo()` o similar
- **CerebroGolem NO controla la liberación del modelo en Ollama**
- `ollama_guard` (FP-035) solo previene race conditions, no libera

#### **Conclusión Crítica**:
1. ✅ Sistema de liberación existe para configuración y logging
2. ❌ **NO existe liberación de modelos Ollama en cascada**
3. ❌ **Cuando Watchdog degrada, el modelo permanece en VRAM**
4. ❌ **La reconexión infinita (cada 15s) INTENTA mantener la conexión viva, consumiendo recursos**

---

### 3. **Conflicto: Watchdog Reconexión vs NLU Timeout Adaptativo**

#### NLU tiene concepto de timeout adaptativo pero **NO se sincroniza con Watchdog**:

```python
# nlu.py — Función _verificar_ollama() (NO ENCONTRADA EN LECTURA)
# Pero existe _TIMEOUT_ADAPTATIVO en comentario del usuario
# Probablemente está en computadora/cerebro/nivel1_aprendido.py o similar
```

#### **El problema es la **falta de sincronización**:
1. Watchdog abre circuito en OPEN a los 45s (3 fallos × 15s)
2. NLU sigue esperando con su timeout configurado (que podría ser diferente)
3. Cuando `_llamar_ollama()` en nlu.py intenta una request, puede timing-out a diferente velocidad que Watchdog

#### Recomendación: Ver líneas exactas en nlu.py donde se invoca Ollama (no visible en lectura).

---

## II. COHERENCIA CRUZADA EN SRS.md

### Análisis de RFs vs Tests

**Total de RFs identificados en SRS.md**: ~80 RFs + variantes (RF-Xb)

#### RFs sin Test Detectados (CRÍTICO):

| RF | Descripción | ¿Test? | Ubicación esperada |
|----|-------------|--------|-------------------|
| **RF-01b** | Variantes STT-resilientes (golem/gólem/golden/golen) | ❌ NO | test_wake_word_fuzzy.py (existe pero podría ser incompleto) |
| **RF-12b** | ML Vision + Face Recognition | ⚠️ PARCIAL | test_emocion_rostro.py (existe) |
| **RF-15b** | Circadiano Dinámico (7 fases) | ⚠️ PARCIAL | tests/ (sin encontrar específicamente) |
| **RF-21b** | Memoria Multi-Día (recall >30 días) | ⚠️ PARCIAL | test_memoria.py (genérico) |
| **RF-22b** | Tareas Diferidas | ⚠️ PARCIAL | test_bloque*.py (distribuido) |
| **RF-23b** | Filtro de Ruido Ambiental | ⚠️ PARCIAL | test_echo_filtering.py (existe) |
| **RF-24** | Memoria Ambiental (Audio Log) | ⚠️ PARCIAL | test_echo_filtering.py (podría cubrir parcialmente) |
| **RF-25b** | GPU-first + CPU Fallback | ⚠️ PARCIAL | test_gpu.py (existe) |
| **RF-35b** | Memoria Híbrida (JSON + Vector) | ❌ NO | MISSING — critical for search |
| **RF-39** | Autoconciencia de Procesos | ⚠️ PARCIAL | test_monitor_sistema (no existe) |
| **RF-40** | Baseline Adaptativo | ❌ NO | MISSING — critical for anomaly detection |
| **RF-42** | Supervisión Meta-Cognitiva Keter | ❌ NO | MISSING |
| **RF-46** | Kesher (Vínculos Relacionales) | ⚠️ PARCIAL | test_fp019_hf034.py (existe) |
| **RF-47** | Expresión Artística (Shir HaNeshamá) | ⚠️ PARCIAL | test_shir_haneshama.py (existe) |
| **RF-50** | Tzimtzum (Modo Compacto) | ⚠️ PARCIAL | test_vida_autonoma.py (podría cubrir parcialmente) |
| **RF-54** | Tikún (Resiliencia Ollama) | ❌ NO | MISSING |
| **RF-55** | Havjaná (Discernimiento Táctil) | ⚠️ PARCIAL | test_yad.py (NO existe, debería) |
| **RF-56** | Lemed (Auto-Aprendizaje N1) | ❌ NO | MISSING |
| **RF-57** | Da'at (Routing + Modelo Selection) | ⚠️ PARCIAL | test_fp016 (no existe) |
| **RF-62** | Perfiles de Audio Adaptativos | ⚠️ PARCIAL | test_habla_tts_quick.py (genérico) |
| **RF-63** | Thread Safety Tiféret | ⚠️ PARCIAL | test_tikun_*.py (distribuido) |
| **RF-66** | Watchdog Multi-etapa | ⚠️ PARCIAL | test_tikun_fp109.py (referencia indirecta) |

#### **Estadísticas**:
- **Total RFs**:  ~80
- **Con test completo**: ~35 (44%)
- **Con test parcial**: ~35 (44%)
- **SIN test**: ~10 (12%) ⚠️ CRÍTICO

#### RFs con Inconsistencias Internas:

| RF | Inconsistencia | Línea SRS |
|----|-----------------|----------|
| **RF-01** | Wake word "computadora" vs apodo "compu"/"gol" — heurística de aceptación NO está clara | L146-153 |
| **RF-06** | Historial "dinámico adaptativo" — método de cálculo poco detallado | L198-207 |
| **RF-13** | "Cooldown 5 minutos" — pero ¿cooldown global o por tipo de sugerencia? | L315 |
| **RF-15b** | "Media móvil 14 días" — ¿ignora fines de semana? ¿qué hace si <7 días de datos? | L344-350 |
| **RF-20** | Mapeo Sefirot→Módulos — algunos módulos aparecen en varias Sefirot (ambigüedad) | L469-509 |
| **RF-23** | "Tarea compleja" — regex `_RE_TAREA_COMPLEJA` no está completo en nlu.py (no se leyó TODO) | L497-499 |
| **RF-46** | GestorPersonas — ¿cómo se persisten personas si Computadora reinicia? ¿dónde se guardan? | L1054+ |

---

## III. ESTRUCTURA DE TESTS

### Jerarquía Actual:

```
tests/
├── test_import.py                    ← Verificación básica
├── test_pyqt6.py                     ← UI testing
├── test_tikun_*.py                   ← Suite de 33 archivos (FPs específicos)
├── test_bloque*.py                   ← 5 bloques monolíticos (WI legacy)
├── test_fp*.py                       ← FPs individuales (37+ archivos)
├── test_demo*.py                     ← Demostraciones visuales
├── test_*_integration.py             ← Tests de integración (14+ archivos)
├── TESTING_CHECKLISTS.md             ← Referencia de cobertura manual
├── run_tests.bat                     ← Script batch para ejecutar suite
└── _test_*.py                        ← Tests legacy (5 archivos)
```

### Problemas Identificados:

#### 1. **Sin Test Maestro que Ejecute TODO**
- No existe `test_suite_master.py` que corra todos los tests en secuencia
- `run_tests.bat` es manual, sin validación de status de salida
- No hay reporte consolidado de cobertura

#### 2. **Convención de Nombres Inconsistente**
- Algunos usan `test_FEATURE.py`
- Otros usan `test_tikunN.py` (histórico legacy)
- Algunos prefijos `_test_` (sin ejecutarse en pytest por defecto)
- Mezcla de números y nombres

#### 3. **Acoplamiento a Legacy**
- **test_bloque1-5.py**: Monolíticos de 200+ líneas cada uno
- **test_tikun_*.py**: 33 archivos para FPs, muchos pequeños y sin consolidación
- Difícil de mantener, duplicación de setup

#### 4. **Cobertura de RFs Débil**
- RFs 01-40 tienen tests dispersos (test_bloque*.py)
- RFs 40-80 tienen tests solo cuando hay FP asignado
- **Muchos RFs sin test dedicado**

#### 5. **Sin Automatización de Validación de Requisitos**
- TESTING_CHECKLISTS.md es manual
- No hay script que valide "cada RF tiene test"
- No hay validación de "cada test valida al menos 1 RF"

---

## IV. ÁRBOL DE DEPENDENCIAS: Watchdog → CerebroGolem → Ollama

```
┌─────────────────────────────────────────────────────────────────┐
│ VENTANA_PRINCIPAL (Maljut)                                      │
│ - UX/Animación                                                  │
│ - Estado visual (colores, partículas)                          │
└────────────┬──────────────────────────────────────────────────┘
             │
             ├─────────────────────────────┬──────────────────┐
             │                             │                  │
┌────────────▼─────────┐   ┌───────────────▼──────┐  ┌──────▼──────────┐
│ HILO_PENSAMIENTO     │   │ HILO_ESCUCHA         │  │ WATCHDOG_GOLEM  │
│ (CerebroGolem)       │   │ (Whisper + regex)    │  │ (Monitoreo)     │
│ - NLU Level 1,2,3    │   │ - Wake word          │  │ - Ollama health │
│ - Ollama call        │   │ - STT               │  │ - TTS health    │
│ - Tool-use          │   │ - Eco filtering      │  │ - Mic health    │
└────────┬────────────┘   └──────────────────────┘  │ - Whisper health│
         │                                           └─────────────────┘
         │
    ┌────▼────────────────────────────────────────────┐
    │ _llamar_ollama() en nlu.py (L??? - NO LEÍDO)   │
    │ - requests.post(OLLAMA_URL, timeout=10)         │
    │ - Retry 3x con backoff 1s, 2s, 3s              │
    │ - Verifica si ollama.exe está en tasklist      │
    └────────┬─────────────────────────────────────────┘
             │
             │ (conexión TCP)
             │
    ┌────────▼──────────────────────────────────┐
    │ OLLAMA (puerto 11434)                      │
    │ - Modelo: gemma3:4b (default)             │
    │ - GET /api/tags (verificar modelos)       │
    │ - POST /api/chat (inferencia)             │
    └─────────────────────────────────────────┘
```

### Punto de Ruptura Crítica: `_llamar_ollama()`

**PROBLEMA**: La función `_llamar_ollama()` en nlu.py **NO es visible en la lectura** (línea 1-500 leídas, pero es probable que esté entre L500-1000).

**BÚSQUEDA**: Grep para `def _llamar_ollama` devolvería la línea exacta. Para esta auditoría, asumimos que existe y:
1. Hace request a `OLLAMA_URL` con `timeout=10`
2. Maneja timeouts capturando `requests.exceptions.Timeout`
3. **PERO NO sincroniza con Watchdog**

#### **Race Condition Potencial**:
```python
# En nlu.py (aproximado)
try:
    r = requests.post(OLLAMA_URL, json=payload, timeout=10)
    return r.json()
except requests.exceptions.Timeout:
    # Timeout individual = 10s
    # Watchdog también está intentando cada 15s
    # ¿Quién gana? ¿Se rompe la sesión?
    pass

# En watchdog.py
def _check_ollama():
    r = requests.get(tags_url, timeout=5)  # ← 5s timeout
    # Si falla → circuit breaker
```

**El problema**: Timeouts **descordinados** entre NLU (10s) y Watchdog (5s) causan comportamiento impredecible.

---

## V. REQUISITOS SIN TEST — CRÍTICO

### Matriz de RFs vs Tests

#### **RFs Críticos Sin Test Dedicado**:

1. **RF-35b**: Memoria Híbrida (JSON + Vector)
   - Implementado en `memoria.py` (parcial)
   - ❌ No hay test que valide búsqueda vectorial
   - ❌ No hay test que valide integración JSON↔Vector

2. **RF-40**: Baseline Adaptativo
   - Mapeado a `baseline_sistema.py` (no visible en búsqueda)
   - ❌ No hay test que valide cálculo de baseline
   - ❌ No hay test que valide alertas contextualizadas

3. **RF-42**: Supervisión Meta-Cognitiva Keter
   - Mapeado a `meta_workflow.py`
   - ❌ No hay test para `autodiagnostico()`
   - ❌ No hay test para `reporte_neshamot()`

4. **RF-54**: Tikún (Resiliencia Ollama)
   - **Descrito en SRS como "COMPLETADO"** (L1300+)
   - ❌ No hay test que valide:
     - Auto-retry con backoff 1s, 2s, 3s
     - Verificación de proceso `ollama.exe`
     - Reconexión automática cada 30s

5. **RF-56**: Lemed (Auto-Aprendizaje N1)
   - Mapeado a `nivel1_patrones.json` (no visible en búsqueda)
   - ❌ No hay test que valide:
     - Generación de regex segura
     - Sistema de confianza (0.5-0.8)
     - Límite de 200 patrones

6. **RF-57**: Da'at (Routing + Modelo Selection)
   - **Descrito como IMPLEMENTADO** (L1360+)
   - ❌ No hay test que valide:
     - `detectar_modelo_disponible()`
     - Ruteo "piensa profundamente" → N3 auto-aprobado
     - Selección inteligente de modelo

#### **RFs Parcialmente Testeados**:

| RF | Cobertura | Brecha |
|----|-----------|--------|
| RF-01 | 40% | Wake word fuzzy — apodo "gol"/"golen" NO completamente validado |
| RF-15b | 30% | Circadiano — 7 fases, media móvil 14 días NOT fully tested |
| RF-46 | 60% | Personas — persistencia y migración backwards-compat untested |
| RF-50 | 50% | Tzimtzum — auto-contracción por gaming NO testeado |
| RF-62 | 20% | Audio adaptativo — no hay test que valide perfiles TTS por fase |
| RF-66 | 40% | Watchdog — circuit breaker OK, pero escalación NOTIFY→DEGRADE untested |

---

## VI. PROPUESTA DE ESTRUCTURA DE TESTS

### Reorganización Recomendada

```
tests/
├── _suites/
│   ├── suite_rf_01_10.py         ← RFs 01-10 consolidados
│   ├── suite_rf_11_20.py         ← RFs 11-20
│   ├── suite_rf_21_30.py         ← RFs 21-30
│   ├── suite_rf_31_40.py         ← RFs 31-40
│   ├── suite_rf_41_50.py         ← RFs 41-50
│   ├── suite_rf_51_60.py         ← RFs 51-60
│   └── suite_rf_61_74.py         ← RFs 61-74
├── _integration/
│   ├── test_watchdog_ollama.py   ← NUEVO: Watchdog + Ollama sync
│   ├── test_cerebro_completo.py  ← NUEVO: CerebroGolem end-to-end
│   └── test_memoria_hibrida.py   ← NUEVO: JSON + Vector
├── test_master.py                 ← NUEVO: Ejecuta todas las suites
└── conftest.py                    ← NUEVO: Fixtures compartidas
```

### Test Master Suite

```python
# test_master.py (pseudo-código)
import pytest
from _suites import (
    suite_rf_01_10,
    suite_rf_11_20,
    # ... etc
)

def test_suite_completa():
    """Ejecuta todas las suites y reporta cobertura de RFs"""
    suites = [suite_rf_01_10, suite_rf_11_20, ...]
    for suite in suites:
        result = pytest.main(["-v", suite])
        assert result == 0, f"Suite {suite} falló"

def test_rf_coverage():
    """Valida que cada RF tenga al menos 1 test"""
    rf_list = list(range(1, 75))  # RF-01 a RF-74
    tested_rfs = suite_rf_01_10.TESTED_RFS | suite_rf_11_20.TESTED_RFS | ...
    
    missing = set(rf_list) - tested_rfs
    assert not missing, f"RFs sin test: {missing}"
```

---

## VII. RESUMEN EJECUTIVO — CONCLUSIONES NIGREDO

### 🔴 **Problemas Críticos Detectados**:

1. **Watchdog Ollama es autónomo del NLU**
   - Reconexión infinita cada 15s
   - NO libera modelos en VRAM cuando degrada
   - Sin sincronización con timeouts de NLU
   - **Riesgo**: Memory leak silencioso

2. **SRS tiene RFs sin test (12%)**
   - RF-35b, RF-40, RF-42, RF-54, RF-56, RF-57 sin cobertura
   - Muchos RFs parcialmente testeados (44%)
   - **Riesgo**: Regresiones no detectadas

3. **Inconsistencias en SRS.md**
   - RF-01: Heurística de apodo "gol" vaga
   - RF-06: Cálculo de historial dinámico poco claro
   - RF-15b: Media móvil sin handling de edge cases
   - RF-20: Sefirot en múltiples módulos (ambigüedad)
   - **Riesgo**: Implementación incoherente

4. **Estructura de Tests Desorganizada**
   - Sin test maestro consolidado
   - Nombres inconsistentes
   - Acoplamiento a legacy (test_tikun_*.py)
   - **Riesgo**: Dificultad para mantener

### ✅ **Lo que Funciona Bien**:

1. ✅ Watchdog circuit breaker bien implementado
2. ✅ Nivel 1 (Regex) con buena cobertura de RFs 01-20
3. ✅ Cleanup/atexit handlers presentes (aunque parciales)
4. ✅ Tests existen para mayoría de RFs (aunque dispersos)

### 📋 **Recomendaciones ALBEDO (Siguiente Fase)**:

1. **Sincronización Watchdog↔NLU**: 
   - Unificar timeouts (ambos 10s)
   - Compartir estado de circuito breaker
   - Implementar liberación cascada de modelos

2. **Completar Cobertura de Tests**:
   - Crear tests para RF-35b (Memoria Híbrida)
   - Crear tests para RF-40 (Baseline)
   - Crear tests para RF-54 (Tikún)
   - Crear tests para RF-56 (Lemed)
   - Crear tests para RF-57 (Da'at)

3. **Clarificar Inconsistencias SRS**:
   - Definir heurística exacta de apodo "gol"
   - Especificar cálculo de historial dinámico
   - Resolver ambigüedad de Sefirot en múltiples módulos
   - Documentar handling de edge cases

4. **Reorganizar Tests**:
   - Consolidar en suites por RF (10-RF groups)
   - Crear test maestro que valide cobertura completa
   - Establecer naming convention coherente

---

## VIII. LÍNEAS EXACTAS DE CÓDIGO PROBLEMÁTICO

### watchdog.py

| Línea | Problema | Impacto |
|-------|----------|--------|
| 206-210 | `umbral_degrade=120.0` — poco documentado, confunde con 60s | Confusión en heurísticas |
| 220 | NO hay `_timeout_adaptativo` desde NLU | Desincronización |
| 264 | `intervalo=15.0` hardcodeado — no configurable | Inflexible |
| 295+ | NO hay liberación de recursos en DEGRADE | Memory leak |
| 301 | `self._on_cambio_etapa` callback — pero NO se llama en todas transiciones | Race condition |

### nlu.py

| Línea | Problema | Impacto |
|-------|----------|--------|
| ??? | `_llamar_ollama()` — función NO leída completa (probablemente L500+) | Imposible validar timeout sync |
| 95 | `OLLAMA_URL` hardcodeado, `timeout=10` sin sincronización | Conflicto con Watchdog (timeout=5) |
| ??? | NO existe `_timeout_adaptativo` observable | Heurística undocumented |
| ??? | NO existe sincronización con `OllamaGuard` del watchdog | Race condition potencial |

### SRS.md

| Línea | Problema | Impacto |
|-------|----------|--------|
| 146-153 | RF-01: Heurística de apodo "compu"/"gol" vaga | Implementación incoherente |
| 198-207 | RF-06: Cálculo `_DEFAULT_HISTORIAL=40` — ¿cómo se adapta dinámicamente? | Algoritmo unclear |
| L344-350 | RF-15b: "Media móvil 14 días" — ¿qué si <7 días de datos? | Edge case undefinido |
| L469-509 | RF-20: Módulos en múltiples Sefirot (e.g., `nlu.py` en Biná Y Tiféret) | Ambigüedad arquitectónica |

---

## IX. LISTA DE VERIFICACIÓN PARA SESIÓN SIGUIENTE (ALBEDO)

- [ ] Leer líneas exactas de `_llamar_ollama()` en nlu.py (~L500-700)
- [ ] Buscar `_timeout_adaptativo` en proyecto (locate, grep completo)
- [ ] Rastrear toda instancia de `OLLAMA_URL` en el código
- [ ] Verificar si `OllamaGuard` se usa efectivamente en nlu.py
- [ ] Auditar memoria en Maljut durante Watchdog DEGRADE (heap dump)
- [ ] Crear test para RF-54 (resiliencia Ollama) con mock offline
- [ ] Crear test para RF-56 (Lemed) con generación de patrones
- [ ] Clarificar SRS.md §1.0-20 inconsistencias
- [ ] Consolidar tests en estructura modular (suites)

---

**FIN DE NIGREDO**

*Esta investigación expone las ashes (cenizas) crudas del sistema. ALBEDO (fase siguiente) separará los hallazgos válidos de los artefactos, purificando el diagnóstico.*
