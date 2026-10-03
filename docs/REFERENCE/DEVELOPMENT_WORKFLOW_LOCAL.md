# DEVELOPMENT_WORKFLOW_LOCAL.md — Optimizado para Ollama Local

> **Para**: Modelo local Ollama llama3.1:8b / Continue VS Code
> **Fecha**: Mayo 2, 2026
> **Propósito**: Guía compacta, token-eficiente para asistentes de código local
> **Nota**: Esta es la versión LOCAL. Para GitHub Copilot/Claude Haiku, ver `DEVELOPMENT_WORKFLOW_REFERENCIA.md`

---

## 🚀 BOOTSTRAP LOCAL (Lee esto PRIMERO)

**Orden de consulta**:
1. 🗺️  **INDEX.md** — Hub central con TODO (arquitectura, guías, especificaciones)
2. 🎉 Este archivo — Instrucciones compactas para Ollama local
3. 📋 `DEVELOPMENT_WORKFLOW_REFERENCIA.md` — Para consultas complejas

**Proyecto**: `Proyecto COMPUTADORA` — Asistente personal de escritorio con IA
2. Lenguaje: Python 3.10+
3. Estructura: `/computadora` (código), `/docs` (docs), `/scripts` (herramientas), `/tests` (tests)
4. Rama principal: `main`

---

## ⚡ CICLO RÁPIDO (Optimizado para modelos <10B tokens)

### Fase 0: CODEGRAPH (SIEMPRE PRIMERO)
- Si buscas un símbolo/módulo: **usa CodeGraph primero** (60-70% más eficiente)
- Evita búsquedas manuales sin contexto
- Query: `CODEGRAPH_QUERY.py Symbol` o busca en `codegraph_report.json`
- Ahorra ~500 tokens vs. búsquedas ciegas

### Fase 1: ENTRADA (Comprende qué pides)
- Lee la descripción breve (max 200 tokens)
- Identifica: ¿Es bug, feature, refactor o doc?
- Si es muy complejo → divide en 2-3 tareas menores

### Fase 2: DIAGNÓSTICO (¿Qué archivos tocar?)
- **Usa CodeGraph** si no conoces la estructura (paso 0)
- Busca archivos clave (max 3-5 archivos)
- Lee solo las primeras 100-200 líneas
- Identifica el patrón existente
- **NO leas todo el proyecto** — ahorra tokens

### Fase 3: SOLUCIÓN (Implementa rápido)
- **REGLA NUEVA**: Antes de crear archivo → PRE-determinar ubicación
  ```python
  from scripts.FILE_LOCATION_MANAGER import FileLocationManager
  location = FileLocationManager.get_location('mi_archivo.py')  # → 'scripts/diagnostics'
  FileLocationManager.create_file('mi_archivo.py', contenido)
  ```
- Escribe código que siga el patrón local
- Tests inline: valida con assertions simples
- Uno o dos cambios por commit, no más
- Mensaje de commit claro (max 1 línea)

### Fase 4: VERIFICACIÓN ⚠️ **OBLIGATORIA** (Valida)
- **NUNCA saltes esta fase** — skipping causa cascadas de errores
- Ejecuta `pytest tests/` si hay tests
- Si no hay tests → ejecuta el código manualmente
- Busca errores de sintaxis obvios
- Verifica que cambios actuales no rompan commits previos
- Si pasa → procede. Si no → diagnostica en Fase 2

### Fase 5: DOCUMENTO (Registra)
- Comenta el cambio en el código
- Si es feature → añade docstring
- Si es bug → añade síntoma + solución en comentario
- Actualiza WorkItems.md si es WI-*
- Commit: una línea clara describiendo qué se validó en Fase 4

---

## 🎯 REGLAS RÁPIDAS

| Qué | Cómo |
|---|---|
| **Bug** | Lee archivo afectado → identifica línea → corrige → test → commit |
| **Feature** | Crea archivo nuevo en directorio correcto → sigue patrón local → test → commit |
| **Refactor** | Agrupa 3-5 cambios relacionados → mantén tests verdes → 1 commit atómico |
| **Doc** | Actualiza inline o crea `docs/TEMA.md` → Link desde README |
| **Test** | Crea en `/tests/` con nombre `test_*.py` → run `pytest` → verde |

---

## 📁 ESTRUCTURA (Todo lo que necesitas saber)

```
proyecto-golem/
├── computadora/          ← Código principal
│   ├── cerebro/          ← NLU, modelos, reasoning
│   ├── interfaz/         ← PyQt6 GUI
│   ├── voz/              ← Audio, TTS
│   ├── habilidades/      ← Tools, herramientas
│   └── nucleo/           ← Eventos, arquitectura base
├── scripts/              ← Utilidades, automatización
├── tests/                ← Tests unitarios + docs de testing
├── docs/                 ← Documentación completa
├── datos/                ← Datos y transcripciones
├── _config/              ← config.json, requirements.txt
├── _archive/             ← Archivos obsoletos
├── .logs/                ← Logs del sistema
├── WorkItems.md          ← Tareas pendientes
├── iniciar computadora.bat ← Launcher principal
└── README.md
```

