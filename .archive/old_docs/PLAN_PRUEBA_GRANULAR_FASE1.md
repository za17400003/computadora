# PLAN DE PRUEBA GRANULAR — COMPUTADORA FASE 1
**Fecha**: Mayo 16, 2026  
**Objetivo**: Solidificar conversación antes de herramientas  
**Metodología**: Pruebas incrementales sin quebrar lo existente

---

## 📋 FASES OPERACIONALES

### FASE 0: BOOT + CONVERSACIÓN BÁSICA ✅ ACTUAL
**Objetivo**: Verificar que el sistema bootea sin errores

**Tests**:
- [x] Boot sin errores de logger
- [x] Ouroboros estable
- [x] Gilgush completa
- [x] Nombre actualizado a "Computadora"
- [ ] UI aparece sin congelamiento
- [ ] Sistema acepta input de voz/texto

**Criterios de Éxito**:
```
✓ Logs limpios (sin UnboundLocalError)
✓ Boot < 12 segundos
✓ Nombre público es "Computadora" (no Golem)
```

---

### FASE 1: CONVERSACIÓN PURA (Sin Herramientas)
**Objetivo**: Validar que responde conversacionalmente sin necesitar herramientas

**Tests a ejecutar**:

#### 1.1 — Saludos Básicos
```
Input: "Hola"
Expected: Respuesta amistosa (random desde lista saludos)
Verificar: Nivel 1 se notifica, NO intenta herramientas

Input: "Hola, Computadora" / "Computadora, ¿qué tal?"
Expected: Reconoce wake word, responde
```

#### 1.2 — Preguntas Personales
```
Input: "¿Cómo estás?" / "¿Cómo te sientes?"
Expected: Delega a Nivel 2 (Ollama) con contexto de autopercepción
Verificar: _introspeccion() ejecuta sin errores

Input: "¿En qué te basas?" / "¿Por qué dices eso?"
Expected: _autorreflexion() proporciona justificación con datos
```

#### 1.3 — Autopresentación
```
Input: "Preséntate" / "¿Quién eres?"
Expected: Narrativa coherente sobre identidad (actualizada a Computadora)
Verificar: Menciona nombre "Computadora", no "Golem"

Input: "¿Cuáles son tus límites éticos?"
Expected: Describe 5 leyes y restricciones
```

#### 1.4 — Intención Conversacional (Tria Prima)
```
Input: "por favor"
Expected: Invita a pedir (Sal)

Input: "gracias"
Expected: Cierre conversacional (Mercurio)

Input: "amén, amén, amén."
Expected: Invoca meta-análisis (Azufre)
```

#### 1.5 — Memoria Conversacional
```
Input: "¿qué recuerdas de hoy?"
Expected: Obtiene historial de hoy sin errores
Verificar: Busca en memoria.py correctamente

Input: "olvida a X" / "recuerda que..."
Expected: Gestiona personas sin errores
```

**Criterios de Éxito**:
```
✓ 100% de pruebas 1.1-1.5 pasen
✓ NO se ejecuten herramientas (retornen None)
✓ Todos los logs sean INFO/DEBUG (no ERROR)
✓ Conversación se sienta natural
```

---

### FASE 2: HERRAMIENTAS BÁSICAS (Después de Fase 1 OK)
**Objetivo**: Activar herramientas que NO requieren permisos/hardware

**Grupo A — Herramientas Información**:
- obtener_fecha_hora
- leer_portapapeles
- contexto_pantalla (qué app está activa)
- monitoreo_sistema (CPU, RAM, disco)

**Grupo B — Herramientas Control**:
- controlar_volumen (subir/bajar/mute)
- abrir_aplicacion / cerrar_aplicacion
- ejecutar_comando (comandos seguros)

**Tests**:
```
Input: "¿Qué hora es?"
Expected: Ejecuta obtener_fecha_hora, retorna hora

Input: "¿Cómo está mi PC?"
Expected: Ejecuta monitoreo_sistema, retorna estado

Input: "Sube el volumen" / "Baja el volumen"
Expected: Ejecuta controlar_volumen, ajusta

Input: "Abre Chrome"
Expected: Ejecuta abrir_aplicacion("Chrome")
```

**Criterios de Éxito**:
```
✓ Las 4 herramientas A se ejecutan sin errores
✓ Las 4 herramientas B se ejecutan sin errores
✓ Respuestas son contextuales (no genéricas)
✓ Ninguna herramienta quebranta privacidad/seguridad
```

---

### FASE 3: HERRAMIENTAS AVANZADAS (Después de Fase 2 OK)
**Objetivo**: Activar herramientas que requieren permisos/APIs

**Grupo C — Internet/APIs**:
- buscar_en_internet
- abrir_sitio_web
- buscar_en_plataforma (YouTube, GitHub, etc)

**Grupo D — Archivos**:
- leer_archivo (read-only)
- escribir_archivo (con confirmación)
- listar_directorio

