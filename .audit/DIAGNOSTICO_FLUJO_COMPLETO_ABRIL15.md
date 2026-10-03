# 🔍 DIAGNÓSTICO COMPLETO DEL FLUJO: Desktop Shortcut → Sistema
**Fecha**: Abril 15, 2026 | **Estado**: 🔴 CRÍTICO — **PROBLEMA FUNDAMENTAL IDENTIFICADO**

---

## 📍 PUNTO DE INICIO: Desktop Shortcut

### **Shortcut Identificado**
- **Nombre**: `COMPUTADORA.lnk`
- **Apunta a**: `.config/iniciar_computadora.bat`
- **Ubicación**: `C:\Users\woire\Documents\proyecto-golem\.config\iniciar_computadora.bat`

---

## 🚨 PROBLEMA CRÍTICO #1: .BAT File Intenta Ejecutar Archivo Fantasma

**En `.config/iniciar_computadora.bat` línea final**:
```batch
.venv\Scripts\python.exe computadora/core/main.py 2>&1
```

**PROBLEMA**: `computadora/core/main.py` **NO EXISTE** ❌

**Archivos reales** en computadora/:
- ✅ `computadora/__init__.py`
- ✅ `computadora/__main__.py`
- ❌ `computadora/core/` (carpeta NO existe)
- ❌ `computadora/core/main.py` (archivo NO existe)

**Consecuencia**: When user clicks shortcut → .bat tries to execute non-existent file → CRASH

---

## ✅ PUNTO DE ENTRADA CORRECTO

La entrada DEBERÍA ser:
```batch
.venv\Scripts\python.exe -m computadora
```

O alternativamente (si no funciona `-m`):
```batch
.venv\Scripts\python.exe computadora/__main__.py
```

---

## 🔴 PROBLEMA CRÍTICO #2: Mezcla de Referencias "GOLEM" en `__main__.py`

Si el .bat se arreglase, ejecutaría `computadora/__main__.py` que tiene MÚLTIPLES líneas con "Golem":

### **Referencias a "Golem" (Debería ser "Computadora")**

| Línea | Contenido | Tipo | Severidad |
|-------|----------|------|-----------|
| 13 | `def _kill_previous_golem_instances()` | Nombre función | 🔴 ALTA |
| 14 | Docstring: "Termina instancias previas de Golem" | Docstring | 🟡 MEDIA |
| 18 | `'-m golem'` (comentario) | Búsqueda pattern | 🔴 ALTA |
| 48 | `if '-m' in cmdline and 'golem' in cmdline:` | Lógica | 🔴 ALTA |
| 68 | `logger.info(f"Terminé instancias previas de Golem:` | Log | 🟡 MEDIA |
| 71 | `print(f"Terminé instancias previas de Golem:` | Fallback | 🟡 MEDIA |
| 84 | `"✓ Ouroboros estable: Ciclo infinito del Golem"` | Log | 🟡 MEDIA |
| 115 | `logger.info("=== GOLEM INICIANDO ===")` | Log | 🟡 MEDIA |
| 136 | `# RF-260 Ayin HaGolem:` | Comentario | 🟡 MEDIA |
| 145 | `# un solo CerebroGolem para todos los canales` | Comentario | 🟡 MEDIA |
| 146 | `from computadora.cerebro.nlu import CerebroGolem` | **Import clase** | 🔴 ALTA |
| 262 | `logger.info("=== GOLEM FINALIZADO ===")` | Log | 🟡 MEDIA |

---

## 🔴 PROBLEMA CRÍTICO #3: Clases NO Renombradas

Las siguientes clases aún dicen "GOLEM" en lugar de "COMPUTADORA":

### **Clases Que Debería Estar Renombradas**

| Archivo | Clase Actual | Debería Ser | Severidad |
|---------|--------------|-------------|-----------|
| `cerebro/nlu.py` | `class CerebroGolem:` | `CerebroComputadora` | 🔴 ALTA |
| `interfaz/ventana_principal.py` | `class OrbeGolem(QWidget):` | `OrbeComputadora` | 🔴 ALTA |

**Impacto**: Cualquier código que importa estas clases tendrá nombres inconsistentes. El proyecto internamente sigue siendo "Golem".

---

## 📋 FLUJO ACTUAL (CON PROBLEMAS IDENTIFICADOS)