**Regla de oro**: Si creas archivo → va en `/scripts`, `/tests`, `/docs`, o `/computadora/<modulo>/`. Nunca en raíz.

---

## 🧠 PATRONES LOCALES (Imita estos)

### Patrón 1: Herramienta simple
```python
# En computadora/habilidades/
def mi_herramienta(parametro: str) -> str:
    """Breve descripción."""
    resultado = ...
    logger.info(f"Resultado: {resultado}")
    return resultado
```

### Patrón 2: Clase con estado
```python
# En computadora/nucleo/
class MiClase:
    def __init__(self, config: dict):
        self.config = config
        self.estado = None
    
    def procesaр(self, datos: str) -> dict:
        """Procesa datos y retorna dict con resultado."""
        ...
        return {"status": "ok", "resultado": ...}
```

### Patrón 3: Test
```python
# En tests/test_mi_feature.py
import pytest
from computadora.mi_modulo import mi_funcion

def test_caso_basico():
    resultado = mi_funcion("entrada")
    assert resultado == "esperado"
```

---

## ⏱️ TOKEN BUDGET POR FASE (¡No excedas!)

- **Entrada**: 100-200 tokens (tu pregunta)
- **Diagnóstico**: 300-500 tokens (lectura de archivos)
- **Solución**: 500-800 tokens (código nuevo)
- **Verificación**: 100-200 tokens (test + error check)
- **Documento**: 50-100 tokens (comentario/docstring)
- **TOTAL**: ~1500-2000 tokens por tarea

**Si excedes 2000** → divide la tarea en 2 más pequeñas.

---

## 🔍 DIAGNÓSTICO RÁPIDO (Checklist)

Antes de actuar, responde:

- [ ] ¿Qué archivo(s) necesito leer? (máximo 5)
- [ ] ¿Cuál es el patrón existente? (copia, no inventes)
- [ ] ¿Es bug/feature/refactor? (clasifica)
- [ ] ¿Cuántos archivos voy a cambiar? (máximo 3-5)
- [ ] ¿Necesito tests nuevos? (si cambio lógica → sí)

---

## 🚀 CODEGRAPH — EXPLORACIÓN SIN TOOL CALLS (Mayo 18, 2026)

**Integración**: Copilot ahora usa CodeGraph para 60-70% menos tool calls.

### Setup (Una sola vez)
```bash
pip install codegraph
python CODEGRAPH_ANALYZER.py  # Genera codegraph_report.json
```

### Protocolo (SIEMPRE)
1. Búsqueda de código → `python CODEGRAPH_QUERY.py --class/--function/--module X`
2. Si encontrada → respuesta instantánea (<100ms)
3. Si no → fallback a `grep_search` / `file_search`

### Prioridad de Herramientas
1. **CodeGraph** — búsquedas por clase/función/módulo
2. **grep_search** — regex complejas
3. **file_search** — búsquedas por nombre
4. **read_file** — leer contenido después de localizar

**Referencia**: `COPILOT_CODEGRAPH_INTEGRATION.md` (documentación completa), `/memories/CODEGRAPH_ALWAYS_USE.md` (recordatorio permanente)

---

## 🚨 ERRORES COMUNES (Evítalos)

| Error | Por qué es malo | Solución |
|---|---|---|
| Leer el proyecto completo | Desperdicia 500+ tokens | Lee solo archivos afectados |
| Cambiar 10+ archivos a la vez | Confunde el contexto | 3-5 archivos máximo por cambio |
| No hacer test después | Código roto sin saberlo | Siempre test verde |
| Crear archivos en raíz | Contamina estructura | Usa directorios existentes |
| Resumen innecesario al final | Desperdicia tokens | Sé conciso, no resumas |

---

## ✅ LISTA DE CHEQUEO FINAL

Antes de decir "DONE":

- [ ] El código compila/corre sin errores
- [ ] Los tests pasan (si hay tests)
- [ ] Seguí patrón local existente
- [ ] Archivos en lugar correcto
- [ ] Commit mensaje claro
- [ ] Documenté el cambio (comentario/docstring)

---

## 💡 CONSEJOS PARA OLLAMA LOCAL

1. **Sé explícito**: "Cambia línea 45 en `cerebro/nlu.py` de `X` a `Y`" → mejor que "mejora el NLU"
2. **Proporciona contexto**: Pega el código relevante (10-20 líneas) antes de pedir cambio
3. **Un cambio = un commit**: No mezcles features
4. **Tests primero** (opcional): Si proporciones test → el modelo lo entiende mejor
5. **Si se traba**: Simplifica la pregunta. Divide en pasos más pequeños.

---

## 🔗 REFERENCIAS

- Archivos del proyecto: `docs/`, `scripts/`, código en `/computadora/`
- Tareas pendientes: `WorkItems.md`
- Para GitHub Copilot: `DEVELOPMENT_WORKFLOW_COPILOT.md` (versión completa)
- Comandos útiles: `docs/COMANDOS.md`

---

**LISTO PARA ACTUAR.** Pide cambios siguiendo este workflow y ahorra tokens.
