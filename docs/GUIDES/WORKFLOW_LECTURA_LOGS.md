# Workflow de Logs — Cómo Leer + Estructura de Archivos (Junio 1, 2026)

## 📋 ¿Cómo Funciona el Logging?

### Estructura de Archivos

```
datos/logs/
├─ computadora_2026-06-01.log ← Archivo actual (JUNIO 1)
├─ computadora_2026-05-31.log ← Ayer
├─ computadora_2026-05-30.log ← Hace 2 días
├─ ... (hasta 7 días atrás)
└─ [Más antiguos se eliminan automáticamente]
```

### 🔑 Punto Clave: Un Archivo POR DÍA

**Pregunta**: "¿Se reescribe el log cada vez que inicio Computadora?"  
**Respuesta**: **NO**. Se ANEXA (append) líneas nuevas.

**Ejemplo**: Si hoy (2026-06-01) inicias Computadora 3 veces:

```
Boot #1 @ 09:00
[líneas de boot 1]

Boot #2 @ 13:00
[líneas de boot 2]

Boot #3 @ 18:00
[líneas de boot 3]
← TODO en el MISMO archivo (computadora_2026-06-01.log)
```

**Mañana** (2026-06-02): Se crea un archivo NUEVO, no interfiere con hoy.

---

## 🎯 Workflow Correcto para Leer Logs

### ❌ INCORRECTO (Lectura secuencial)

```bash
# Leer desde el inicio del archivo
head -100 datos/logs/computadora_2026-06-01.log
# ← Vés los primeros eventos, pero el PROBLEMA está al final
# ← Contexto confuso
```

### ✅ CORRECTO (Lectura desde el final)

```bash
# 1. Ver las ÚLTIMAS líneas primero (lo más importante)
tail -150 datos/logs/computadora_2026-06-01.log

# 2. Identificar: ¿Dónde se detiene? ¿Dónde está el error?

# 3. LUEGO leer hacia atrás para entender el contexto
# (grep para encontrar el inicio del boot actual)
grep -n "Sistema de logs inicializado" datos/logs/computadora_2026-06-01.log
# ← Esto te dice en qué línea comenzó el boot

# 4. Leer desde esa línea hacia el error
```

---

## 🧪 Ejemplo Práctico (WI-BERESHIT-DEADLOCK-FIX)

### Cómo Detecté el Problema

```bash
# 1. Leer última parte del log (donde pasó lo grave)
tail -150 datos/logs/computadora_2026-06-01.log
```

**Output** (últimas líneas):
```
09:15:53 | INFO | Silero VAD cargado correctamente (lazy-init)
09:15:55 | INFO | Cargando modelo Whisper en cuda:0...
09:15:55 | INFO | Inscribiendo la Palabra en cuda:0... modelo 'small'
[SILENCIO — nada más]
```

**Conclusión inmediata**: Whisper se cargaba y bloqueaba. ✅

### Si Hubiera Leído Desde el Inicio

```bash
head -100 datos/logs/computadora_2026-06-01.log
```

**Output**:
```
09:15:30 | INFO | Ouroboros estable...
09:15:31 | INFO | Backend de TTS inicializado...
09:15:32 | INFO | Backend de NLU inicializado...
...
[100 líneas de setup normal]
```

**Conclusión**: ¿Dónde está el problema? 🤔  
**Tiempo perdido**: 10+ minutos buscando "qué salió mal"

---

## 📊 Rotación de Logs

### Cuándo se Rota un Archivo

```python
# En computadora/utilidades/logs.py:
logger.add(
    archivo_log,
    rotation="10 MB",      # ← Rota si archivo > 10 MB
    retention="7 days",    # ← Borra si > 7 días
    ...
)
```

**Scenario**: Hoy (2026-06-01), Computadora ha escrito 15 MB

```
datos/logs/
├─ computadora_2026-06-01.log     (10 MB)
└─ computadora_2026-06-01.1.log   (5 MB) ← Rotado
```

**Ambos son del MISMO DÍA** (solo rotados por tamaño).

Para leer todo de hoy:
```bash
cat datos/logs/computadora_2026-06-01*.log | tail -200
```

---

## 🛠️ Herramientas Útiles

### Para Encontrar el Inicio del Boot Actual

```bash
# ¿En qué línea empezó el último boot?
grep -n "Sistema de logs inicializado" datos/logs/computadora_2026-06-01.log | tail -1

# Output: 1542:Sistema de logs inicializado
# ↑ Línea 1542 fue donde empezó el último boot
```

### Ver Solo el Último Boot

```bash
# Combinar: desde línea N hasta el final
BOOT_LINE=$(grep -n "Sistema de logs inicializado" datos/logs/computadora_2026-06-01.log | tail -1 | cut -d: -f1)
tail -n +$BOOT_LINE datos/logs/computadora_2026-06-01.log
```

### Ver Boot #N (si hay múltiples)

```bash
# Ver TODOS los inicios de boot de hoy
grep -n "Sistema de logs inicializado" datos/logs/computadora_2026-06-01.log

# Output:
# 1:Sistema de logs inicializado        ← Boot #1 @ línea 1
# 523:Sistema de logs inicializado      ← Boot #2 @ línea 523
# 1542:Sistema de logs inicializado     ← Boot #3 @ línea 1542

# Leer solo Boot #2 (líneas 523-1541)
sed -n '523,1541p' datos/logs/computadora_2026-06-01.log
```

---

## 📝 Workflow Estándar a Partir de Ahora

**Cuando haya problemas**:

1. **Ir a `datos/logs/computadora_[HOY].log`**
2. **Leer últimas 100-200 líneas** (`tail -200`)
3. **Identificar punto de fallo** (¿dónde se detiene? ¿dónde está el error?)
4. **Encontrar línea de inicio del boot** (`grep "Sistema de logs inicializado"`)
5. **Leer desde línea de inicio → línea de fallo** (contexto completo)
6. **Hacer hipótesis + verificar código**

**Tiempo típico**: 2-5 minutos vs. 20+ minutos leyendo desde el inicio.

---

## 💡 Por Qué Funciona Este Workflow

**Principio**: Los últimos eventos son los más relevantes para diagnosticar.

- ✅ Si UI no aparece → últimas líneas dicen por qué
- ✅ Si error → stack trace está al final
- ✅ Si deadlock → línea donde se "congela" está al final
- ✅ Si éxito → último evento es "✅ Sistema listo"

**Contexto histórico**: Solo se necesita si último evento es ambiguo (ej: "Cargando X...").

---

## 🎓 Aplicación en WI-BERESHIT-DEADLOCK-FIX

**Logs leídos**: 
- ❌ Primero 100 líneas = setup normal
- ✅ Últimas 10 líneas = reveló Whisper bloqueando
- Tiempo de diagnóstico: ~2 minutos

**Sin este workflow**:
- Leer 1500+ líneas desde el inicio
- Esperar 20+ minutos para llegar al final
- Tempo lento, diagnóstico lento

---

## 📌 Memorizar Este Workflow

```
RULE #1: Logs → TAIL (final) primero
RULE #2: 1 archivo por día
RULE #3: Múltiples boots = MISMO archivo (append)
RULE #4: Rotation solo por tamaño (>10MB), no por boot
RULE #5: Grep "Sistema de logs" para encontrar inicio de cada boot
```

---

**FIN WORKFLOW**: Este proceso será estándar a partir de ahora para todos los diagnósticos.