```
Usuario presiona: COMPUTADORA.lnk
    ↓
1. .bat ejecuta: .venv\Scripts\python.exe computadora/core/main.py
    ↓
   ❌ ERROR: computadora/core/main.py NO EXISTE
    ↓
   CRASH - Mensaje de error: "No module named 'computadora.core.main'"
    ↓
   [SI se arreglase el .bat y ejecutase __main__.py]
    ↓
2. __main__.py carga:
   - ❌ Función: _kill_previous_golem_instances() busca "-m golem"
   - ❌ Log: "=== GOLEM INICIANDO ===" 
   - ❌ Import: CerebroGolem (clase aún tiene nombre "Golem")
   - ❌ Múltiples comentarios/logs con "Golem" en lugar de "Computadora"
    ↓
3. Se crea: cerebro_compartido = CerebroGolem() ← Clase aún se llama "Golem"
    ↓
4. Se instancia: OrbeGolem (ventana principal) ← Clase aún se llama "Golem"
    ↓
5. Logs de boot muestran mensajes mezclados:
   - "✓ Ouroboros estable: Ciclo infinito del Golem ← MENSAJES "GOLEM"
   - "=== GOLEM INICIANDO ===" ← DEBERÍA SER "COMPUTADORA"
   - "Ciclo infinito del Golem" ← DEBERÍA SER "COMPUTADORA"
```

---

## 📊 RESUMEN DE ITEMS MEZCLADOS ENCONTRADOS