**Tests**:
```
Input: "Busca en Google qué es una sinfonía"
Expected: Ejecuta buscar_en_internet, retorna resumen

Input: "Abre github.com/usuario/repo"
Expected: Abre en navegador

Input: "Lee el archivo config.json"
Expected: Muestra contenido (si está en ruta permitida)
```

**Criterios de Éxito**:
```
✓ APIs funcionan sin timeouts
✓ Archivos se acceden en rutas permitidas
✓ Sin acceso a archivos sensibles
✓ Rate limiting respetado
```

---

### FASE 4: VISIÓN + RECONOCIMIENTO (FASE POSTERIOR)
**Objetivo**: Activar cámara y face recognition

**PENDIENTE**: No se ejecuta hasta que Fases 1-3 pasen 100%

---

## 🔄 CICLO DE VALIDACIÓN

### Paso 1: Pre-Test
```bash
# Verificar cambios de código
git diff

# Ejecutar linter
python -m pylint computadora/cerebro/nlu.py --disable=all --enable=E,F

# Ejecutar tests existentes
pytest tests/ -v --tb=short
```

### Paso 2: Boot Test
```bash
# Verificar boot sin errores
python -m computadora 2>&1 | grep -E "(ERROR|Exception|Traceback)"

# Medir tiempo de boot
time python -m computadora
```

### Paso 3: Conversación Manual
```bash
# Ejecutar script de prueba
python tests/test_conversation_live.py

# O interactivo:
python -c "
from computadora.cerebro.nlu import CerebroGolem
cerebro = CerebroGolem()
respuesta = cerebro.pensar('Hola, ¿cómo estás?')
print(respuesta)
"
```

### Paso 4: Validación de Herramientas
```bash
# Ver qué herramientas se ejecutaron
grep "ejecutar_herramienta\|ejecutada" logs_live.txt

# Verificar NO se ejecutan en Fase 1
grep "None\|__TOOL__" respuestas.log  # Debería devolver None
```

---

## 📊 CHECKLIST PROGRESIVO

### FASE 0 (AHORA)
- [x] Boot sin UnboundLocalError
- [x] Nombre actualizado a "Computadora"
- [ ] UI se muestra sin congelamiento
- [ ] Sistema escucha entrada de voz/texto

### FASE 1 (PRÓXIMA)
- [ ] Test 1.1: Saludos básicos ✓
- [ ] Test 1.2: Preguntas personales ✓
- [ ] Test 1.3: Autopresentación ✓
- [ ] Test 1.4: Tria Prima ✓
- [ ] Test 1.5: Memoria ✓

### FASE 2 (SI 1 PASA)
- [ ] Información: hora, portapapeles, contexto ✓
- [ ] Control: volumen, aplicaciones ✓
- [ ] Validar sin quebrar Fase 1

### FASE 3 (SI 2 PASA)
- [ ] Internet: búsqueda, sitios, plataformas ✓
- [ ] Archivos: lectura, escritura, listado ✓
- [ ] Validar sin quebrar Fases 1-2

### FASE 4 (POSTERIOR)
- [ ] Visión: cámara operativa
- [ ] Reconocimiento: face_recognition funciona

---

## ⚙️ PATRONES DE ESTABILIDAD

### Anti-Colateral
```
✓ Cada Test aislado (no depende de anteriores)
✓ Rollback automático si falla (git checkout)
✓ Snapshots ANTES de cambios
✓ Commits atómicos por Fase
```

### Mediciones
```
Métrica: Tiempo respuesta promedio por nivel
- Nivel 1: < 200ms (regex patterns)
- Nivel 2: 1-5s (Ollama local)
- Nivel 3: 5-15s (Copilot + red)

Métrica: Tasa de errores
- Inicial: < 5% (errores de desarrollo)
- Target: < 0.5% (producción)
```

---

## 📝 NOTAS DE IMPLEMENTACIÓN

### Si Fase X Falla
1. **Git restore**: `git checkout computadora/cerebro/nlu.py`
2. **Diagnosticar**: Ver logs exactos del error
3. **NIGREDO**: Análisis exhaustivo del problema
4. **Corregir**: Fix mínimo sin cambios colaterales
5. **Retry Fase**: Ejecutar de nuevo

### Commit Strategy
```
FASE 0 FIX: Logger error + nombre actualizado
FASE 1 TEST: Validar conversación pura (sin herramientas)
FASE 2 TEST: Activar herramientas básicas
... etc
```

### Performance Baselines
- Boot: 11-13s (acceptable después lazy-loading)
- Respuesta N1: < 500ms
- Respuesta N2: 2-6s
- CPU idle: < 5%
- RAM: < 250MB

---

## 🎯 PRÓXIMA ACCIÓN

**Ejecutar Fase 0 + 1 Validation**:
```bash
cd proyecto-golem
python -m computadora 2>&1 | tee boot_phase0.log
# Verificar: sin errores, Computadora en logs
# Luego: test conversación manual
```

Si todo OK → Commit Fase 0  
Si falla → NIGREDO diagnosis

---

*Solid Foundation First. Features After Stability.*