**Total de referencias "golem/Golem" encontradas en computadora/**: **100+ coincidencias**

### **Distribución por tipo:**

| Categoría | Cantidad | Ejemplos |
|-----------|----------|----------|
| **Clases (NO renombradas)** | 2 | CerebroGolem, OrbeGolem |
| **Función names** | 5+ | `_kill_previous_golem_instances`, `_estado_golem`, etc |
| **Búsquedas de procesos** | 3 | `'-m golem'`, `'golem' in cmdline` |
| **Logs/mensajes usuario** | 20+ | "GOLEM INICIANDO", "Ciclo del Golem", etc |
| **Comentarios técnicos** | 30+ | "Ayin HaGolem", "CerebroGolem para todos", etc |
| **Variables/configuración** | 10+ | `ram_golem_mb`, servicios mDNS `_golem._tcp` |
| **Imports incorrectos** | 2 | `from golem import __version__` en servidor_api.py |
| **Firestore collections** | 5+ | `db.collection("golem")` en lugar de "computadora" |
| **Docstrings/descripciones** | 20+ | "Configuración global de Golem", "Estado del Golem", etc |

---

## 🎯 PROBLEMAS ESPECÍFICOS POR MÓDULO

### **`__main__.py`** - CRÍTICO
- 🔴 Función busca `'-m golem'` pero proyecto es ahora `python -m computadora`
- 🔴 Logs dicen "GOLEM" en lugar de "COMPUTADORA"
- 🔴 Importa `CerebroGolem` (clase no renombrada)
- 🔴 Llama a `_kill_previous_golem_instances()` que busca proceso antiguo

### **`cerebro/nlu.py`** - CRÍTICO
- 🔴 `class CerebroGolem:` ← Nombre de clase no actualizado

### **`interfaz/ventana_principal.py`** - CRÍTICO
- 🔴 `class OrbeGolem(QWidget):` ← Nombre de clase no actualizado
- 🔴 Todos los logs internos hablan de "Golem"

### **`canales/servidor_api.py`** - IMPORTANTE
- 🔴 Línea 166: `from golem import __version__` ← Import incorrecto
- 🔴 Línea 162: `hw["ram_golem_mb"]` ← Variable aún dice "golem"
- 🔴 Línea 674-675: mDNS registra `_golem._tcp`
- 🔴 Líneas 742, 761, 799: Firestore collection es "golem" no "computadora"

### **`canales/discord_brain.py`, `telegram_brain.py`** - IMPORTANTE
- 🔴 Múltiples referencias a "→ Golem" en logsjugador
- 🔴 Prefijo Discord: `"golem "` ← Debería ser algo más genérico

### **`cerebro/flujos_guardian.py`** - IMPORTANTE
- 🔴 Logger: `logging.getLogger("golem_shim")` ← Debería actualizar namespace
- 🔴 Parámetros: `cerebro: CerebroGolem` ← Nombre clase antiguo

### **`cerebro/bina_pnimit.py`** - IMPORTANTE
- 🔴 `class DiagnosticoGolem:` ← Nombre clase aún tiene "Golem"
- 🔴 Búsqueda: `if "golem" in m for m in sys.modules`

---

## 🔧 ACCIONES NECESARIAS PARA CORREGIR

### **PRIORIDAD 1 - CRÍTICA** (El sistema no arranca sin estas):
1. ✅ **Actualizar `.config/iniciar_computadora.bat`** línea final:
   - Cambiar: `computadora/core/main.py`
   - A: `-m computadora`

2. ✅ **Renombrar clases en `__main__.py`**:
   - `_kill_previous_golem_instances()` → `_kill_previous_computadora_instances()`
   - Dentro: cambiar `'-m golem'` → `'-m computadora'`
   - Dentro: cambiar búsqueda `'golem' in cmdline` → `'computadora' in cmdline`

3. ✅ **Renombrar clases principales**:
   - `cerebro/nlu.py: class CerebroGolem:` → `class CerebroComputadora:`
   - `interfaz/ventana_principal.py: class OrbeGolem(QWidget):` → `class OrbeComputadora(QWidget):`

### **PRIORIDAD 2 - ALTA** (El sistema funciona pero tiene confusión):
4. ✅ Actualizar todos los imports de `CerebroGolem` → `CerebroComputadora`
5. ✅ Actualizar todos los imports de `OrbeGolem` → `OrbeComputadora`
6. ✅ Actualizar logs en `__main__.py`:
   - `"=== GOLEM INICIANDO ===" ` → `"=== COMPUTADORA INICIANDO ==="`
   - `"=== GOLEM FINALIZADO ===" ` → `"=== COMPUTADORA FINALIZADO ==="`
   - `"Ciclo infinito del Golem"` → `"Ciclo infinito de COMPUTADORA"`

### **PRIORIDAD 3 - MEDIA** (Polish, no bloquea):
7. ✅ Actualizar `canales/servidor_api.py`:
   - Línea 166: `from golem import __version__` → `from computadora import __version__`
   - Línea 162: `hw["ram_golem_mb"]` → `hw["ram_computadora_mb"]`
   - Línea 674-675: mDNS `_golem._tcp` → `_computadora._tcp`
   - Firestore collections: `"golem"` →`"computadora"`

8. ✅ Actualizar nombres en canales (Discord, Telegram, etc):
   - Namespace logger: `"golem_shim"` → `"computadora_app"`
   - Prefijos Discord: `"golem "` → algo más genérico

---

## 📸 FLUJO CORRECTO (Cómo DEBERÍA funcionar)

```
Usuario presiona: COMPUTADORA.lnk
    ↓
1. .bat ejecuta: .venv\Scripts\python.exe -m computadora
    ↓
2. __main__.py (punto de entrada) carga:
   - ✅ Función: _kill_previous_computadora_instances() busca "-m computadora"
   - ✅ Log: "=== COMPUTADORA INICIANDO ===" 
   - ✅ Import: CerebroComputadora (clase renombrada)
   - ✅ Todos los logs limpios con "COMPUTADORA"
    ↓
3. Se crea: cerebro_compartido = CerebroComputadora()
    ↓
4. Se instancia: OrbeComputadora (ventana principal)
    ↓
5. Boots completo sin confusión de nombres:
   - "✓ Ouroboros estable: Ciclo infinito de la COMPUTADORA"
   - "=== COMPUTADORA INICIANDO ===" ✅
   - Todos los logs internos: COMPUTADORA
   - API funciona correctamente sin confusiones
```

---

## ✅ VERIFICACIONES RECOMENDADAS

Después de aplicar todas las correcciones, ejecutar:

```bash
# 1. Verificar sintaxis
python -m py_compile computadora/**/*.py

# 2. Verificar imports
python -c "from computadora.cerebro.nlu import CerebroComputadora; print('OK')"
python -c "from computadora.interfaz.ventana_principal import OrbeComputadora; print('OK')"

# 3. Boot test
python -m computadora  [Primeras 50 líneas de logs]

# 4. Verificar NO hay referencias "golem" en código python
grep -r "from golem\|import golem\|CerebroGolem\|OrbeGolem" computadora --include="*.py" | head -20
```

---

## 🎯 CONCLUSIÓN

**Estado Actual**: 🔴 **CRÍTICO**
- El shortcut NO FUNCIONA (archivo fantasma)
- Las clases NO ESTÁN RENOMBRADAS
- Hay 100+ referencias "golem" esparcidas por el código
- El proyecto funciona internamente bajo el nombre "Golem" aunque la carpeta se llama "computadora"

**Action Plan**: Aplicar las correcciones PRIORIDAD 1-3 en ese orden para lograr coherencia total.

**Tiempo estimado**: 30-45 minutos para correcciones exhaustivas.

---

**Diagnostic Report Generated**: April 15, 2026 - 12:15 UTC
